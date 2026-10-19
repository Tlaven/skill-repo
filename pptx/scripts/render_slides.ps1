# render_slides.ps1 - Render a PPTX to per-slide PNGs (and optionally PDF) via PowerPoint COM.
#
# Windows-only. Uses the "PowerPoint.Application" COM server, which is provided by
# either Microsoft PowerPoint or WPS Office (本机 WPS 26.8.1 的 COM 兼容接口实测, 2026-10-19).
# Cross-platform alternative: python scripts/office/soffice.py --headless --convert-to pdf
#
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts/render_slides.ps1 -Pptx deck.pptx -OutDir render/ -Pdf
#
# Outputs: <OutDir>/slide-01.png, slide-02.png, ... ; with -Pdf also <OutDir>/<name>.pdf

param(
  [Parameter(Mandatory = $true)][string]$Pptx,
  [Parameter(Mandatory = $true)][string]$OutDir,
  [int]$Width = 1920,
  [int]$Height = 1080,
  [switch]$Pdf
)

$ErrorActionPreference = 'Stop'

$pptxPath = (Resolve-Path -LiteralPath $Pptx).Path
if (-not (Test-Path -LiteralPath $OutDir)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }
$outPath = (Resolve-Path -LiteralPath $OutDir).Path
$baseName = [System.IO.Path]::GetFileNameWithoutExtension($pptxPath)

Write-Host "[render] open: $pptxPath"
$app = New-Object -ComObject PowerPoint.Application
$pres = $null
try {
  $pres = $app.Presentations.Open($pptxPath, $true, $false, $false)  # ReadOnly, Untitled:$false, WithWindow:$false
  $n = $pres.Slides.Count
  Write-Host "[render] slides: $n"
  for ($i = 1; $i -le $n; $i++) {
    $target = Join-Path $outPath ("slide-{0:d2}.png" -f $i)
    $pres.Slides.Item($i).Export($target, "PNG", $Width, $Height)
    Write-Host "[render] png: $target"
  }
  if ($Pdf) {
    $pdfTarget = Join-Path $outPath "$baseName.pdf"
    $pres.SaveAs($pdfTarget, 32)  # ppSaveAsPDF = 32
    Write-Host "[render] pdf: $pdfTarget"
  }
  $pres.Close()
  Write-Host "[render] done: $n slide(s) -> $outPath"
} finally {
  if ($null -ne $pres) { try { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($pres) | Out-Null } catch {} }
  try { $app.Quit() } catch {}
  try { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($app) | Out-Null } catch {}
}
