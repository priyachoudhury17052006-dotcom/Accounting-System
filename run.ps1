# Bank Accounting System - PowerShell Portable Launcher
Set-Location -Path $PSScriptRoot

Write-Host "==============================================================" -ForegroundColor Cyan
Write-Host "          BANK ACCOUNTING SYSTEM (TYBSC CS SEM V)" -ForegroundColor Yellow
Write-Host "             Portable Pen-Drive Edition - Plug & Play" -ForegroundColor Green
Write-Host "==============================================================" -ForegroundColor Cyan

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Python was not found in your PATH." -ForegroundColor Red
    Write-Host "Please install Python 3.9+ from https://www.python.org/downloads/"
    Read-Host "Press Enter to exit..."
    exit 1
}

$hasDeps = python -c "import flask, flask_sqlalchemy" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[1/2] Installing required dependencies..." -ForegroundColor White
    python -m pip install -r requirements.txt
}

Write-Host "`nLaunching server on: http://127.0.0.1:5000" -ForegroundColor Green
Write-Host "Logins:" -ForegroundColor White
Write-Host "  - Accountant: accountant01 / password123" -ForegroundColor Yellow
Write-Host "  - Admin:      admin / admin123" -ForegroundColor Yellow
Write-Host "`nOpening default browser..." -ForegroundColor Gray

Start-Process "http://127.0.0.1:5000"
python app.py
