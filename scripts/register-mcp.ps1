<#
.SYNOPSIS
读取 mcp/ 下各服务器的 mcp.config.json，生成 Claude Code / Codex 的 MCP 注册配置。

.DESCRIPTION
每个服务器目录需包含 mcp.config.json，示例：
{
  "name": "lp-local-ai",
  "command": "uv",
  "args": ["run", "--project", "{repo}/mcp/lp-local-ai", "lp-local-ai"],
  "env": {}
}
其中 {repo} 会替换为当前仓库的绝对路径（正斜杠形式）。
默认只打印各客户端的注册命令与配置片段，不写任何文件。

.PARAMETER Client
All（默认）、Codex 或 Claude。

.PARAMETER Apply
直接执行 codex mcp add / claude mcp add 命令（会写入客户端配置，请先预览确认）。

.PARAMETER Quiet
只输出命令与配置片段，不打印服务器说明。

.EXAMPLE
./scripts/register-mcp.ps1
./scripts/register-mcp.ps1 -Client Codex
./scripts/register-mcp.ps1 -Apply
#>
[CmdletBinding()]
param(
    [ValidateSet("All", "Codex", "Claude")]
    [string]$Client = "All",
    [switch]$Apply,
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$mcpRoot = Join-Path $repoRoot "mcp"
if (-not (Test-Path -LiteralPath $mcpRoot)) {
    throw "MCP 目录不存在: $mcpRoot"
}

$configs = Get-ChildItem -LiteralPath $mcpRoot -Recurse -Filter "mcp.config.json" -File
if ($configs.Count -eq 0) {
    Write-Host "未找到任何 mcp.config.json。在每个 MCP 服务器目录中放置该文件后重试。"
    exit 0
}

$repoFwd = $repoRoot.Replace("\", "/")

function Get-McpConfig {
    param([string]$Path)
    try {
        $cfg = Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
    }
    catch {
        Write-Warning "解析失败，跳过: $Path"
        return $null
    }
    if (-not $cfg.name -or -not $cfg.command -or -not $cfg.args) {
        Write-Warning "缺少 name/command/args 字段，跳过: $Path"
        return $null
    }
    $expandedArgs = @($cfg.args | ForEach-Object { $_ -replace "{repo}", $repoFwd })
    return [pscustomobject]@{
        Name    = $cfg.name
        Command = $cfg.command -replace "{repo}", $repoFwd
        Args    = $expandedArgs
        Env     = $cfg.env
        Path    = $Path
    }
}

function Format-Command {
    param([string]$ClientName, [object]$Cfg)
    $parts = @($Cfg.Command) + @($Cfg.Args | ForEach-Object {
        if ($_ -match "\s") { "'$_'" } else { $_ }
    })
    return "$ClientName mcp add $($Cfg.Name) -- $($parts -join ' ')"
}

function Format-Json {
    param([object]$Cfg)
    $payload = @{
        mcpServers = @{
            $Cfg.Name = @{
                command = $Cfg.Command
                args    = @($Cfg.Args)
                env     = $Cfg.Env
            }
        }
    }
    return $payload | ConvertTo-Json -Depth 6
}

function Format-Toml {
    param([object]$Cfg)
    $argsStr = ($Cfg.Args | ForEach-Object { "`"$_`"" }) -join ", "
    $envLines = ""
    if ($null -ne $Cfg.Env -and (@($Cfg.Env.PSObject.Properties).Count -gt 0)) {
        $pairs = $Cfg.Env.PSObject.Properties | ForEach-Object {
            "`"$($_.Name)`" = `"$($_.Value)`""
        }
        $envLines = "env = { $($pairs -join ', ') }`n"
    }
    return "[mcp_servers.$($Cfg.Name)]`ncommand = `"$($Cfg.Command)`"`nargs = [$argsStr]`n$envLines"
}

function Invoke-ClientAdd {
    param([string]$ClientName, [object]$Cfg)
    Write-Host "  执行 $ClientName mcp add ..."
    & $ClientName mcp add $Cfg.Name "--" @($Cfg.Command) @($Cfg.Args)
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "$ClientName mcp add 退出码 $LASTEXITCODE"
        return $false
    }
    return $true
}

$applied = 0
foreach ($cfgFile in $configs) {
    $cfg = Get-McpConfig -Path $cfgFile.FullName
    if (-not $cfg) {
        continue
    }
    if (-not $Quiet) {
        Write-Host "## $($cfg.Name)"
        Write-Host "   配置文件: $($cfgFile.FullName)"
    }

    if ($Client -in @("All", "Codex")) {
        Write-Host ""
        Write-Host "[Codex] 注册命令:"
        Write-Host "  $(Format-Command -ClientName codex -Cfg $cfg)"
        if ($Apply) {
            if (Invoke-ClientAdd -ClientName codex -Cfg $cfg) { $applied++ }
        }
        Write-Host ""
        Write-Host "[Codex] ~/.codex/config.toml 参考片段（不用 CLI 时）:"
        Write-Host (Format-Toml $cfg)
    }

    if ($Client -in @("All", "Claude")) {
        Write-Host ""
        Write-Host "[Claude] 注册命令:"
        Write-Host "  $(Format-Command -ClientName claude -Cfg $cfg)"
        if ($Apply) {
            if (Invoke-ClientAdd -ClientName claude -Cfg $cfg) { $applied++ }
        }
        Write-Host ""
        Write-Host "[Claude] .mcp.json 参考片段:"
        Write-Host (Format-Json $cfg)
    }

    $hasEnv = $null -ne $cfg.Env -and (@($cfg.Env.PSObject.Properties).Count -gt 0)
    if ($hasEnv) {
        Write-Host ""
        Write-Warning "该服务器带环境变量（env），CLI 注册命令未包含；请在客户端配置或片段中补充。"
    }
    Write-Host ""
}

if ($Apply) {
    Write-Host "已完成 $applied 个注册操作。"
}
