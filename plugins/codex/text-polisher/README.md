# 文本润色助手

一个显式调用的 Codex 插件，通过智谱 BigModel 的 GLM-4.7-Flash 润色用户提供的文本。插件只把本次指定的文本与润色要求发送给模型，不读取或上传工作区文件。

## 安装

在本仓库根目录注册本地插件市场：

```powershell
codex plugin marketplace add .
```

然后在 Codex 插件界面中从 **LittlePotato Skill** 市场安装 **文本润色助手**。技能调用名是 `$text-polisher`。

## 配置密钥

设置 `ZHIPU_API_KEY` 环境变量，或在当前项目根目录的 `.env.local` 中添加：

```dotenv
ZHIPU_API_KEY=你的智谱API密钥
```

本仓库的 `.gitignore` 已忽略 `.env.local`。不要把密钥放在命令行参数、提示词或请求正文中。

## 使用

明确调用 `$text-polisher`，并提供要润色的文本。可以在同一次请求中指定正式、简洁、自然、学术等风格。默认沿用原文语言，只输出润色后的文本。

配置好密钥后，可在 PowerShell 中手动验证脚本：

```powershell
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$request = @{ text = '这是一段需要润色的文字。'; style = '自然、简洁' } | ConvertTo-Json -Compress
$request | node .\plugins\codex\text-polisher\scripts\polish.mjs
```

脚本从标准输入接收请求，不创建临时请求文件，也不会记录正文。请求使用 BigModel 对话补全接口与 `glm-4.7-flash`。服务上下文上限按模型文档的 200K 处理，输入、指令和输出会共同占用上下文；默认 `max_tokens` 为 65536。不会自动截断或拆分文本；超限时请缩短或分段后重试。

## 状态

可用；需要 Node.js 18 或更高版本以及用户自己的智谱 API 密钥。每次调用都会将用户明确提交的文本发送到智谱 BigModel。
