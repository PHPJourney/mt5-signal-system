@echo off
chcp 65001 >nul
title MT5 Signal System - Install MQTT Broker
color 0D

echo.
echo ========================================
echo   Install MQTT Broker (Mosquitto)
echo ========================================
echo.
echo This will download and install Mosquitto MQTT Broker.
echo.

REM Check if already installed
where mosquitto >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Mosquitto is already installed
    mosquitto -h | findstr "version"
    echo.
    set /p choice="Do you want to reinstall? (Y/N): "
    if /i not "%choice%"=="Y" exit /b 0
)

echo Downloading Mosquitto installer...
echo.

REM Download latest version
powershell -Command "& {Invoke-WebRequest -Uri 'https://github.com/eclipse/mosquitto/releases/download/v2.0.18/mosquitto-2.0.18-install-windows-x64.exe' -OutFile 'mosquitto-installer.exe'}"

if not exist "mosquitto-installer.exe" (
    echo [ERROR] Download failed
    echo Please download manually from: https://mosquitto.org/download/
    pause
    exit /b 1
)

echo.
echo Starting installer...
echo Please follow the installation wizard.
echo Make sure to check "Add to PATH" option.
echo.

start /wait mosquitto-installer.exe

REM Cleanup
del mosquitto-installer.exe

echo.
echo ========================================
echo Installation completed!
echo ========================================
echo.
echo To start Mosquitto service:
echo   net start mosquitto
echo.
echo Or run manually:
echo   mosquitto -v
echo.
pause
