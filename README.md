# LittlePotato Skill

LittlePotato 的个人 AI 工具库：技能（Skills）、MCP 服务器、自定义工具、插件、工作流与提示词模板。

## 仓库结构

| 分类 | 路径 | 说明 |
|------|------|------|
| 技能 | [skills/](./skills/) | Claude Code / Codex 技能（SKILL.md 规范） |
| MCP | [mcp/](./mcp/) | 可分享的 MCP 服务器 |
| 工具 | [tools/](./tools/) | 自定义工具：git 钩子、CLI 脚本等 |
| 插件 | [plugins/](./plugins/) | 平台插件（目前只收 Codex） |
| 工作流 | [workflows/](./workflows/) | 可复用工作流 |
| 提示词 | [prompts/](./prompts/) | 提示词模板 |
| 维护脚本 | [scripts/](./scripts/) | 仓库维护脚本（索引、同步、注册） |
| 文档 | [docs/](./docs/) | 仓库教程与使用指南 |
| 归档 | [archive/](./archive/) | 弃用但保留的内容 |

> 技能、MCP、工具、插件、工作流、提示词的索引由 `scripts/index.py` 自动维护，手动编辑会在一键生成时被覆盖。

## 技能目录

<!-- lp:index:begin:skills -->

### Coding

| 名称 | 说明 |
|------|------|
| [lp-build-orchestrator](skills/coding/lp-build-orchestrator/) | Coordinate non-trivial software construction by delegating independent research, implementation, review, or testing tasks to as many subagents as useful, or th… |

### Competition Docs

| 名称 | 说明 |
|------|------|
| [lp-md2docx](skills/competition-docs/lp-md2docx/) | 将 Markdown 文档 + 图片文件夹转换为带样式表和多级标题的 Word 文档（.docx）， 面向大学生比赛文档（商业计划书、计算机设计大赛项目文档等论文格式文档）。 触发条件：把 md 转成 word、md 转 docx、生成比赛文档、商业计划书排版、 按样式表转换 Markdown、生成带多级编号标题的… |

### Learning

| 名称 | 说明 |
|------|------|
| [lp-tidy-any-text](skills/learning/lp-tidy-any-text/) | 将任意学科的杂乱复习资料（PDF、DOCX、DOC、XMIND、图片等）整理成结构化复习文件。 触发条件：整理课程资料、复习资料、期末复习、按章节归纳知识点、去重整理题目、 分类归档学习资料、将杂乱的源文件整理成可打印的复习文档等。 |

<!-- lp:index:end:skills -->

## MCP 目录

<!-- lp:index:begin:mcp -->

| 名称 | 说明 |
|------|------|
| [lp-local-ai](mcp/lp-local-ai/) | 本地 AI 工具 MCP：OCR（中英）+ 本地大模型（翻译/摘要/改写）。 所有数据都在本机处理，不发送到任何云端服务。 |

<!-- lp:index:end:mcp -->

安装与注册方法见 [mcp/README.md](./mcp/README.md)。

## 工具

<!-- lp:index:begin:tools -->

| 名称 | 说明 |
|------|------|
| [git-hook](tools/git-hook/) | 提交前自动检查暂存区，命中以下任一规则就阻止提交： |

<!-- lp:index:end:tools -->

## 安装

将技能文件夹复制到以下路径：

**个人全局**（所有项目可用）：
```
~/.claude/skills/<skill-name>/
```

**单项目**（仅当前项目可用）：
```
<项目>/.claude/skills/<skill-name>/
```

## 仓库规范

给 AI 协作者与贡献者的约定见 [AGENTS.md](./AGENTS.md)；仓库文档见 [docs/](./docs/)。
