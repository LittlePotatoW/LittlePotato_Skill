# Plugins

平台插件，按目标平台分子目录。目前只收 Codex，后续如需要可扩展 `claude-code/`、`cursor/`、`vscode/`。

<!-- lp:index:begin:plugins -->

| 平台 | 说明 | 状态 |
|------|------|------|
| [codex](codex/) | Codex 插件及扩展配置。 | 已有条目 |

<!-- lp:index:end:plugins -->

## 约定

- 一个插件一个子目录，目录名与插件 ID 一致并使用 kebab-case。
- 每个插件目录包含 `README.md`（安装方式、版本兼容说明）与插件文件。
- 新增或移除插件后，同步更新本索引与根 README。
