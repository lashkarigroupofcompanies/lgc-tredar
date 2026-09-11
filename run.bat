@echo off
title AI QUANT FUND - AUTONOMOUS TRADING AGENT ARMY
color 0A
echo ================================================================
echo    LGC QUANT TRADING - 1-CLICK AUTONOMOUS MULTI-AGENT ENGINE
echo ================================================================
echo.
echo [*] Checking Python environment...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found in PATH! Please install Python 3.10 or 3.11.
    pause
    exit /b
)

if not exist .venv (
    echo [*] Creating virtual environment (.venv)...
    python -m venv .venv
)

echo [*] Activating virtual environment...
call .venv\Scripts\activate
set PYTHONDONTWRITEBYTECODE=1

echo [*] Checking and installing dependencies...
pip install -r requirements.txt

echo.
echo [*] Launching AI Agent Army & Dashboard...
start http://localhost:8000
python -B server.py

pause

