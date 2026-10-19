<#
check-skills.ps1 — skill 结构机器检查（低成本一批）。
用法:
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check-skills.ps1            # 全量扫描
  ... -Changed                                                                             # 只查本次变更涉及的 skill（git）
  ... -Name drawio-export                                                                  # 只查一个
  ... -Strict                                                                              # 有 FAIL 时 exit 1
检查项:
  1. frontmatter 存在,且 name == 目录名
  2. description 含 TRIGGER
  3. SKILL.md 的引用（一层,不递归）全部可解析（死链 = FAIL）
  4. SKILL.md 行数 <= 500（超出 = WARN）
判定: FAIL（结构/死链）默认只提示, -Strict 才阻断; WARN 仅提示。
#>
param(
  [switch]$Strict,
  [switch]$Changed,
  [string]$Name
)
$ErrorActionPreference = 'Stop'
$repo = Split-Path $PSScriptRoot -Parent
$lineLimit = 500

$skills = @(Get-ChildItem $repo -Directory | Where-Object {
  $_.Name -notin @('.git', 'scripts', 'dist', 'node_modules') -and
  (Test-Path (Join-Path $_.FullName 'SKILL.md'))
})

if ($Changed) {
  $oldEap = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  try {
    $paths = @(& git -C $repo diff --name-only HEAD 2>$null)
    $paths += @(& git -C $repo ls-files --others --exclude-standard 2>$null)
  } finally {
    $ErrorActionPreference = $oldEap
  }
  $touched = @($paths | Where-Object { $_ } | ForEach-Object { ($_ -split '/')[0] } | Select-Object -Unique)
  $skills = @($skills | Where-Object { $touched -contains $_.Name })
  if ($skills.Count -eq 0) { Write-Output '本次变更未涉及任何 skill。'; exit 0 }
}
if ($Name) {
  $skills = @($skills | Where-Object { $_.Name -eq $Name })
  if ($skills.Count -eq 0) { Write-Output "未找到 skill: $Name"; exit 2 }
}

$rows = @()
foreach ($skill in $skills) {
  $mdPath = Join-Path $skill.FullName 'SKILL.md'
  $text = [System.IO.File]::ReadAllText($mdPath, [System.Text.Encoding]::UTF8)
  $lines = $text -split "`r?`n"
  $lineCount = $lines.Count
  if ($lines.Count -gt 0 -and $lines[$lines.Count - 1] -eq '') { $lineCount-- }

  $fail = @()
  $warn = @()
  $fmName = ''
  $fmOk = $false
  $descText = ''
  if ($lines.Count -gt 2 -and $lines[0].Trim() -eq '---') {
    $end = -1
    for ($i = 1; $i -lt [Math]::Min($lines.Count, 100); $i++) {
      if ($lines[$i].Trim() -eq '---') { $end = $i; break }
    }
    if ($end -gt 0) {
      $fmOk = $true
      $fm = $lines[1..($end - 1)]
      for ($i = 0; $i -lt $fm.Count; $i++) {
        if ($fm[$i] -match '^name:\s*(.+?)\s*$') {
          $fmName = $matches[1].Trim().Trim('"').Trim("'")
        }
        if ($fm[$i] -match '^description:\s*(.*)$') {
          $v = $matches[1].Trim()
          if ($v -eq '' -or $v -eq '|' -or $v -eq '>') {
            $buf = @()
            $j = $i + 1
            while ($j -lt $fm.Count -and ($fm[$j] -match '^\s+' -or $fm[$j].Trim() -eq '')) {
              $buf += $fm[$j]
              $j++
            }
            $descText = ($buf -join "`n")
          } else {
            $descText = $v
          }
        }
      }
    }
  }
  if (-not $fmOk) { $fail += '缺 frontmatter' }
  elseif ($fmName -ne $skill.Name) { $fail += ("name=" + $(if ($fmName) { $fmName } else { '(空)' }) + " ≠ 目录") }
  if ($descText -notmatch 'TRIGGER') { $warn += 'description 缺 TRIGGER' }

  $dead = @()
  foreach ($m in [regex]::Matches($text, '!?\[[^\]]*\]\(([^)]+)\)')) {
    $t = $m.Groups[1].Value.Trim()
    if ($t -match '^(https?:|mailto:|#|[a-zA-Z]+:)') { continue }
    $t = ($t -split '#')[0]
    $t = ($t -split '\?')[0]
    $t = $t.Trim().Trim('<>').Trim()
    if (-not $t) { continue }
    $resolved = Join-Path $skill.FullName $t
    if (-not (Test-Path $resolved)) { $dead += $t }
  }
  if ($dead.Count -gt 0) { $fail += ("死链: " + (($dead | Select-Object -Unique) -join ', ')) }
  if ($lineCount -gt $lineLimit) { $warn += ("SKILL.md " + $lineCount + " 行 > " + $lineLimit) }

  $status = if ($fail.Count -gt 0) { 'FAIL' } elseif ($warn.Count -gt 0) { 'WARN' } else { 'PASS' }
  $detail = (@($fail + $warn)) -join '; '
  $rows += [pscustomobject]@{
    Skill  = $skill.Name
    Status = $status
    Lines  = $lineCount
    Detail = $detail
  }
}

$rows | Format-Table -AutoSize
$p = @($rows | Where-Object { $_.Status -eq 'PASS' }).Count
$w = @($rows | Where-Object { $_.Status -eq 'WARN' }).Count
$f = @($rows | Where-Object { $_.Status -eq 'FAIL' }).Count
Write-Output ("合计: PASS={0} WARN={1} FAIL={2}" -f $p, $w, $f)

if ($Strict -and $f -gt 0) { exit 1 }
exit 0
