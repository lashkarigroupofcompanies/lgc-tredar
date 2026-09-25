@echo off
setlocal enabledelayedexpansion

echo ==========================================================
echo        LGC TRADER - STANDALONE APP COMPILER
echo           Automated Windows .exe Generator
echo ==========================================================
echo.

echo [1/4] Checking Python and Node environments...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found in PATH. Please install Python 3.10+
    pause
    exit /b 1
)

node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found in PATH. Please install Node.js 18+
    pause
    exit /b 1
)

echo [2/4] Compiling Dark Tactical Web UI...
cd ui
call npx vite build --config vite.lgc.config.ts
if %errorlevel% neq 0 (
    echo [WARNING] Vite build had warnings, continuing with existing static assets...
)
cd ..

echo.
echo [3/4] Ensuring PyInstaller and PyWebView are installed...
python -m pip install --quiet pyinstaller pywebview

echo.
echo [4/4] Packaging Standalone Windows Application (LGCTrader.exe)...
pyinstaller --noconfirm --onefile --windowed ^
    --name "LGCTrader" ^
    --add-data "ui/dist;ui/dist" ^
    --add-data "agents;agents" ^
    --add-data "shared_brain;shared_brain" ^
    --add-data "version.py;." ^
    --exclude-module "torch" ^
    --exclude-module "matplotlib" ^
    --exclude-module "scipy" ^
    --exclude-module "IPython" ^
    --exclude-module "jupyter" ^
    --hidden-import "uvicorn" ^
    --hidden-import "fastapi" ^
    --hidden-import "pydantic" ^
    --hidden-import "requests" ^
    --hidden-import "webview" ^
    desktop_app.py

if %errorlevel% equ 0 (
    echo.
    echo ==========================================================
    echo [SUCCESS] LGCTrader.exe successfully created!
    echo Location: %~dp0dist\LGCTrader.exe
    echo.
    echo You can move LGCTrader.exe anywhere and run it with 1-click!
    echo ==========================================================
) else (
    echo.
    echo [ERROR] PyInstaller compilation failed. See logs above.
)

pause
