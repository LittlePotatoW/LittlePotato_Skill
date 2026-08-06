# LittlePotato Skill

LittlePotato 的个人 AI 工具库：Claude Code / Codex 技能 + 可分享的 MCP 服务器。

## 技能目录

### Learning

| 技能 | 说明 |
|------|------|
| [lp-tidy-any-text](./skills/learning/lp-tidy-any-text/) | 将任意学科的杂乱复习资料整理成结构化复习文件 |

### Competition Docs

| 技能 | 说明 |
|------|------|
| [lp-md2docx](./skills/competition-docs/lp-md2docx/) | 将 Markdown + 图片文件夹转换为带样式表和多级标题的 Word 文档（比赛文档专用） |
| [lp-competition-proposal](./skills/competition-docs/lp-competition-proposal/) | 根据代码与材料分阶段生成比赛项目计划书（文字稿→图片映射表→调研补全→最终 .md） |

## MCP 目录

| MCP | 说明 |
|------|------|
| [lp-local-ai](./mcp/lp-local-ai/) | 本地 OCR（中英）+ 本地大模型（翻译/摘要/改写），数据不出本机 |

安装与注册方法见 [mcp/README.md](./mcp/README.md)。

## 工具

| 工具 | 说明 |
|------|------|
| [git 提交钩子](./tool/git-hook/) | pre-commit 检查：图片数量、文件大小、后缀排除表、二进制文件、Jupyter 未清空输出 |

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
