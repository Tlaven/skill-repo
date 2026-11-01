# pptx-delivery 验收入口（无渲染子集）
# 9 组负控 + 干净基线（从源码重新构建 fixture，不渲染）+ C5/C7 检查器自测。
# 不写 tests/evidence/，可在钩子 / CI 里跑而不脏工作区；全量（含渲染）仍用 python tests/run_tests.py。
$ErrorActionPreference = 'Continue'
$root = Split-Path $PSScriptRoot -Parent
Push-Location $root
try {
    if (Get-Command node -ErrorAction SilentlyContinue) {
        python tests/run_tests.py --which controls --no-render --no-evidence
        if ($LASTEXITCODE -ne 0) { Write-Output 'FAIL pptx-delivery: control suite (9 负控 + 干净基线)'; exit 1 }
    } else {
        Write-Output 'SKIP control suite: 未找到 node（构建 fixture 需要全局 pptxgenjs / sharp）。仅跑检查器自测。'
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
