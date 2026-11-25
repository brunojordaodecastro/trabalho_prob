$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$pythonMercado = Get-Command python -ErrorAction SilentlyContinue
$runtimeMercado = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (Test-Path -LiteralPath $runtimeMercado) {
    & $runtimeMercado 'server.py'
} elseif ($pythonMercado) {
    & $pythonMercado.Source 'server.py'
} else {
    throw 'Python 3.10 ou superior não encontrado. Instale Python ou execute usando seu interpretador existente.'
}
