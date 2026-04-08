@echo off
REM Windows Build Script for Elite Job Agent
REM Builds .exe and Windows installer using NSIS
REM Usage: build_windows.bat

setlocal enabledelayedexpansion

set PROJECT_ROOT=%~dp0
set BUILD_DIR=%PROJECT_ROOT%build
set DIST_DIR=%PROJECT_ROOT%dist
set ASSETS_DIR=%PROJECT_ROOT%assets

set APP_NAME=Elite Job Agent
set APP_VERSION=1.0.0
set BUNDLE_ID=com.salman.elite-job-agent

echo.
echo ========================================
echo Building Elite Job Agent for Windows...
echo ========================================
echo.

REM Step 1: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.8+
    exit /b 1
)
echo ✅ Python found

REM Step 2: Install PyInstaller and Pillow if needed
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Installing PyInstaller...
    pip install pyinstaller
)
pip show pillow >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Installing Pillow...
    pip install pillow
)

REM Step 3: Create directories
if not exist "%ASSETS_DIR%" mkdir "%ASSETS_DIR%"
echo 📁 Directories created

REM Step 4: Check for icon or generate from logo.png
if not exist "%ASSETS_DIR%\app_icon.ico" (
    if exist "logo.png" (
        echo 🖼️ Generating app_icon.ico from logo.png...
        python -c "from pathlib import Path; from PIL import Image; logo=Path('logo.png'); icon=Path(r'%ASSETS_DIR%\\app_icon.ico'); img=Image.open(logo).convert('RGBA'); img.save(icon, format='ICO', sizes=[(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)])"
        if exist "%ASSETS_DIR%\app_icon.ico" (
            echo ✅ Generated icon from logo.png
        ) else (
            echo ⚠️  Failed to generate icon from logo.png
        )
    ) else (
        echo ⚠️  No app_icon.ico found in assets\
        echo    Convert PNG to ICO using: https://icoconvert.com/
    )
) else (
    echo ✅ Icon found
)

REM Step 5: Build with PyInstaller
echo.
echo 🔨 Building executable with PyInstaller...
python -m PyInstaller ^
    --name="Elite Job Agent" ^
    --windowed ^
    --onefile ^
    --icon="%ASSETS_DIR%\app_icon.ico" ^
    --add-data "requirements.txt;." ^
    --add-data "README.md;." ^
    --add-data ".gitignore;." ^
    main.py

if errorlevel 1 (
    echo ❌ Build failed!
    exit /b 1
)

echo ✅ Executable created

REM Step 6: Check if NullSoft Installer System is available
if exist "C:\Program Files (x86)\NSIS\makensis.exe" (
    echo 📦 Creating Windows installer...
    REM Note: NSIS script would go here (installer.nsi)
) else (
    echo ⚠️  NSIS not found. Using portable version.
    echo    To create installer: Download NSIS from https://nsis.sourceforge.io
)

REM Step 7: Verify build
if exist "%DIST_DIR%\Elite Job Agent.exe" (
    echo.
    echo ✅ Build completed successfully!
    echo.
    echo 📊 Build Summary:
    echo    - App Name: %APP_NAME%
    echo    - Version: %APP_VERSION%
    echo    - Location: %DIST_DIR%\Elite Job Agent.exe
    echo.
    echo 🚀 To run the app:
    echo    Double-click: %DIST_DIR%\Elite Job Agent.exe
    echo.
    echo 📦 To distribute:
    echo    Users simply download and run Elite Job Agent.exe
) else (
    echo ❌ Build failed!
    exit /b 1
)

pause
