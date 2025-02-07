# AI 对话插件

## 简介

本插件为 [zhenxun_bot](https://github.com/HibiKier/zhenxun_bot) 提供了 AI 对话功能。用户可以通过在群聊中 @机器人 并发送消息，与 AI 进行互动。

## 功能

- **AI 对话**：用户在群聊中 @机器人 并发送消息，机器人将使用指定的 AI 模型生成回复。
- **清空对话历史**：用户发送 "@机器人 清空对话" 指令，可以清除与机器人的对话历史记录。

## 安装

1. **克隆插件仓库**：将插件代码克隆到本地。

   ```bash
   git clone https://github.com/shouzia/zhenxun_ai_plugin.git
   ```

2. **复制插件到插件目录**：将克隆的插件文件夹复制到 `zhenxun_bot` 的 `plugins` 目录下。

3. **安装依赖**：在 `zhenxun_bot` 项目根目录下，使用 Poetry 安装插件所需的依赖。

   ```bash
   poetry add openai nonebot_plugin_session
   ```

4. **配置 API 密钥**：在 `data/config.yaml` 文件中，添加以下配置项，并填写您的 API 密钥和模型名称。

   API 密钥可在 [OpenRouter](https://openrouter.ai) 获取。
   
   ```yaml
   ai_API_KEY:
     API_KEY: "your_api_key_here"
   BACKUP_API_KEYS:
     backup_api_keys: ["backup_api_key1", "backup_api_key2"]
   ai_MODEL:
     MODEL_NAME: "google/gemini-2.0-flash-lite-preview-02-05:free"
   ```

   - `API_KEY`：主 API 密钥。
   - `backup_api_keys`：备用 API 密钥列表。
   - `MODEL_NAME`：使用的 AI 模型名称。

## 使用方法

- **AI 对话**：在群聊中 @机器人，并发送您的消息，机器人将根据您的输入生成回复。
- **清空对话历史**：在群聊中发送 "@机器人 清空对话"，机器人将清除与您的对话历史记录。

## 注意事项

- 确保在 `data/config.yaml` 中正确配置了 API 密钥和模型名称。
- 插件会为每个用户保存独立的对话历史，存储在插件目录下的 `dialogue_histories` 文件夹中。
- 如果需要清除对话历史，可以使用相应的指令，或手动删除对应的 JSON 文件。

