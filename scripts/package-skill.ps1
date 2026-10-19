<#
package-skill.ps1 — 把单个 skill 打成可交付包（带版本、验收档、来源提交、SHA256）。
用法:
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts/package-skill.ps1 -Name drawio-export
  ... -Force          # 允许低于 golden 档的 skill 也打包（manifest 如实标注 forced=true）
  ... -OutDir dist    # 默认 dist/
规则:
  - 只打 <repo>/<skill>/；排除 .cache / .calibration / .commandcode / __pycache__ / node_modules
  - version 取 SKILL.md frontmatter 的 version:（缺省 0.0.0）
  - 验收档取 SKILL.md 的 `## 验收` 段；非 golden/acceptance 需 -Force
  - 产出: <OutDir>/<name>-<version>.zip、<name>-<version>.manifest.json、<zip>.sha256
#>
param(
  [string]$Name,
  [string]$OutDir = 'dist',
  [switch]$Force
)
$ErrorActionPreference = 'Stop'
$repo = Split-Path $PSScriptRoot -Parent
if (-not $Name) { Write-Output '缺 -Name'; exit 2 }
$src = Join-Path $repo $Name
if (-not (Test-Path (Join-Path $src 'SKILL.md'))) { Write-Output "不是 skill 目录: $Name"; exit 2 }

$md = Get-Content (Join-Path $src 'SKILL.md') -Raw -Encoding UTF8
$ver = '0.0.0'
$vm = [regex]::Match($md, '(?m)^version\s*:\s*(.+)$')
if ($vm.Success) {
  $v = $vm.Groups[1].Value.Trim().Trim('"').Trim("'").Trim()
  if ($v) { $ver = $v }
}
$tier = '未验收'
$sec = [regex]::Match($md, '(?ms)^##\s*验收[^\r\n]*\r?\n(.*?)(?=^##\s|\z)')
if ($sec.Success) {
  $t = [regex]::Match($sec.Groups[1].Value, '档位\s*[:：]\s*[*`]*\s*(smoke|golden|acceptance|teach-back)')
  if ($t.Success) { $tier = $t.Groups[1].Value }
}
if ((@('golden', 'acceptance') -notcontains $tier) -and (-not $Force)) {
  Write-Output ("拒绝打包:{0} 的验收档为 {1}(< golden)。确认要发就用 -Force(manifest 会如实标注)。" -f $Name, $tier)
  exit 1
}

$commit = (& git -C $repo rev-parse --short HEAD).Trim()
$outPath = Join-Path $repo $OutDir
New-Item -ItemType Directory -Path $outPath -Force | Out-Null
$tmp = Join-Path $env:TEMP ("pkg-" + $Name + "-" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $tmp -Force | Out-Null
try {
  $exclude = '\\(\.cache|\.calibration|\.commandcode|__pycache__|node_modules)(\\|$)'
  Get-ChildItem $src -Recurse -File | Where-Object { $_.FullName.Substring($src.Length) -notmatch $exclude } | ForEach-Object {
    $rel = $_.FullName.Substring($src.Length).TrimStart('\')
    $dst = Join-Path $tmp $rel
    New-Item -ItemType Directory -Path (Split-Path $dst -Parent) -Force | Out-Null
    Copy-Item $_.FullName $dst -Force
  }
  $zip = Join-Path $outPath ("{0}-{1}.zip" -f $Name, $ver)
  if (Test-Path $zip) { Remove-Item $zip -Force }
  Compress-Archive -Path (Join-Path $tmp '*') -DestinationPath $zip -CompressionLevel Optimal
  $sha = (Get-FileHash $zip -Algorithm SHA256).Hash.ToLower()
  $manifest = [ordered]@{
    name          = $Name
    version       = $ver
    eval_tier     = $tier
    forced        = [bool]$Force
    source_commit = $commit
    created_at    = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    file          = (Split-Path $zip -Leaf)
    sha256        = $sha
  }
  $manifestPath = Join-Path $outPath ("{0}-{1}.manifest.json" -f $Name, $ver)
  [System.IO.File]::WriteAllText($manifestPath, ($manifest | ConvertTo-Json -Depth 4), (New-Object System.Text.UTF8Encoding($false)))
  [System.IO.File]::WriteAllText(($zip + '.sha256'), ($sha + "`n"), (New-Object System.Text.UTF8Encoding($false)))
  Write-Output ("PACKED {0} {1} tier={2} commit={3}" -f $Name, $ver, $tier, $commit)
  Write-Output ("zip={0}" -f $zip)
  Write-Output ("sha256={0}" -f $sha)
} finally {
  Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
}
