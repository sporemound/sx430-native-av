$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    python -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw 'Offline tests failed' }
    python tools/check_sources.py
    if ($LASTEXITCODE -ne 0) { throw 'Source integrity check failed' }
    Write-Output 'Research tools verified. No firmware image or native receiver was built.'
} finally {
    Pop-Location
}
