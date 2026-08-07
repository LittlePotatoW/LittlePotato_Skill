# Scripts

仓库维护脚本。

| 脚本 | 用途 |
|------|------|
| [index.py](./index.py) | 扫描各分类条目，自动生成/校验各级 README 索引 |
| [sync-skills.ps1](./sync-skills.ps1) | 把 `skills/` 同步到 Claude Code / Codex 的全局技能目录 |
| [register-mcp.ps1](./register-mcp.ps1) | 读取 `mcp/` 下服务器的 `mcp.config.json`，生成 MCP 注册配置 |

## index.py

自动发现 `skills/`（以 `SKILL.md` 为准）、`mcp/`、`tools/`、`plugins/`、`workflows/`、`prompts/`（以 `README.md` 为准）下的真实条目，重写各 README 中 `<!-- lp:index:begin:<key> --> ... <!-- lp:index:end:<key> -->` 之间的索引块。

```bash
python scripts/index.py            # 生成并写回
python scripts/index.py --check    # 校验：有漂移时退出码 1（适合 pre-commit / CI）
python scripts/index.py --dry-run  # 只预览将更新的文件
```

## sync-skills.ps1

复制（或符号链接）`skills/` 下所有技能到全局技能目录，默认目标为 `~/.claude/skills` 和 `~/.codex/skills`。复制模式会覆盖同名旧目录，建议先 `-DryRun` 预览。

```powershell
.\scripts\sync-skills.ps1 -DryRun          # 预览
.\scripts\sync-skills.ps1                  # 复制到默认目标
.\scripts\sync-skills.ps1 -Mode Symlink    # 符号链接（Windows 需管理员/开发者模式）
.\scripts\sync-skills.ps1 -Targets @("$HOME\.claude\skills")
```

> 若系统执行策略禁止直接运行 .ps1，可改用：`powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\sync-skills.ps1 -DryRun`

## register-mcp.ps1

每个 MCP 服务器目录需提供 `mcp.config.json`，其中 `{repo}` 会自动替换为当前仓库的绝对路径：

```json
{
  "name": "lp-local-ai",
  "command": "uv",
  "args": ["run", "--project", "{repo}/mcp/lp-local-ai", "lp-local-ai"],
  "env": {}
}
```

```powershell
.\scripts\register-mcp.ps1              # 打印 Codex / Claude 的注册命令与配置片段
.\scripts\register-mcp.ps1 -Client Codex
.\scripts\register-mcp.ps1 -Apply       # 直接执行 codex/claude mcp add（谨慎，会写入客户端配置）
```

> 脚本文件以 UTF-8 带 BOM 保存，兼容 Windows PowerShell 5.1 的中文解析。

## 约定

- 脚本命名 kebab-case，每个脚本自带使用说明。
- 新增条目后运行 `python scripts/index.py` 保持各级索引同步。
