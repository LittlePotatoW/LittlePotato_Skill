<#
.SYNOPSIS
将 skills/ 下的技能同步到 AI 客户端的全局技能目录。

.DESCRIPTION
自动发现 skills/ 下所有包含 SKILL.md 的技能目录，复制（默认）或符号链接到目标目录。
默认目标：~/.claude/skills、~/.codex/skills，可用 -Targets 覆盖。
复制模式会覆盖同名旧目录，建议先 -DryRun 预览。

.PARAMETER Mode
Copy（复制，默认）或 Symlink（符号链接；Windows 需管理员权限或开发者模式）。

.PARAMETER Targets
目标目录列表；为空时使用默认目标。

.PARAMETER Source
技能仓库目录，默认取本仓库的 skills/。

.PARAMETER DryRun
只打印将要执行的操作，不写入。

.EXAMPLE
./scripts/sync-skills.ps1 -DryRun
./scripts/sync-skills.ps1
./scripts/sync-skills.ps1 -Mode Symlink
#>
[CmdletBinding()]
param(
    [ValidateSet("Copy", "Symlink")]
    [string]$Mode = "Copy",
    [string[]]$Targets = @(),
    [string]$Source = "",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
if (-not $Source) {
    $Source = Join-Path $repoRoot "skills"
}
if (-not (Test-Path -LiteralPath $Source)) {
    throw "技能目录不存在: $Source"
}

if ($Targets.Count -eq 0) {
    $Targets = @(
        (Join-Path $HOME ".claude\skills"),
        (Join-Path $HOME ".codex\skills")
    )
}

$skillDirs = Get-ChildItem -LiteralPath $Source -Recurse -Filter "SKILL.md" -File |
    ForEach-Object { $_.Directory } |
    Sort-Object FullName -Unique

if ($skillDirs.Count -eq 0) {
    Write-Host "在 $Source 下未发现任何技能（SKILL.md）。"
    exit 0
}

Write-Host "模式: $Mode"
Write-Host "技能数: $($skillDirs.Count)  目标数: $($Targets.Count)"
Write-Host ""

$ok = 0
$failed = 0
foreach ($skill in $skillDirs) {
    foreach ($target in $Targets) {
        $dest = Join-Path $target $skill.Name
        if ($DryRun) {
            Write-Host "[dry-run] $($skill.Name) -> $dest"
            continue
        }
        try {
            if ($Mode -eq "Copy") {
                New-Item -ItemType Directory -Path $target -Force | Out-Null
                if (Test-Path -LiteralPath $dest) {
                    Remove-Item -LiteralPath $dest -Recurse -Force
                }
                Copy-Item -LiteralPath $skill.FullName -Destination $dest -Recurse -Force
            }
            else {
                if (Test-Path -LiteralPath $dest) {
                    Write-Warning "目标已存在，跳过符号链接: $dest"
                    continue
                }
                New-Item -ItemType SymbolicLink -Path $dest -Target $skill.FullName | Out-Null
            }
            $ok++
        }
        catch {
            $failed++
            Write-Warning "同步失败: $($skill.Name) -> $dest : $_"
        }
    }
}

Write-Host ""
Write-Host "完成：成功 $ok，失败 $failed。"
