# pptx-delivery 验收入口（无渲染子集）
# 9 组负控 + 干净基线（用 tests/out 里已构建的 deck，不重建、不渲染）+ C5/C7 检查器自测。
# 不写 tests/evidence/，可在钩子 / CI 里跑而不脏工作区；全量（含构建与渲染）仍用 python tests/run_tests.py。
$ErrorActionPreference = 'Continue'
$root = Split-Path $PSScriptRoot -Parent
Push-Location $root
try {
    # 干净克隆里 tests/out（构建缓存，不入库）不存在：退化为只跑检查器自测，并如实说明跳过了控制组。
    if (-not (Test-Path 'tests/out/clean.pptx')) {
        Write-Output 'SKIP control suite: tests/out 无已构建 fixture（干净克隆）；先跑 python tests/run_tests.py 构建。仅跑检查器自测。'
    } else {
        python tests/run_tests.py --which controls --no-build --no-render --no-evidence
        if ($LASTEXITCODE -ne 0) { Write-Output 'FAIL pptx-delivery: control suite (9 负控 + 干净基线)'; exit 1 }
    }

    python tests/c5_selftest.py | Out-Null
    if ($LASTEXITCODE -ne 0) { Write-Output 'FAIL pptx-delivery: C5 selftest'; exit 1 }

    python tests/c7_selftest.py | Out-Null
    if ($LASTEXITCODE -ne 0) { Write-Output 'FAIL pptx-delivery: C7 selftest'; exit 1 }

    Write-Output 'PASS pptx-delivery (render-free subset: controls + C5/C7 selftests)'
    exit 0
} finally {
    Pop-Location
}
