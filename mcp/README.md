# MCP

存放可分享的 MCP 服务器，一个服务器一个子目录；安装与使用见各子目录的 `README.md`。

<!-- lp:index:begin:mcp -->

| 名称 | 说明 |
|------|------|
| [lp-local-ai](lp-local-ai/) | 本地 AI 工具 MCP：OCR（中英）+ 本地大模型（翻译/摘要/改写）。 所有数据都在本机处理，不发送到任何云端服务。 |

<!-- lp:index:end:mcp -->

## 约定

- 一个服务器一个子目录，目录名 `lp-` 前缀 + kebab-case。
- 每个服务器目录包含 `README.md`（安装、注册、使用说明）与实现代码。
- 每个服务器目录包含 `mcp.config.json`（供 `scripts/register-mcp.ps1` 生成注册配置）。
- 新增或移除服务器后，同步更新本索引与根 README。
