# Bank Accounting System - PowerShell Portable Launcher
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

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "[1/3] Creating virtual environment..." -ForegroundColor White
    python -m venv .venv
    & ".\.venv\Scripts\pip.exe" install -r requirements.txt
}

Write-Host "`nLaunching server on: http://127.0.0.1:5000" -ForegroundColor Green
Write-Host "Logins:" -ForegroundColor White
Write-Host "  - Accountant: accountant01 / password123" -ForegroundColor Yellow
Write-Host "  - Admin:      admin / admin123" -ForegroundColor Yellow
Write-Host "`nOpening default browser..." -ForegroundColor Gray

Start-Process "http://127.0.0.1:5000"
& ".\.venv\Scripts\python.exe" app.py
