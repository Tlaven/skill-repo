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
# 复核完成后，把当前 HEAD 记为下次起点（写 ASCII / 无 BOM，别用 `>`——PS 5.1 的 `>` 写成 UTF-16）：
#   Set-Content -Encoding ascii docs/reviews/.last-review "<sha> <yyyy-MM-dd>"
# BOM 会让 .sh 版读到的 SHA 带前缀，git diff 失效并静默显示“无变化”。
# 退出码恒为 0 —— 它不拦任何东西。

$ErrorActionPreference = "Continue"

# 契约面：L1（全部宿主文件名）+ L2（来自 scripts/l2-docs.txt）+ 术语表 + 模块文档
# L4（docs/core-analysis.*）不算契约文件——阅读视图，不触发复核（C-1）
$L2Docs = @((Get-Content (Join-Path $PSScriptRoot 'l2-docs.txt') -Raw -Encoding UTF8 -ErrorAction SilentlyContinue) -split "\r?\n" |
  Where-Object { $_ -and $_.Trim() -and $_.Trim() -notmatch '^#' } |
  ForEach-Object { $_.Trim() })
if ($L2Docs.Count -eq 0) { $L2Docs = @('docs/architecture.md','docs/architecture.markdown') }
$CONTRACT = @("AGENTS.md", "CLAUDE.md", ".cursorrules", ".cursor/rules/project.mdc", ".windsurfrules", ".github/copilot-instructions.md", "docs/glossary.md", "docs/glossary.markdown") + $L2Docs + @("docs/design-contract.md", "docs/modules/")
$MARKER = "docs/reviews/.last-review"

git rev-parse --is-inside-work-tree 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Host "[review-backlog] 不是 git 仓库，跳过。"; exit 0 }

$headRaw = git rev-parse --short HEAD 2>$null
$head = if ($headRaw) { "$headRaw".Trim() } else { "" }
$existing = @($CONTRACT | Where-Object { Test-Path $_ })
if ($existing.Count -eq 0) { Write-Host "[review-backlog] 未找到契约文件（$($CONTRACT -join ', ')）。"; exit 0 }

$since = $null
if (Test-Path $MARKER) {
  $first = Get-Content $MARKER -TotalCount 1 -ErrorAction SilentlyContinue
  if ($first) { $since = ($first -split '\s+')[0] }
}
if ($since) {
  git cat-file -e "$since^{commit}" 2>$null
  if ($LASTEXITCODE -ne 0) {
    Write-Host "[review-backlog] 起点 $since 不是有效 commit；按首次全量列。"
    $since = $null
  }
}

if (-not $since) {
  Write-Host "[review-backlog] 还没有复核起点（$MARKER 不存在）——首次按全量列。"
  Write-Host "契约文件:"
  $existing | ForEach-Object { Write-Host "  - $_" }
  Write-Host ""
  if ($head) {
    Write-Host "复核完成后写入起点:  New-Item -ItemType Directory -Force docs/reviews | Out-Null; Set-Content -Encoding ascii $MARKER `"$head $(Get-Date -Format yyyy-MM-dd)`""
  } else {
    Write-Host "（尚无提交——先提交一次,再把 HEAD 写入 $MARKER 作为起点）"
  }
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
# 行过滤与 .sh 的 awk 等价:先筛行(--/++ 元数据行排除,不吞行首字符),再匹配编号
$hits = @($diff | Where-Object { $_ -match '^[+-]' -and $_ -notmatch '^(\+\+\+|---)' -and $_ -match '\b(I-\d+|Q-\d+|E-\d+|D-\d+|R-\d+|A-\d+|M\d+-\d+|U-\d+|P-A\d+-\d+)\b' } | ForEach-Object { $_.Trim() })
if ($hits.Count -gt 0) {
  $hits | Select-Object -First 80 | ForEach-Object { Write-Host "  $_" }
  if ($hits.Count -gt 80) { Write-Host "  …（还有 $($hits.Count - 80) 行，直接看 git diff）" }
} else {
  Write-Host "  （未识别到编号变化——可能改的是叙述/白话，仍需人工扫一眼 diff）"
}

Write-Host ""
if ($head) {
  Write-Host "复核完成后写入新起点:  New-Item -ItemType Directory -Force docs/reviews | Out-Null; Set-Content -Encoding ascii $MARKER `"$head $(Get-Date -Format yyyy-MM-dd)`""
} else {
  Write-Host "（尚无提交——先提交一次,再把 HEAD 写入 $MARKER 作为起点）"
}
exit 0
