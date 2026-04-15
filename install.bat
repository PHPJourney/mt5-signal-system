@echo off
chcp 65001 >nul
title MT5 Signal System - Installation
color 0F

echo.
echo ========================================
echo   MT5 Signal System - Installation
echo ========================================
echo.
echo This script will install all required dependencies.
echo.

REM Check Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.7+ from: https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo [OK] Python found
python --version
echo.

REM Install dependencies
echo Installing dependencies...
echo.
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to install dependencies
    echo Please check your internet connection and try again.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Installation completed successfully!
echo ========================================
echo.
echo Next steps:
echo 1. Run config_panel.bat to configure the system
echo 2. Start master server with start_master.bat
echo 3. Start slave server with start_slave.bat
echo.
pause
