@echo off
chcp 65001 >nul
:: MT5 Signal System - Windows Installation Script
:: Supports selecting Master, Slave, or Unified components

setlocal enabledelayedexpansion

echo ============================================
echo   MT5 Signal System - Installer
echo ============================================
echo.

set "INSTALL_DIR=%PROGRAMFILES%\MT5SignalSystem"

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [Warning] Running without admin rights
    set "INSTALL_DIR=%USERPROFILE%\Applications\MT5SignalSystem"
)

set /p "user_dir=Installation directory [%INSTALL_DIR%]: "
if defined user_dir set "INSTALL_DIR=%user_dir%"

if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

echo.
echo Select components to install:
echo   1^) Master Panel
echo   2^) Slave Panel
echo   3^) Unified Manager
echo   4^) All components
echo.

set /p "choice=Enter choice (1/2/3/4, default 4): "
if not defined choice set "choice=4"

set "SCRIPT_DIR=%~dp0"
set "DIST_DIR=%SCRIPT_DIR%dist"

if not exist "%DIST_DIR%" (
    echo [Error] dist directory not found. Please build first.
    pause
    exit /b 1
)

call :install_component "Master Panel" "%DIST_DIR%\MT5_Master_Panel.exe" "%INSTALL_DIR%\MT5_Master_Panel.exe"
call :install_component "Slave Panel" "%DIST_DIR%\MT5_Slave_Panel.exe" "%INSTALL_DIR%\MT5_Slave_Panel.exe"
call :install_component "Unified Manager" "%DIST_DIR%\MT5_Unified_Manager.exe" "%INSTALL_DIR%\MT5_Unified_Manager.exe"

if exist "%SCRIPT_DIR%config\" (
    if not exist "%INSTALL_DIR%\config\" mkdir "%INSTALL_DIR%\config"
    xcopy "%SCRIPT_DIR%config\*" "%INSTALL_DIR%\config\" /E /Y >nul 2>&1
    echo [OK] Installed: Configuration files
)

for %%f in (README.md QUICKSTART.md) do (
    if exist "%SCRIPT_DIR%%%f" (
        copy "%SCRIPT_DIR%%%f" "%INSTALL_DIR%\" >nul 2>&1
        echo [OK] Installed: %%f
    )
)

echo.
echo ============================================
echo Installation complete!
echo ============================================
echo.
echo Installed to: %INSTALL_DIR%
echo.

pause
exit /b 0

:install_component
set "name=%~1"
set "src=%~2"
set "dst=%~3"
if exist "%src%" (
    copy "%src%" "%dst%" >nul 2>&1
    echo [OK] Installed: %name%
) else (
    echo [SKIP] Not found: %name%
)
goto :eof
