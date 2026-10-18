#!/usr/bin/env pwsh
# review-backlog.ps1 — 列出"自上次复核以来"契约文档的变化（零 token，只列清单，不判定）
#
# 用途：teach-back 是**按需 + 攒批**做的。攒批的代价不是"跑 agent"，是"复核时要重读多少"。
# 本脚本把"重读全量"变成"只看 delta"：
#   - 哪些契约文件变了（git diff --stat）
#   - 哪些不变量 / 单元编号被增删改（正则扫 +/- 行）
#
# 用法：
#   pwsh scripts/review-backlog.ps1
# 复核完成后，把当前 HEAD 记为下次起点：
#   "<sha> <yyyy-MM-dd>" > docs/reviews/.last-review
#
# 退出码恒为 0 —— 它不拦任何东西。

$ErrorActionPreference = "Continue"

# 按项目改：哪些文件算"契约"（L1 全部宿主文件名，与 check-docs-sync 对齐；+ L2/L4 + 术语表 + 模块文档）
$CONTRACT = @("AGENTS.md", "CLAUDE.md", ".cursorrules", ".cursor/rules/project.mdc", ".windsurfrules", ".github/copilot-instructions.md", "docs/architecture.md", "docs/architecture.markdown", "docs/core-code.md", "docs/core-code.markdown", "docs/glossary.md", "docs/glossary.markdown", "docs/modules/")
$MARKER = "docs/reviews/.last-review"

git rev-parse --is-inside-work-tree 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Host "[review-backlog] 不是 git 仓库，跳过。"; exit 0 }

$head = (git rev-parse --short HEAD 2>$null).Trim()
$existing = @($CONTRACT | Where-Object { Test-Path $_ })
if ($existing.Count -eq 0) { Write-Host "[review-backlog] 未找到契约文件（$($CONTRACT -join ', ')）。"; exit 0 }

$since = $null
if (Test-Path $MARKER) {
  $first = Get-Content $MARKER -TotalCount 1 -ErrorAction SilentlyContinue
  if ($first) { $since = ($first -split '\s+')[0] }
}

if (-not $since) {
  Write-Host "[review-backlog] 还没有复核起点（$MARKER 不存在）——首次按全量列。"
  Write-Host "契约文件:"
  $existing | ForEach-Object { Write-Host "  - $_" }
  Write-Host ""
  Write-Host "复核完成后写入起点:  `"$head $(Get-Date -Format yyyy-MM-dd)`" > $MARKER"
  exit 0
}

Write-Host "[review-backlog] 自 $since 以来的契约变化（当前 HEAD=$head）："
$stat = git diff --stat "$since..HEAD" -- $existing 2>$null
if (-not $stat) { Write-Host "  （无变化）"; exit 0 }
$stat | ForEach-Object { Write-Host "  $_" }

Write-Host ""
Write-Host "被增删改的编号（复核时只看这些 + 它们引用的上下文）："
$diff = git diff -U0 "$since..HEAD" -- $existing 2>$null
# 编号族是启发式(示例来自试点项目约定):按项目增删
$hits = @($diff | Select-String -Pattern '^[+-](?![+-]).*\b(I-\d+|Q-\d+|A-\d+|M\d+-\d+|U-\d+|P-A\d+-\d+)\b' | ForEach-Object { $_.Line.Trim() })
if ($hits.Count -gt 0) {
  $hits | Select-Object -First 80 | ForEach-Object { Write-Host "  $_" }
  if ($hits.Count -gt 80) { Write-Host "  …（还有 $($hits.Count - 80) 行，直接看 git diff）" }
} else {
  Write-Host "  （未识别到编号变化——可能改的是叙述/白话，仍需人工扫一眼 diff）"
}

Write-Host ""
Write-Host "复核完成后写入新起点:  `"$head $(Get-Date -Format yyyy-MM-dd)`" > $MARKER"
exit 0
