param(
    [string]$ProjectRoot = "C:\Users\9400\.openclaw\workspace\twilio-review-mvp"
)

$ErrorActionPreference = 'Stop'
Set-Location $ProjectRoot

if (-not (Test-Path '.venv')) {
    python -m venv .venv
}

& .venv\Scripts\python.exe -m pip install -r requirements.txt

if (-not (Test-Path '.env') -and (Test-Path '.env.example')) {
    Copy-Item '.env.example' '.env'
}

& .venv\Scripts\python.exe -m app.init_db
Write-Host 'Bootstrap complete.'
