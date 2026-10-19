<#
skills-eval.ps1 — 运行各 skill 的验收入口（约定见下）。
用法:
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts/skills-eval.ps1 -Name drawio-export
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts/skills-eval.ps1 -Changed   # 依 git 变更挑 skill
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts/skills-eval.ps1 -All
  -Strict  有失败即退出 1（默认只提示、退出 0）

约定:
  1) 验收入口: <skill>/eval/run.ps1 或 <skill>/eval/run.py（可选；无入口 = 未接入，不阻断）
  2) 验收档: SKILL.md 的 `## 验收…` 段内写 `档位: smoke|golden|acceptance|teach-back`
  3) 接线（可选）: 在 .git/hooks/pre-commit 末尾加一行本脚本 -Changed（默认只提示，不阻断）
#>
param(
  [string]$Name,
  [switch]$Changed,
  [switch]$All,
  [switch]$Strict
)
$ErrorActionPreference = 'Continue'
$repo = Split-Path $PSScriptRoot -Parent

function Get-Tier([string]$skillDir) {
  $mdPath = Join-Path $skillDir 'SKILL.md'
  if (-not (Test-Path $mdPath)) { return '' }
  $md = Get-Content $mdPath -Raw -Encoding UTF8
  $sec = [regex]::Match($md, '(?ms)^##\s*验收[^\r\n]*\r?\n(.*?)(?=^##\s|\z)')
  if (-not $sec.Success) { return '' }
  $t = [regex]::Match($sec.Groups[1].Value, '档位\s*[:：]\s*[*`]*\s*(smoke|golden|acceptance|teach-back)')
  if ($t.Success) { return $t.Groups[1].Value }
  return '?'
}

$skills = Get-ChildItem $repo -Directory | Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') } | Sort-Object Name

if ($Name) {
  $skills = @($skills | Where-Object { $_.Name -eq $Name })
  if ($skills.Count -eq 0) { Write-Output "未找到 skill: $Name"; exit 2 }
} elseif ($Changed) {
  $paths = @()
  $paths += @(& git -C $repo diff --name-only HEAD 2>$null)
  $paths += @(& git -C $repo ls-files --others --exclude-standard 2>$null)
  $tops = @($paths | Where-Object { $_ } | ForEach-Object { ($_ -split '/')[0] } | Sort-Object -Unique)
  $skills = @($skills | Where-Object { $tops -contains $_.Name })
  if ($skills.Count -eq 0) { Write-Output '本次变更未涉及任何 skill。'; exit 0 }
}

$rows = @()
$anyFail = $false
foreach ($s in $skills) {
  $tier = Get-Tier $s.FullName
  if (-not $tier) { $tier = '-' }
  $runPs1 = Join-Path $s.FullName 'eval/run.ps1'
  $runPy  = Join-Path $s.FullName 'eval/run.py'
  if (Test-Path $runPs1) {
    $out = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $runPs1 2>&1
    $code = $LASTEXITCODE
  } elseif (Test-Path $runPy) {
    $out = & python $runPy 2>&1
    $code = $LASTEXITCODE
  } else {
    $rows += [pscustomobject]@{ Skill = $s.Name; Tier = $tier; Result = '未接入'; Detail = '无 eval 入口（见 SKILL.md 验收段）' }
    continue
  }
  $ok = ($code -eq 0)
  if ($ok) { $res = 'PASS' } else { $res = 'FAIL'; $anyFail = $true }
  $detail = (@($out) | Out-String).Trim()
  if ($detail.Length -gt 200) { $detail = $detail.Substring(0, 200) + '…' }
  $rows += [pscustomobject]@{ Skill = $s.Name; Tier = $tier; Result = $res; Detail = $detail }
}

$rows | Format-Table -AutoSize -Wrap
$pass = @($rows | Where-Object { $_.Result -eq 'PASS' }).Count
$fail = @($rows | Where-Object { $_.Result -eq 'FAIL' }).Count
$skip = @($rows | Where-Object { $_.Result -eq '未接入' }).Count
Write-Output ("合计: PASS=" + $pass + " FAIL=" + $fail + " 未接入=" + $skip)
if ($Strict -and $anyFail) { exit 1 }
exit 0
