# check-doc-refs.ps1 — 结构性对账:docs/ 里的死链(含大小写错链:目标存在但大小写不一致,大小写敏感系统上会断)、未填占位符、标了 N2 却缺 `**验收**` / 没有「危险实现清单」、N2 模块缺「失败语义」、危险实现清单行未填(空/占位符)、现状文档引记录、入口文档点具体 ADR 条目。
# 用法:
#   powershell -File check-doc-refs.ps1
#   powershell -File check-doc-refs.ps1 -Strict
param([switch]$Strict)
$ErrorActionPreference = 'SilentlyContinue'

# 按项目改:文档扩展名(含点)。默认同时认 .md 与 .markdown。
$DocExt = @('.md', '.markdown')

# L2 文件名来自 scripts/l2-docs.txt；缺失时用默认值。
$L2Docs = @((Get-Content (Join-Path $PSScriptRoot 'l2-docs.txt') -Raw -Encoding UTF8 -ErrorAction SilentlyContinue) -split "\r?\n" |
  Where-Object { $_ -and $_.Trim() -and $_.Trim() -notmatch '^#' } |
  ForEach-Object { $_.Trim() })
if ($L2Docs.Count -eq 0) { $L2Docs = @('docs/architecture.md','docs/architecture.markdown') }

# 按项目改:对账要排除的路径(正则,匹配即跳过)。默认排除"不是本项目当前维护的文档"的那些:存档层
# (如 docs/legacy/、docs/archive/、docs/experiment/、docs/scaffolds/)、记录类(docs/decisions/、
# docs/reviews/——历史快照,引用退役术语/旧链接是常态,不是错误)与待填件目录(docs/templates/——
# 有些项目把待填件放在 docs/ 内)。
# 置空字符串则不过滤。
$DocExclude = '^(docs/legacy/|docs/archive/|docs/experiment/|docs/scaffolds/|docs/decisions/|docs/templates/|docs/reviews/)'

$root = (git rev-parse --show-toplevel 2>$null)
if (-not $root) { $root = (Get-Location).Path }
Set-Location $root
if (-not (Test-Path 'docs')) { Write-Host '[check-doc-refs] 无 docs/,跳过'; exit 0 }

$docsMd = Get-ChildItem -Path 'docs' -Recurse -File | Where-Object { $DocExt -ccontains $_.Extension }
if (($docsMd | Measure-Object).Count -eq 0) {
  Write-Host "[check-doc-refs] 警告:docs/ 下没有匹配 DocExt=$($DocExt -join ',') 的文件。"
  Write-Host '                 若你的文档用别的扩展名,改脚本顶部的 DocExt / DOC_EXT。'
  exit 0
}

# 排除存档层(不是本项目当前维护的文档;见顶部 $DocExclude)
if ($DocExclude) {
  $docsMd = @($docsMd | Where-Object {
    $rel = $_.FullName.Substring($root.Length).TrimStart('\','/').Replace('\','/')
    $rel -notmatch $DocExclude
  })
}

$found = $false

# HTML 注释 + fenced code block 剥离(行数保真;模板引导注释 / 示例代码不算正文)——#3 计数与 #4 引用扫描共用
function Strip-Comments([string[]]$lines) {
  $out = New-Object System.Collections.Generic.List[string]
  $inC = $false
  $inFence = $false
  foreach ($line in $lines) {
    $s = $line.TrimStart()
    if ($inFence) {
      if ($s.StartsWith('```') -or $s.StartsWith('~~~')) { $inFence = $false }
      $out.Add('')
      continue
    }
    if ($s.StartsWith('```') -or $s.StartsWith('~~~')) {
      $inFence = $true
      $out.Add('')
      continue
    }
    $buf = $line; $outLine = ''
    while ($buf -ne '') {
      if ($inC) {
        $i = $buf.IndexOf('-->')
        if ($i -lt 0) { $buf = ''; break }
        $buf = $buf.Substring($i + 3); $inC = $false
      } else {
        $i = $buf.IndexOf('<!--')
        if ($i -lt 0) { $outLine += $buf; $buf = ''; break }
        $outLine += $buf.Substring(0, $i)
        $buf = $buf.Substring($i + 4); $inC = $true
      }
    }
    $out.Add($outLine)
  }
  return ,$out
}

# 1) 死链
foreach ($f in $docsMd) {
  $rel = $f.FullName.Substring($root.Length).TrimStart('\','/').Replace('\','/')
  $text = (Strip-Comments @(Get-Content -LiteralPath $f.FullName -Encoding UTF8)) -join "`n"
  foreach ($m in [regex]::Matches($text, '\]\(([^)]+)\)')) {
    $t = $m.Groups[1].Value
    if ($t -match '^(https?:|#|mailto:)') { continue }
    $t = ($t -split '#')[0]
    if ([string]::IsNullOrWhiteSpace($t)) { continue }
    if ($t -notmatch '[/.]') { continue }   # 只看"像路径"的目标,跳过 `](被拒)` 这类标注
    $cand1 = Join-Path $f.DirectoryName $t
    $cand2 = Join-Path $root $t
    # 存在性之后再做字面大小写比对:大小写不敏感文件系统(Windows/默认 macOS)会放过
    # 错大小写链接,在大小写敏感系统(Linux CI)上会断。-ceq = 大小写敏感比较。
    $exact = $false; $caseHit = $false
    foreach ($p in @($cand1, $cand2)) {
      if (Test-Path -LiteralPath $p) {
        $base = [IO.Path]::GetFileName($p)
        if ([string]::IsNullOrEmpty($base)) { $exact = $true; continue }   # 尾斜杠目录链接:不比大小写
        $dir  = [IO.Path]::GetDirectoryName($p)
        if (Get-ChildItem -LiteralPath $dir -Force -ErrorAction SilentlyContinue |
              Where-Object { $_.Name -ceq $base }) { $exact = $true }
        else { $caseHit = $true }
      }
    }
    if (-not $exact) {
      if ($caseHit) {
        Write-Host "[case-mismatch] ${rel} -> $t(目标存在但大小写不一致,大小写敏感系统上会断)"
      } else {
        Write-Host "[dead-link] ${rel} -> $t"
      }
      $found = $true
    }
  }
}

# 2) 未填占位符 / TODO
$ph = $docsMd | Select-String -Pattern 'TODO|TBD|与用户对话后填|novelty=N[?]|未填写|待补充' -Encoding UTF8
if ($ph) {
  Write-Host '[placeholder] docs/ 仍有未填占位符 / TODO:'
  $ph | ForEach-Object { $relp = $_.Path.Substring($root.Length).TrimStart('\','/').Replace('\','/'); Write-Host "  ${relp}:$($_.LineNumber):$($_.Line)" }
  $found = $true
}

# 3) N2 结构：L2 与承载五件套的模块（模块以「危险实现清单」判定）。
#    先剥 HTML 注释与 fenced code；只做字面计数，语义归复核。
$targets = @()
foreach ($n in $L2Docs) { if (Test-Path $n) { $targets += $n } }
if (Test-Path 'docs/modules') {
  $targets += (Get-ChildItem 'docs/modules' -File | Where-Object { $DocExt -ccontains $_.Extension } | ForEach-Object { $_.FullName.Substring($root.Length).TrimStart('\','/').Replace('\','/') })
}
foreach ($f in $targets) {
  $raw = Get-Content -Raw -LiteralPath $f -Encoding UTF8
  if ($null -eq $raw) { continue }
  $body = (Strip-Comments ($raw -split "`n")) -join "`n"
  $n2  = ([regex]::Matches($body, 'novelty=N2')).Count
  $acc = ([regex]::Matches($body, '\*\*验收\*\*')).Count
  $dan = ([regex]::Matches($body, '危险实现清单')).Count
  if ($f -like 'docs/modules/*') {
    if ($dan -gt 0) {
      if ($n2 -eq 0) {
        Write-Host "[n2-missing-marker] $($f): 承载五件套(含「危险实现清单」),但没有 novelty=N2"
        $found = $true
      } elseif ($n2 -gt $acc) {
        Write-Host "[n2-missing-verification] $($f): N2 条目 $n2 个,「**验收**」仅 $acc 处"
        $found = $true
      }
      if ($body -notmatch '失败语义') {
        Write-Host "[module-missing-failure-semantics] $($f): 承载五件套的模块文档没有「失败语义」一节"
        $found = $true
      }
    }
    continue
  }
  if (($n2 -eq 0) -and ($body -match '### N2:|危险实现清单')) {
    Write-Host "[n2-missing-marker] $($f): 有 N2 结构但没有 novelty=N2"
    $found = $true
  }
  if ($n2 -gt $acc) {
    Write-Host "[n2-missing-verification] $($f): N2 条目 $n2 个,「**验收**」仅 $acc 处"
    $found = $true
  }
  # 标了 N2 却没有「危险实现清单」
  #    没有"指针形"豁免:N2 的正文与 `novelty=N2` 只写在承载它的那份里;
  #    模块文档只留档位标记、不写正文——所以"只声明、不写正文"的形态在 L2 不该存在。
  if (($n2 -gt 0) -and ($dan -eq 0)) {
    Write-Host "[n2-missing-checklist] $($f): 标了 N2 却没有「危险实现清单」"
    $found = $true
  }
}

# 4) 现状文档不得引用记录类（ADR / decisions / reviews）；要引就引稳定代号。
#    $liveDocs = 现状 / 规则类文档;L2 用上面的 $L2Docs。
$liveDocs = @($L2Docs + @('docs/design-contract.md','docs/glossary.md','docs/glossary.markdown'))
foreach ($n in @('docs/core-analysis.md','docs/core-analysis.markdown')) { if (Test-Path $n) { $liveDocs += $n } }
if (Test-Path 'docs/modules') {
  $liveDocs += (Get-ChildItem 'docs/modules' -File | Where-Object { $DocExt -ccontains $_.Extension } | ForEach-Object { $_.FullName.Substring($root.Length).TrimStart('\','/').Replace('\','/') })
}

$refPat = 'docs/decisions/|docs/reviews/|ADR-\d{3}|adr-\d{3}-'
foreach ($f in $liveDocs) {
  if (-not (Test-Path -LiteralPath $f)) { continue }
  $raw = Get-Content -Raw -LiteralPath $f -Encoding UTF8
  if ($null -eq $raw) { continue }
  $ln = 0
  foreach ($line in (Strip-Comments ($raw -split "`n"))) {   # 先剥注释 / fence；命中即报
    $ln++
    if ($line -match $refPat) {
      Write-Host "[live-doc-refs] ${f}:${ln}:${line}: 现状类文档引了记录类文档(记录会过期,条款不会;引条款请用稳定代号,如 D-14;要理由 / 被拒方案,从 L1 的活文档索引进)"
      $found = $true
    }
  }
}

# 4b) 入口文档不得点具体 ADR 条目；目录级引用可以，000 模板例外。
#    按项目改:L1 的宿主文件名(全部存在才查)。
$l1Files = @('AGENTS.md','CLAUDE.md','.cursor/rules/project.mdc','.windsurfrules','.github/copilot-instructions.md')
foreach ($f in $l1Files) {
  if (-not (Test-Path -LiteralPath $f)) { continue }
  $raw = Get-Content -Raw -LiteralPath $f -Encoding UTF8
  if ($null -eq $raw) { continue }
  $ln = 0
  foreach ($line in ($raw -split "`n")) {
    $ln++
    foreach ($m in [regex]::Matches($line, '(?i)(?:ADR-|adr-)(\d{3})')) {
      if ($m.Groups[1].Value -eq '000') { continue }   # 模板文件名,不是决策
      Write-Host "[l1-entry-ref] ${f}:${ln}:${line}: 入口文档点了具体 ADR 条目(索引只写『哪份文档管什么』,不点条目)"
      $found = $true
      break
    }
  }
}

# 5) 危险实现清单：数据行的「挡住者」列不能是空 / 占位符。
#    列位置按表头含“挡住”定位；只查填没填，是否真挡住归复核。
foreach ($f in $targets) {
  $raw = Get-Content -Raw -LiteralPath $f -Encoding UTF8
  if ($null -eq $raw) { continue }
  $ln2 = 0; $inSec = $false; $inTab = $false; $bcol = -1
  foreach ($line in (Strip-Comments ($raw -split "`n"))) {
    $ln2++
    if ($line -match '^#+\s*\**危险实现清单' -or $line -match '^(\s*-\s+)?\*\*危险实现清单') { $inSec = $true; $inTab = $false; $bcol = -1; continue }
    if (-not $inSec) { continue }
    if ($line -match '^#') { $inSec = $false; $inTab = $false; $bcol = -1; continue }
    if ($line -match '^\|') {
      $cells = $line -split '\|'
      if (-not $inTab) {   # 表头行:定位"挡住者"列
        $inTab = $true; $bcol = -1
        for ($j = 1; $j -lt $cells.Count; $j++) { if ($cells[$j] -match '挡住') { $bcol = $j; break } }
        continue
      }
      if ($bcol -lt 0) { continue }   # 表头没有"挡住"列 → 不猜
      if ($line -match '^\|[\s:|-]+\|\s*$') { continue }   # 分隔行
      $cell = ''
      if ($cells.Count -gt $bcol) { $cell = $cells[$bcol] }
      $lc = $cell.Trim().ToLower()
      if ($lc -eq '' -or $lc -match '^(-|—|待补|tbd|todo|\?|n/a)$') {
        Write-Host "[danger-blocker] ${f}:${ln2}:${line}: 危险实现清单行未填(""挡住者""列为空 / 占位符)"
        $found = $true
      }
      continue
    }
    if ($inTab) { $inSec = $false; $inTab = $false; $bcol = -1 }   # 表后首个非表行 → 结束
  }
}

if (-not $found) {
  Write-Host "[check-doc-refs] 无结构性发现(扫描 $($docsMd.Count) 个文档)。"
} else {
  Write-Host '[check-doc-refs] 以上为结构性提醒;语义一致性请跑 teach-back 验证者。'
  if ($Strict) { exit 1 }
}
exit 0
