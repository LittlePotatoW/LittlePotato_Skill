# Tools

仓库自定义工具：git 钩子、CLI 脚本等。

<!-- lp:index:begin:tools -->

| 名称 | 说明 |
|------|------|
| [git-hook](git-hook/) | 提交前自动检查暂存区，命中以下任一规则就阻止提交： |

<!-- lp:index:end:tools -->

## 约定

- 一个工具一个子目录，目录名 `lp-` 前缀 + kebab-case（历史条目 `git-hook` 保留原名）。
- 每个工具目录包含 `README.md`（功能、安装、使用说明）与实现文件。
- 新增或移除工具后，同步更新本索引与根 README。
