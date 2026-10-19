# Skills

技能按用途分为两类：`learning`（学习辅助）、`competition-docs`（比赛文档）。

<!-- lp:index:begin:skills -->

| 技能 | 分类 | 说明 |
|------|------|------|
| [lp-build-orchestrator](coding/lp-build-orchestrator/) | coding | Coordinate non-trivial software construction by delegating independent research, implementation, review, or testing tasks to as many subagents as useful, or th… |
| [lp-md2docx](competition-docs/lp-md2docx/) | competition-docs | 将 Markdown 文档 + 图片文件夹转换为带样式表和多级标题的 Word 文档（.docx）， 面向大学生比赛文档（商业计划书、计算机设计大赛项目文档等论文格式文档）。 触发条件：把 md 转成 word、md 转 docx、生成比赛文档、商业计划书排版、 按样式表转换 Markdown、生成带多级编号标题的… |
| [lp-tidy-any-text](learning/lp-tidy-any-text/) | learning | 将任意学科的杂乱复习资料（PDF、DOCX、DOC、XMIND、图片等）整理成结构化复习文件。 触发条件：整理课程资料、复习资料、期末复习、按章节归纳知识点、去重整理题目、 分类归档学习资料、将杂乱的源文件整理成可打印的复习文档等。 |

<!-- lp:index:end:skills -->

## 约定

- 一个技能一个子目录，目录名 `lp-` 前缀 + kebab-case（如 `lp-md2docx`）。
- 每个技能目录内必须有 `SKILL.md`，可选 `README.md`、`references/`、`scripts/`、`assets/`、`examples/`。
- 新增或移除技能后，同步更新本索引与根 README。
