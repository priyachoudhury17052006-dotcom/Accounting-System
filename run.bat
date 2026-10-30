@echo off
setlocal
cd /d "%~dp0"
title Bank Accounting System - Priya Choudhury
color 0B

echo ==============================================================
echo           BANK ACCOUNTING SYSTEM (TYBSC CS SEM V)
echo              Portable Pen-Drive Edition - Plug & Play
echo ==============================================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your system PATH!
    echo Please install Python 3.9+ from https://www.python.org/downloads/
    echo Make sure to check "Add python.exe to PATH" during installation.
    pause
    exit /b 1
)

python -c "import flask, flask_sqlalchemy" >nul 2>nul
if %errorlevel% neq 0 (
    echo [1/2] Installing required dependencies (Flask, SQLAlchemy)...
    python -m pip install -r requirements.txt
)

echo.
echo ==============================================================
echo Server is launching on: http://127.0.0.1:5000
echo Default Logins:
echo   - Accountant: accountant01 / password123
echo   - Admin:      admin / admin123
echo Press Ctrl+C in this terminal to stop the application.
echo ==============================================================
echo.

start "" "http://127.0.0.1:5000"
python app.py
pause
