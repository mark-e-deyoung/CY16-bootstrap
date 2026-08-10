$ErrorActionPreference = 'Stop'

$py = Get-Command py -ErrorAction SilentlyContinue
if ($py) {
    & py -3 "$PSScriptRoot\dev.py" bootstrap @args
    exit $LASTEXITCODE
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Error "Python 3 is required. Install Python and rerun this command."
    exit 2
}

& python "$PSScriptRoot\dev.py" bootstrap @args
exit $LASTEXITCODE
