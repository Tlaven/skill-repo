# pptx-delivery 验收入口（环境无关子集）
# 只跑检查器自身的红/绿自测：C5 叠层背景解析、C7 页面越界检测（人造输入，不依赖渲染器与 poppler 版本）。
# 全量（构建 + 渲染 + 9 组负控）仍用 python tests/run_tests.py——它依赖具体机器的渲染器与 pdftotext，
# 不适合放进钩子：同一套 deck 在 Git 自带 pdftotext 下会多出 C7/C8 误报。
$ErrorActionPreference = 'Continue'
$root = Split-Path $PSScriptRoot -Parent
Push-Location $root
try {
    python tests/c5_selftest.py | Out-Null
    if ($LASTEXITCODE -ne 0) { Write-Output 'FAIL pptx-delivery: C5 selftest'; exit 1 }

    python tests/c7_selftest.py | Out-Null
    if ($LASTEXITCODE -ne 0) { Write-Output 'FAIL pptx-delivery: C7 selftest'; exit 1 }

    Write-Output 'PASS pptx-delivery (checker selftests C5/C7; full suite: python tests/run_tests.py)'
    exit 0
} finally {
    Pop-Location
}
