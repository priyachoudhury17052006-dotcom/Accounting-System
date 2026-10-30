#!/usr/bin/env bash
echo "=============================================================="
echo "          BANK ACCOUNTING SYSTEM (TYBSC CS SEM V)"
echo "             Portable Pen-Drive Edition - Plug & Play"
echo "=============================================================="

if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 could not be found. Please install Python 3.9+."
    exit 1
fi

if [ ! -d ".venv" ]; then
    echo "[1/2] Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

echo "Starting server at http://127.0.0.1:5000"
python3 app.py
