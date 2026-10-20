<#
check-ps1-bom.ps1 — 检查仓库内 .ps1 是否带 UTF-8 BOM。
Windows PowerShell 5.1 对无 BOM 的 UTF-8 脚本按 ANSI/GBK 解码,中文会被撕裂成语法错(本仓不变量 8)。
用法:
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check-ps1-bom.ps1            # 只提示
  ... -Strict                                                                               # 有缺失时 exit 1
  ... -Root <dir>                                                                           # 指定根目录(自测用)
#>
param(
  [switch]$Strict,
  [string]$Root
)
$ErrorActionPreference = 'Stop'
if (-not $Root) { $Root = Split-Path $PSScriptRoot -Parent }
$Root = (Resolve-Path $Root).Path

$files = @(Get-ChildItem -Path $Root -Recurse -File -Filter *.ps1 -ErrorAction SilentlyContinue |
  Where-Object { $_.FullName -notmatch '\\(\.git|node_modules|dist|__pycache__)\\' })

$rows = @()
$missing = 0
foreach ($f in $files) {
  $hasBom = $false
  $fs = [System.IO.File]::OpenRead($f.FullName)
  try {
    $buf = New-Object byte[] 3
    $n = $fs.Read($buf, 0, 3)
    $hasBom = ($n -eq 3 -and $buf[0] -eq 0xEF -and $buf[1] -eq 0xBB -and $buf[2] -eq 0xBF)
  } finally {
    $fs.Dispose()
  }
  if (-not $hasBom) { $missing++ }
  $rows += [pscustomobject]@{
    Path   = $f.FullName.Substring($Root.Length).TrimStart('\')
    Status = if ($hasBom) { 'OK' } else { 'MISSING' }
  }
}

$rows | Format-Table -AutoSize
Write-Output ("合计: 文件={0} 缺BOM={1}" -f $files.Count, $missing)

if ($Strict -and $missing -gt 0) { exit 1 }
exit 0
