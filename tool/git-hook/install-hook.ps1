# 将 pre-commit 钩子安装到本仓库 .git/hooks/pre-commit
$ErrorActionPreference = "Stop"

$scriptDir = $PSScriptRoot
$repo = git -C $scriptDir rev-parse --show-toplevel
if ($LASTEXITCODE -ne 0) {
    throw "不是 Git 仓库: $scriptDir"
}

$hookSource = Join-Path $scriptDir "pre-commit"
$hooksDir = Join-Path $repo ".git\hooks"
$target = Join-Path $hooksDir "pre-commit"

if (-not (Test-Path $hooksDir)) {
    New-Item -ItemType Directory -Path $hooksDir -Force | Out-Null
}

if (Test-Path $target) {
    $backup = "$target.bak-$(Get-Date -Format 'yyyyMMddHHmmss')"
    Copy-Item -LiteralPath $target -Destination $backup
    Write-Host "已备份现有钩子到 $backup"
}

Copy-Item -LiteralPath $hookSource -Destination $target -Force
Write-Host "pre-commit 钩子已安装: $target"
Write-Host "下次 git commit 时自动执行；可用 python tool/git-hook/pre-commit.py 手动测试。"
