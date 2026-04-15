@echo off
chcp 65001 >nul
title MT5 Signal System - Installation Verification
color 0F

echo.
echo ===============================================
echo   MT5 Signal System - Installation Check
echo ===============================================
echo.

set ERRORS=0

REM Check Python
echo [1/7] Checking Python...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [FAIL] Python not found
    set /a ERRORS+=1
) else (
    echo [PASS] Python found
    python --version
)
echo.

REM Check pip
echo [2/7] Checking pip...
where pip >nul 2>&1
if %errorlevel% neq 0 (
    echo [FAIL] pip not found
    set /a ERRORS+=1
) else (
    echo [PASS] pip found
)
echo.

REM Check MetaTrader5
echo [3/7] Checking MetaTrader5 module...
python -c "import MetaTrader5" 2>nul
if %errorlevel% neq 0 (
    echo [FAIL] MetaTrader5 not installed
    echo        Run: install.bat
    set /a ERRORS+=1
) else (
    echo [PASS] MetaTrader5 installed
)
echo.

REM Check paho-mqtt
echo [4/7] Checking paho-mqtt module...
python -c "import paho.mqtt.client" 2>nul
if %errorlevel% neq 0 (
    echo [FAIL] paho-mqtt not installed
    echo        Run: install.bat
    set /a ERRORS+=1
) else (
    echo [PASS] paho-mqtt installed
)
echo.

REM Check Mosquitto
echo [5/7] Checking MQTT Broker...
where mosquitto >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] Mosquitto not found
    echo        Install from: https://mosquitto.org/download/
) else (
    echo [PASS] Mosquitto found
)
echo.

REM Check config files
echo [6/7] Checking configuration files...
if exist "config\master_config.json" (
    echo [PASS] master_config.json exists
) else (
    echo [FAIL] master_config.json missing
    set /a ERRORS+=1
)

if exist "config\slave_config.json" (
    echo [PASS] slave_config.json exists
) else (
    echo [FAIL] slave_config.json missing
    set /a ERRORS+=1
)
echo.

REM Check core modules
echo [7/7] Checking core modules...
set MODULES_OK=1

if not exist "common\models.py" set MODULES_OK=0
if not exist "common\mqtt_client.py" set MODULES_OK=0
if not exist "master\signal_sender.py" set MODULES_OK=0
if not exist "slave\signal_receiver.py" set MODULES_OK=0
if not exist "slave\symbol_mapper.py" set MODULES_OK=0
if not exist "slave\risk_manager.py" set MODULES_OK=0
if not exist "config_panel.py" set MODULES_OK=0

if %MODULES_OK% equ 1 (
    echo [PASS] All core modules present
) else (
    echo [FAIL] Some core modules missing
    set /a ERRORS+=1
)
echo.

REM Summary
echo ===============================================
if %ERRORS% equ 0 (
    echo   Result: ALL CHECKS PASSED ✓
    echo ===============================================
    echo.
    echo System is ready to use!
    echo.
    echo Next steps:
    echo 1. Start Mosquitto: net start mosquitto
    echo 2. Configure: config_panel.bat
    echo 3. Start master: start_master.bat
    echo 4. Start slave: start_slave.bat
) else (
    echo   Result: %ERRORS% CHECK(S) FAILED ✗
    echo ===============================================
    echo.
    echo Please fix the issues above.
    echo Run install.bat to install dependencies.
)
echo.

pause
