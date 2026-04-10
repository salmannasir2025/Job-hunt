@echo off
setlocal

set PROJECT_ROOT=%~dp0
cd /d "%PROJECT_ROOT%"

echo ========================================
echo Elite Job Agent - Windows Runner
echo ========================================

REM 1. Detect Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Python not found! Please install Python from https://python.org
    pause
    exit /b 1
)

REM 2. Setup Virtual Environment
set VENV_PATH=%PROJECT_ROOT%.venv_run
if not exist "%VENV_PATH%" (
    echo ✨ Creating new virtual environment...
    python -m venv "%VENV_PATH%"
)

REM Activate venv
call "%VENV_PATH%\Scripts\activate.bat"

REM 3. Install/Update Dependencies
echo 📚 Verifying dependencies...
python -m pip install --upgrade pip --quiet
python -m pip install --prefer-binary -r requirements.txt --quiet

REM 4. Run the Application
echo 🏁 Launching Elite Job Agent...
echo ----------------------------------------
python main.py
echo ----------------------------------------
echo ✅ Application closed.
pause
