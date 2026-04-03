param(
    [string]$ProjectRoot = "C:\Users\9400\.openclaw\workspace\twilio-review-mvp",
    [int]$Port = 8000
)

$ErrorActionPreference = 'Stop'
Set-Location $ProjectRoot
& .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port $Port --reload
