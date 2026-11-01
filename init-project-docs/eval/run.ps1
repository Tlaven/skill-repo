# init-project-docs 验收入口 —— 跑 skill 侧单元测试。
# 约定(skills-eval.ps1):退出码 0 = PASS。
# 覆盖:检查器行为(含反向用例)、N2 发现、2A 最小项目首跑必须绿。
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent

Push-Location $root
try {
    # 用 cmd 合并 stdout/stderr:PS 5.1 把原生 stderr 直接重定向会抛 NativeCommandError。
    $out = & cmd /c "python -m unittest discover -s tests -q 2>&1"
    $code = $LASTEXITCODE
} finally {
    Pop-Location
}

if ($code -ne 0) {
    Write-Output ("FAIL unit tests (exit " + $code + ")")
    Write-Output ($out | Out-String)
    exit 1
}

Write-Output ("PASS init-project-docs unit tests: " + (($out | Out-String).Trim() -replace "`r?`n", " "))
exit 0
