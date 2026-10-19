# drawio-export 验收（smoke）：正常生成 + 负控拒绝
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$tmp = Join-Path $env:TEMP ('drawio-eval-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $tmp -Force | Out-Null
try {
    $spec = '{"pages":[{"name":"t","nodes":[{"id":"a","label":"开始","type":"rounded","x":0,"y":0,"w":120,"h":60},{"id":"b","label":"结束","type":"rectangle","x":220,"y":0,"w":120,"h":60}],"edges":[{"from":"a","to":"b"}]}]}'
    [System.IO.File]::WriteAllText((Join-Path $tmp 'spec.json'), $spec)
    & python (Join-Path $root 'drawio_helper.py') create --spec-file (Join-Path $tmp 'spec.json') -o (Join-Path $tmp 'out.drawio') | Out-Null
    if ($LASTEXITCODE -ne 0) { Write-Output 'FAIL good-case: exit != 0'; exit 1 }
    $out = Join-Path $tmp 'out.drawio'
    if (-not (Test-Path $out)) { Write-Output 'FAIL good-case: output missing'; exit 1 }
    if ((Get-Content $out -Raw) -notmatch '<mxfile') { Write-Output 'FAIL good-case: output is not .drawio (no <mxfile)'; exit 1 }

    $bad = '{"pages":[{"nodes":[{"id":"a","label":"x"},{"id":"a","label":"y"}],"edges":[]}]}'
    [System.IO.File]::WriteAllText((Join-Path $tmp 'bad.json'), $bad)
    & python (Join-Path $root 'drawio_helper.py') create --spec-file (Join-Path $tmp 'bad.json') -o (Join-Path $tmp 'bad.drawio') | Out-Null
    if ($LASTEXITCODE -eq 0) { Write-Output 'FAIL negctl: duplicate ids were not rejected'; exit 1 }
    if (Test-Path (Join-Path $tmp 'bad.drawio')) { Write-Output 'FAIL negctl: bad output was written'; exit 1 }

    Write-Output 'PASS drawio-export smoke (good: generated; negctl: rejected)'
    exit 0
} catch {
    Write-Output ('FAIL ' + $_.Exception.Message)
    exit 1
} finally {
    Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
}
