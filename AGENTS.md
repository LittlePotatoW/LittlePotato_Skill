# AGENTS.md

本文件给 AI 协作者（Claude Code、Codex 等）说明仓库约定。开始改动前请先阅读根 README 与本文档。

## 仓库是什么

LittlePotato 的个人 AI 工具库，按类型分目录存放：技能（`skills/`）、MCP（`mcp/`）、自定义工具（`tools/`）、插件（`plugins/`）、工作流（`workflows/`）、提示词（`prompts/`）、维护脚本（`scripts/`）。

## 通用规则

1. **不自造内容**：索引中只列出真实存在的条目；空分类保持"当前为空"的说明，不要编造示例条目。
2. **条目自包含**：每个条目一个子目录，含自己的 README（是什么、怎么装、怎么用、状态）。
3. **命名**：kebab-case；自建条目用 `lp-` 前缀（历史条目如 `git-hook` 保留原名）。
4. **同步索引**：新增/移动/删除条目后，运行 `python scripts/index.py` 重新生成索引（或至少同步更新对应分类 README 与根 README 的索引表）。
5. **编码**：所有文件 UTF-8，文本文件末尾保留换行。
6. **不动无关改动**：不修改与本任务无关的未提交内容。

## 各分类速览

- `skills/`：一个技能一个目录，必须有 `SKILL.md`；按用途子分类（`learning`、`competition-docs`）。
- `mcp/`：一个服务器一个目录，README 含安装与注册方法。
- `tools/`：git 钩子、CLI 工具等。
- `plugins/codex/`：Codex 插件。
- `workflows/`：多步流程编排。
- `prompts/`：提示词模板。
- `scripts/`：索引生成、技能同步、MCP 注册脚本。
- `docs/`、`archive/`：仓库文档、弃用内容。
