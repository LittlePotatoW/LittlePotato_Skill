# DeepSeek 创意顾问

一个 Codex 插件，按用户显式请求调用一次 DeepSeek，为当前问题提供创意方向。插件包含 `$deepseek-creative` 技能和 Node.js 调用脚本。

## 安装

在本仓库根目录添加仓库级插件市场：

```powershell
codex plugin marketplace add .
```

然后在 Codex 插件界面打开 `littlepotato-skill-local` 市场，安装并启用 **DeepSeek Creative Consultant**。启用后可从 `/` 菜单选择，或显式调用 `$deepseek-creative`。该技能不允许隐式调用。

## 配置

在运行 Codex 的环境中设置 `DEEPSEEK_API_KEY`，或在正在处理的项目根目录创建本地 `.env.local`：

```dotenv
DEEPSEEK_API_KEY=你的DeepSeek_API_Key
```

不要把密钥放入请求 JSON、命令行参数或插件文件。仓库 `.gitignore` 会忽略 `.env.local` 和 `.creative-consultant.json`。

默认参数如下；可在当前项目根目录的 `.creative-consultant.json` 中覆盖：

```json
{
  "temperature": 1.5,
  "model": "deepseek-flash",
  "max_tokens": 4096,
  "timeout_ms": 60000
}
```

单次调用参数可覆盖 `question`、`context`、`system_prompt`、`temperature`、`model`、`max_tokens`、`stop`、`response_format` 和 `timeout_ms`。温度范围为 0 到 2。参数优先级为：单次调用参数、项目级 `.creative-consultant.json`、用户级 Codex 默认值、内置默认值。API Key 优先从项目级 `.env.local` 读取，其次读取运行 Codex 的环境变量。

## 数据与权限

每次调用都会向 `https://api.deepseek.com/chat/completions` 发送一次请求。技能只选择回答问题所需的最少上下文，不会默认发送整段对话或整个工作区。调用脚本需要一次性沙箱外运行权限；每次调用都由用户批准，拒绝后不会发送请求。

## 依赖与状态

- 需要可用的 Node.js（内置 `fetch`）。
- 需要 DeepSeek API Key 和网络连接。
- 当前版本：`0.1.0`。

插件清单位于 `.codex-plugin/plugin.json`，其中的 `skills` 字段声明技能目录。用户级默认参数文件位于 `$CODEX_HOME/creative-consultant/config.json`；未设置 `CODEX_HOME` 时使用 `~/.codex/creative-consultant/config.json`。项目配置覆盖用户级默认参数，单次请求参数优先级最高。
