<#
.SYNOPSIS
  账本自检:列完整性 / 证伪条件与动作 / 判据来源 / 层 / 视图容量。

.DESCRIPTION
  只报告,不改文件。红 != 错:退出码 1 是裁决输入,状态列由人改。
  这是与「退役形态」无关的那部分检查;编号复用与状态枚举等约定拍板后再加。
  缺省扫 docs/scaffolds/*-ledger.md;扫不到就静默通过(0 份账本不是错)。

.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check-ledger.ps1 -Path docs/scaffolds/x-ledger.md
#>
param(
  [string[]]$Path = @(),
  [switch]$Quiet
)

$ErrorActionPreference = 'Stop'

$RequiredColumns = @('事件(摩擦)', '断言', '层', '证伪条件', '证伪动作', '判据 / 取证', '状态', '载体')
$ActionPrefixes = @('复跑', '对照', '盲评', '人看')
$JudgeSources = @('用户编码', '用户确认', 'AI 自拟', '用户裁决')
$ViewLimit = 5

function Get-LedgerFiles {
  param([string[]]$InputPath)
  $files = New-Object System.Collections.ArrayList
  if ($InputPath.Count -eq 0) {
    if (Test-Path 'docs/scaffolds') {
      Get-ChildItem -Path 'docs/scaffolds' -Filter '*-ledger.md' -File -ErrorAction SilentlyContinue |
        ForEach-Object { [void]$files.Add($_.FullName) }
    }
    return @($files)
  }
  foreach ($p in $InputPath) {
    if (Test-Path -Path $p -PathType Container) {
      Get-ChildItem -Path $p -Filter '*-ledger.md' -File -ErrorAction SilentlyContinue |
        ForEach-Object { [void]$files.Add($_.FullName) }
    } elseif (Test-Path -Path $p -PathType Leaf) {
      [void]$files.Add((Resolve-Path $p).Path)
    } else {
      Write-Output ("[FAIL] L-FILE 找不到路径: {0}" -f $p)
      $script:hadFail = $true
    }
  }
  return @($files)
}

function Split-TableRow {
  param([string]$Line)
  $t = $Line.Trim()
  if ($t.StartsWith('|')) { $t = $t.Substring(1) }
  if ($t.EndsWith('|')) { $t = $t.Substring(0, $t.Length - 1) }
  return @($t -split '\|' | ForEach-Object { $_.Trim() })
}

function Test-SeparatorRow {
  param([string[]]$Cells)
  foreach ($c in $Cells) {
    if ($c -notmatch '^:?-{2,}:?$') { return $false }
  }
  return $true
}

function Get-SectionBody {
  param([string[]]$Lines, [string]$StartPattern, [string]$EndPattern)
  $start = -1
  for ($i = 0; $i -lt $Lines.Count; $i++) {
    if ($Lines[$i] -match $StartPattern) { $start = $i; break }
  }
  if ($start -lt 0) { return @() }
  $body = New-Object System.Collections.ArrayList
  for ($j = $start + 1; $j -lt $Lines.Count; $j++) {
    if ($EndPattern -and $Lines[$j] -match $EndPattern) { break }
    [void]$body.Add($Lines[$j])
  }
  return @($body)
}

$script:hadFail = $false
$script:warnCount = 0
$script:failCount = 0

function Add-Finding {
  param([string]$Level, [string]$Code, [string]$Message)
  if ($Level -eq 'FAIL') {
    $script:hadFail = $true
    $script:failCount++
    Write-Output ("[FAIL] {0} {1}" -f $Code, $Message)
  } else {
    $script:warnCount++
    Write-Output ("[WARN] {0} {1}" -f $Code, $Message)
  }
}

$files = Get-LedgerFiles -InputPath $Path
if ($files.Count -eq 0) {
  if (-not $Quiet) { Write-Output "未发现账本(docs/scaffolds/*-ledger.md),无事可查。" }
  exit 0
}

foreach ($file in $files) {
  if (-not $Quiet) { Write-Output ("── {0}" -f $file) }
  $lines = Get-Content -Path $file -Encoding UTF8
  if ($lines.Count -eq 0) {
    Add-Finding 'FAIL' 'L-EMPTY' ("{0}: 空文件" -f $file)
    continue
  }

  # 一、条目
  $rowStatus = @{}
  $prevIdNum = 0
  $entryBody = Get-SectionBody -Lines $lines -StartPattern '^##\s*一、' -EndPattern '^##\s'
  if ($entryBody.Count -eq 0) {
    Add-Finding 'FAIL' 'L-SECTION' ("{0}: 找不到「一、条目」小节" -f $file)
  } else {
    $headerIndex = -1
    for ($i = 0; $i -lt $entryBody.Count; $i++) {
      if ($entryBody[$i].Trim().StartsWith('|') -and $entryBody[$i] -match '事件') { $headerIndex = $i; break }
    }
    if ($headerIndex -lt 0) {
      Add-Finding 'FAIL' 'L-HEADER' ("{0}: 条目表缺少表头" -f $file)
    } else {
      $headerCells = Split-TableRow -Line $entryBody[$headerIndex]
      foreach ($col in $RequiredColumns) {
        if (-not ($headerCells -contains $col)) {
          Add-Finding 'FAIL' 'L-COLNAME' ("{0}: 表头缺列「{1}」" -f $file, $col)
        }
      }
      $expected = $headerCells.Count

      for ($i = $headerIndex + 1; $i -lt $entryBody.Count; $i++) {
        $line = $entryBody[$i]
        if (-not $line.Trim().StartsWith('|')) { break }
        $cells = Split-TableRow -Line $line
        if (Test-SeparatorRow -Cells $cells) { continue }
        if ($cells.Count -ne $expected) {
          Add-Finding 'FAIL' 'L-COLCOUNT' ("{0}: 第 {1} 行有 {2} 列,应为 {3} 列" -f $file, ($i + 1), $cells.Count, $expected)
          continue
        }
        $id = $cells[0]
        $event = $cells[2]
        $claim = $cells[3]
        $layer = $cells[4]
        $falsifyCond = $cells[5]
        $falsifyAct = $cells[6]
        $judge = $cells[7]
        $status = $cells[8]
        $carrier = $cells[9]

        if ([string]::IsNullOrWhiteSpace($claim) -and [string]::IsNullOrWhiteSpace($event)) {
          if (-not $Quiet) { Write-Output ("[NOTE] L-PLACEHOLDER {0}: {1} 是占位行,跳过内容检查" -f $file, $id) }
          continue
        }
        if (-not [string]::IsNullOrWhiteSpace($id)) {
          if ($rowStatus.ContainsKey($id)) {
            Add-Finding 'FAIL' 'L-ID-DUP' ("{0}: 编号 {1} 重复" -f $file, $id)
          } else {
            $rowStatus[$id] = $status
          }
          if ($id -match '^L(\d+)$') {
            $num = [int]$Matches[1]
            if ($num -le $prevIdNum) {
              Add-Finding 'WARN' 'L-ID-ORDER' ("{0}: 编号 {1} 未递增(删除候选后留下的空号可以跳过,但不复用)" -f $file, $id)
            } else {
              $prevIdNum = $num
            }
            $num = 0
          }
        }
        if ([string]::IsNullOrWhiteSpace($claim)) {
          Add-Finding 'FAIL' 'L-CLAIM' ("{0}: {1} 断言为空" -f $file, $id)
        }
        if ([string]::IsNullOrWhiteSpace($falsifyCond)) {
          Add-Finding 'FAIL' 'L-FALSIFY-COND' ("{0}: {1} 缺证伪条件" -f $file, $id)
        }
        if ([string]::IsNullOrWhiteSpace($falsifyAct)) {
          Add-Finding 'FAIL' 'L-FALSIFY-ACT' ("{0}: {1} 缺证伪动作" -f $file, $id)
        } elseif ($falsifyAct -notmatch '^\s*(复跑|对照|盲评|人看)\s*[:：]') {
          Add-Finding 'FAIL' 'L-FALSIFY-ACT-VOCAB' ("{0}: {1} 证伪动作不是四选一(复跑:/对照:/盲评:/人看:): {2}" -f $file, $id, $falsifyAct)
        }
        if ($layer -notmatch '^\[(通用|本地)\]$') {
          Add-Finding 'FAIL' 'L-LAYER' ("{0}: {1} 层必须是 [通用] 或 [本地]: {2}" -f $file, $id, $layer)
        }
        if ([string]::IsNullOrWhiteSpace($judge)) {
          Add-Finding 'FAIL' 'L-JUDGE' ("{0}: {1} 缺判据 / 取证" -f $file, $id)
        } else {
          $hit = $false
          foreach ($src in $JudgeSources) { if ($judge -match [regex]::Escape($src)) { $hit = $true; break } }
          if (-not $hit) {
            Add-Finding 'FAIL' 'L-JUDGE-VOCAB' ("{0}: {1} 判据未标来源(用户编码/用户确认/AI 自拟/用户裁决): {2}" -f $file, $id, $judge)
          }
        }
        if ([string]::IsNullOrWhiteSpace($status)) {
          Add-Finding 'WARN' 'L-STATUS' ("{0}: {1} 状态为空" -f $file, $id)
        }
        if ([string]::IsNullOrWhiteSpace($carrier)) {
          Add-Finding 'WARN' 'L-CARRIER' ("{0}: {1} 载体为空" -f $file, $id)
        }
      }
    }
  }

  # 三、退役记录:退役行必须留档,且必须写替代(或「无替代」)与证据
  $retiredIds = @()
  foreach ($k in $rowStatus.Keys) { if ($rowStatus[$k] -match '^退役') { $retiredIds += $k } }
  $recordIds = @()
  $recordBody = Get-SectionBody -Lines $lines -StartPattern '^##\s*三、' -EndPattern '^##\s'
  if ($recordBody.Count -gt 0) {
    $h = -1
    for ($i = 0; $i -lt $recordBody.Count; $i++) {
      if ($recordBody[$i].Trim().StartsWith('|') -and $recordBody[$i] -match '退役原因') { $h = $i; break }
    }
    if ($recordBody.Count -gt 0 -and $h -lt 0) {
      Add-Finding 'FAIL' 'L-RETIRE-HEADER' ("{0}: 退役记录缺少表头" -f $file)
    } elseif ($h -ge 0) {
      $hc = Split-TableRow -Line $recordBody[$h]
      $idIdx = -1; $altIdx = -1; $evIdx = -1
      for ($i = 0; $i -lt $hc.Count; $i++) {
        if ($hc[$i] -eq '#') { $idIdx = $i }
        if ($hc[$i] -like '替代*') { $altIdx = $i }
        if ($hc[$i] -like '证据*') { $evIdx = $i }
      }
      if ($altIdx -lt 0) {
        Add-Finding 'FAIL' 'L-RETIRE-COL' ("{0}: 退役记录缺「替代」列(写替代 ID 或「无替代」)" -f $file)
      }
      for ($i = $h + 1; $i -lt $recordBody.Count; $i++) {
        $line = $recordBody[$i]
        if (-not $line.Trim().StartsWith('|')) { break }
        $cells = Split-TableRow -Line $line
        if (Test-SeparatorRow -Cells $cells) { continue }
        if ($idIdx -lt 0 -or $cells.Count -le $idIdx) { continue }
        $rid = $cells[$idIdx]
        if ([string]::IsNullOrWhiteSpace($rid)) { continue }
        $recordIds += $rid
        if ($evIdx -lt 0 -or $cells.Count -le $evIdx -or [string]::IsNullOrWhiteSpace($cells[$evIdx])) {
          Add-Finding 'FAIL' 'L-RETIRE-EVID' ("{0}: 退役记录 {1} 缺证据(证伪现象 / 复评结论)" -f $file, $rid)
        }
        if ($altIdx -ge 0 -and ($cells.Count -le $altIdx -or [string]::IsNullOrWhiteSpace($cells[$altIdx]))) {
          Add-Finding 'FAIL' 'L-RETIRE-ALT' ("{0}: 退役记录 {1} 缺替代(写替代 ID 或「无替代」)" -f $file, $rid)
        }
      }
    }
  }
  foreach ($rid in $recordIds) {
    if (-not $rowStatus.ContainsKey($rid)) {
      Add-Finding 'FAIL' 'L-RETIRE-ROW-GONE' ("{0}: 退役记录引用了 {1},但条目里没有这一行(生效过的条目退役后必须留在账本)" -f $file, $rid)
    }
  }
  foreach ($rid in $retiredIds) {
    if ($recordIds -notcontains $rid) {
      Add-Finding 'FAIL' 'L-RETIRE-RECORD' ("{0}: {1} 状态是退役,但退役记录里没有它" -f $file, $rid)
    }
  }

  # 二、视图容量
  $viewBody = Get-SectionBody -Lines $lines -StartPattern '^##\s*二、' -EndPattern '^##\s'
  $viewItems = 0
  foreach ($l in $viewBody) {
    $t = $l.Trim()
    if ($t -eq '') { continue }
    if ($t.StartsWith('<!--') -or $t.StartsWith('>')) { continue }
    if ($t.StartsWith('|') -and (Split-TableRow -Line $t)[0] -eq '') { continue }
    if ($t -match '^[-*]\s+' -or ($t.StartsWith('|') -and $t -notmatch '^[\|\s\-:]+$')) { $viewItems++ }
  }
  if ($viewItems -gt $ViewLimit) {
    Add-Finding 'WARN' 'L-VIEW' ("{0}: 视图 {1} 条,超过上限 {2}" -f $file, $viewItems, $ViewLimit)
  }
  $reportedRetired = @{}
  foreach ($l in $viewBody) {
    foreach ($m in [regex]::Matches($l, 'L\d+')) {
      if (($retiredIds -contains $m.Value) -and (-not $reportedRetired.ContainsKey($m.Value))) {
        $reportedRetired[$m.Value] = $true
        Add-Finding 'FAIL' 'L-VIEW-RETIRED' ("{0}: 视图里出现已退役条目 {1}(退役行只留在账本,不进视图)" -f $file, $m.Value)
      }
    }
  }
}

if (-not $Quiet) {
  Write-Output ''
  Write-Output ("合计: FAIL={0} WARN={1} 文件={2}" -f $script:failCount, $script:warnCount, $files.Count)
  if ($script:failCount -gt 0) {
    Write-Output '红是裁决输入,不是自动状态变更:缺动作/缺判据先补人,不补模板。'
  }
}

if ($script:hadFail) { exit 1 } else { exit 0 }
