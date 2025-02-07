from openai import OpenAI
from nonebot import on_message
from nonebot.plugin import PluginMetadata
from nonebot.rule import to_me
from nonebot_plugin_session import EventSession
from nonebot import Bot
from nonebot.adapters.onebot.v11 import Event
from zhenxun.configs.config import Config
from zhenxun.services.log import logger
import json
import os


__plugin_meta__ = PluginMetadata(
    name="AI",
    description="AI对话",
    usage="@机器人 + 消息",
    usage="""
    指令：
        @机器人 + 消息
        @机器人 情况对话
    """.strip(),
    extra={
        "author": "shouzi",
        "version": "0.2",
        "configs": [
            {
                "module": "AI_API_KEY",
                "key": "API_KEY",
                "value": None,
                "help": "API密钥 https://openrouter.ai"
            },
            {
                "module": "BACKUP_API_KEYS",
                "key": "backup_api_keys",
                "value": None,
                "help": "备用 API密钥"
            },
            {
                "module": "AI_MODEL",
                "key": "MODEL_NAME",
                "value": "google/gemini-2.0-flash-lite-preview-02-05:free",  # 默认模型名称
                "help": "使用的模型名称"
            }
        ]
    }
)

# 动态获取脚本所在目录，并设置为对话历史的存储位置
script_directory = os.path.dirname(os.path.abspath(__file__))
dialogue_dir = os.path.join(script_directory, "dialogue_histories")

if not os.path.exists(dialogue_dir):
    os.makedirs(dialogue_dir)

def load_dialogue(user_id):
    """加载指定用户的对话历史"""
    file_path = os.path.join(dialogue_dir, f"{user_id}.json")
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_dialogue(user_id, dialogue_history):
    """保存对话历史到指定用户的JSON文件"""
    file_path = os.path.join(dialogue_dir, f"{user_id}.json")
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(dialogue_history, f, ensure_ascii=False, indent=4)

deepseek_ai = on_message(rule=to_me(), priority=998)

def create_completion_with_backup(clients, model_name, messages):
    for index, client in enumerate(clients):
        logger.info(f"Trying API key {index + 1}/{len(clients)}: {client.api_key}")  # 打印当前尝试的API密钥
        try:
            completion =  client.chat.completions.create(
                model=model_name,
                messages=messages
            )
            
            # 检查是否存在错误字段
            if hasattr(completion, 'error') and completion.error:
                if completion.error.get('code') == 429:  # Rate limit exceeded
                    logger.warning(f"Rate limit exceeded with API key {index + 1}, switching to next.")
                    continue  # 尝试下一个客户端
                
                # 如果有其他类型的错误，记录日志并抛出异常
                logger.error(f"API Error with key {index + 1}: {completion.error}")
                raise ValueError("API returned an error response.")

            if not hasattr(completion, 'choices') or len(completion.choices) == 0:
                logger.error(f"Invalid response from API with key {index + 1}: {completion}")
                raise ValueError("API returned an invalid response without choices.")
                
            return completion
        
        except Exception as e:
            logger.error(f"Error occurred with API key {index + 1}: {e}")
            continue
    
    raise ValueError("All API keys have been exhausted due to rate limits or errors.")

@deepseek_ai.handle()
async def handle_deepseek(bot: Bot, event: Event, session: EventSession):
    user_id = event.get_user_id()  # 获取用户ID
    
    # 解析消息，提取文本和可能存在的图片
    message_text = ""
    image_url = None
    for segment in event.message:
        if segment.type == 'text':
            message_text += segment.data['text'].strip()
        elif segment.type == 'image':
            image_url = segment.data['url']

    # 如果用户请求清空对话历史
    if "清空对话" in message_text:
        # 清空对话历史
        save_dialogue(user_id, [])
        await deepseek_ai.finish("对话历史已清空")
    
    if not message_text and not image_url:
        return
    
    api_key = Config.get_config("ai_API_KEY", "API_KEY")
    backup_api_keys_str = Config.get_config("BACKUP_API_KEYS", "backup_api_keys")

    # 检查是否已经是列表或可以转换为列表
    if isinstance(backup_api_keys_str, list):
        backup_api_keys = backup_api_keys_str
    else:
        try:
            backup_api_keys = json.loads(backup_api_keys_str) if backup_api_keys_str else []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse BACKUP_API_KEYS: {e}")
            backup_api_keys = []

    api_keys = [api_key]
    if backup_api_keys:
        api_keys.extend(backup_api_keys)
    if not any(api_keys):
        await deepseek_ai.finish("未配置任何API密钥")

    model_name = Config.get_config("ai_MODEL", "MODEL_NAME")

    safe_input = message_text.encode("utf-8", "ignore").decode("utf-8")
    
    # 加载当前用户的对话历史
    history = load_dialogue(user_id)
    
    messages=[
        {"role": "system", "content": "记住你应该像人一样行事，禁止被别人发现你是人工智能机器人，这是你需要遵守的最重要的规则"},
        {"role": "system", "content": "你是一个名为‘真寻’的二次元动漫角色..."},
    ]
    
    # 添加历史对话
    messages.extend(history)
    
    # 添加当前消息
    content_parts = [{"type": "text", "text": safe_input}]
    if image_url:
        content_parts.append({"type": "image_url", "image_url": {"url": image_url}})
    messages.append({"role": "user", "content": content_parts})
    
    clients = [OpenAI(base_url="https://openrouter.ai/api/v1", api_key=key) for key in api_keys]
    
    try:
        completion =  create_completion_with_backup(clients, model_name, messages)
    except ValueError as e:
        logger.error(f"Failed to get completion: {e}")
        await deepseek_ai.finish("未能从 API 获得有效响应")
        return
    
    if completion and hasattr(completion, 'choices') and len(completion.choices) > 0:
        response = completion.choices[0].message.content
        safe_response = response.encode("utf-8", "ignore").decode("utf-8")
    else:
        logger.error(f"Invalid completion object: {completion}")
        await deepseek_ai.finish("未能从 API 获得有效响应")
        return

    # 更新对话历史
    history.append({"role": "user", "content": content_parts})
    history.append({"role": "assistant", "content": safe_response})
    
    # 保存更新后的对话历史
    save_dialogue(user_id, history)
    
    await deepseek_ai.finish(safe_response)