@echo off
chcp 65001 >nul
title MT5 Signal System - Quick Deploy
color 0A

setlocal enabledelayedexpansion

echo.
echo ===============================================
echo    MT5 Signal System - Quick Deployment Tool
echo ===============================================
echo.
echo This tool will help you set up the system step by step.
echo.

REM Step 1: Check Python
echo [Step 1/5] Checking Python installation...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed!
    echo.
    echo Please install Python 3.7+ from:
    echo https://www.python.org/downloads/
    echo.
    echo IMPORTANT: Check "Add Python to PATH" during installation
    echo.
    set /p open_python="Open download page? (Y/N): "
    if /i "!open_python!"=="Y" start https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [OK] Python found
python --version
echo.

REM Step 2: Install dependencies
echo [Step 2/5] Installing dependencies...
pip install -r requirements.txt >install_log.txt 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies
    echo Check install_log.txt for details
    pause
    exit /b 1
)
echo [OK] Dependencies installed
echo.

REM Step 3: Install Mosquitto
echo [Step 3/5] Checking MQTT Broker...
where mosquitto >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Mosquitto not found
    echo.
    set /p install_mosquitto="Install Mosquitto now? (Y/N): "
    if /i "!install_mosquitto!"=="Y" (
        call install_mosquitto.bat
    ) else (
        echo Please install Mosquitto manually later
        echo Download from: https://mosquitto.org/download/
    )
) else (
    echo [OK] Mosquitto found
)
echo.

REM Step 4: Configuration
echo [Step 4/5] Configuration...
echo.
echo You can configure the system now or skip and do it later.
set /p config_now="Open configuration panel now? (Y/N): "
if /i "!config_now!"=="Y" (
    start "" config_panel.py
    echo.
    echo Configuration panel opened.
    echo Please complete the configuration and close the panel.
    pause
)
echo.

REM Step 5: Start services
echo [Step 5/5] Starting services...
echo.
echo Choose which service to start:
echo   1. Master Server only
echo   2. Slave Server only
echo   3. Both servers
echo   4. Skip (start manually later)
echo.
set /p choice="Enter your choice (1-4): "

if "!choice!"=="1" (
    start "MT5 Master Server" cmd /k start_master.bat
    echo Master server started in new window
) else if "!choice!"=="2" (
    start "MT5 Slave Server" cmd /k start_slave.bat
    echo Slave server started in new window
) else if "!choice!"=="3" (
    start "MT5 Master Server" cmd /k start_master.bat
    timeout /t 2 /nobreak >nul
    start "MT5 Slave Server" cmd /k start_slave.bat
    echo Both servers started in separate windows
) else (
    echo Services not started
    echo You can start them manually using:
    echo   - start_master.bat (Master Server)
    echo   - start_slave.bat (Slave Server)
)

echo.
echo ===============================================
echo    Deployment Completed!
echo ===============================================
echo.
echo Important notes:
echo 1. Make sure MT5 terminal is logged in
echo 2. Check logs/ directory for detailed logs
echo 3. Use config_panel.bat to modify settings
echo.
echo For troubleshooting, see README.md
echo.
pause
