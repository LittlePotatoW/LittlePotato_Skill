# Git pre-commit 钩子

提交前自动检查暂存区，命中以下任一规则就**阻止提交**：

| 规则 | 默认值 | 说明 |
|------|--------|------|
| 图片数量 | 最多 1 张 | 一次提交中图片超过 `max_images` 张即阻止 |
| 文件大小 | 1 MB | 任一文件超过 `max_file_size_mb` 即阻止 |
| 后缀排除表 | 见配置 | `blocked_extensions` / `blocked_filenames` 命中的文件直接阻止 |
| 二进制内容 | 开启 | 检测到 NUL 字节即视为二进制（图片除外，图片走数量规则） |
| Jupyter 输出 | 开启 | `.ipynb` 存在未清空的 `outputs` 或 `execution_count` 即阻止 |

## 安装

在 PowerShell 中执行：

```powershell
.\tool\git-hook\install-hook.ps1
```

脚本会把 `pre-commit`（bash 入口）复制到 `.git/hooks/pre-commit`，
已有钩子会先备份为 `pre-commit.bak-<时间戳>`。

## 手动测试

暂存文件后直接运行：

```powershell
python tool/git-hook/pre-commit.py
```

退出码 0 = 通过，1 = 有文件需要处理。

## 配置

所有规则都在 [pre-commit-config.json](./pre-commit-config.json) 中调整，
钩子每次运行都会重新读取，改完即生效：

- `max_images`：一次提交允许的最大图片数
- `max_file_size_mb`：单文件大小上限（MB）
- `image_extensions`：按扩展名识别图片
- `blocked_extensions` / `blocked_filenames`：后缀 / 文件名排除表
- `check_binary`：是否检查二进制内容
- `check_notebook_outputs`：是否检查 Jupyter 未清空输出

## 绕过（不推荐）

- 单次跳过：`git commit --no-verify`
- 环境变量跳过：`$env:LP_GIT_HOOK_SKIP=1` 后再提交
