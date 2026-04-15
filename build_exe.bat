@echo off
chcp 65001 >nul
title MT5 Signal System - Build Windows EXE
color 0E

echo.
echo ===============================================
echo   MT5 Signal System - Windows EXE Builder
echo ===============================================
echo.
echo This script will create standalone Windows executables.
echo.

REM Check Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo Please install Python 3.7+ for Windows
    pause
    exit /b 1
)

echo [OK] Python found
python --version
echo.

REM Install PyInstaller
echo Installing PyInstaller...
pip install pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install PyInstaller
    pause
    exit /b 1
)
echo [OK] PyInstaller installed
echo.

REM Clean previous builds
echo Cleaning previous builds...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "*.spec" del /q "*.spec"
echo [OK] Cleaned
echo.

REM Build Master Server EXE
echo ===============================================
echo Building Master Server EXE...
echo ===============================================
echo.

pyinstaller --name="MT5_Master_Server" ^
    --onedir ^
    --console ^
    --icon=NONE ^
    --add-data "config;config" ^
    --hidden-import=paho.mqtt.client ^
    --hidden-import=MetaTrader5 ^
    --hidden-import=common ^
    --hidden-import=common.models ^
    --hidden-import=common.utils ^
    --hidden-import=common.mqtt_client ^
    master\signal_sender.py

if %errorlevel% neq 0 (
    echo [ERROR] Failed to build Master Server
    pause
    exit /b 1
)

echo [OK] Master Server built successfully
echo.

REM Build Slave Server EXE
echo ===============================================
echo Building Slave Server EXE...
echo ===============================================
echo.

pyinstaller --name="MT5_Slave_Server" ^
    --onedir ^
    --console ^
    --icon=NONE ^
    --add-data "config;config" ^
    --hidden-import=paho.mqtt.client ^
    --hidden-import=MetaTrader5 ^
    --hidden-import=common ^
    --hidden-import=common.models ^
    --hidden-import=common.utils ^
    --hidden-import=common.mqtt_client ^
    --hidden-import=slave ^
    --hidden-import=slave.symbol_mapper ^
    --hidden-import=slave.risk_manager ^
    slave\signal_receiver.py

if %errorlevel% neq 0 (
    echo [ERROR] Failed to build Slave Server
    pause
    exit /b 1
)

echo [OK] Slave Server built successfully
echo.

REM Create release package
echo ===============================================
echo Creating Release Package...
echo ===============================================
echo.

set RELEASE_DIR=dist\MT5_Signal_System_Release
if exist "%RELEASE_DIR%" rmdir /s /q "%RELEASE_DIR%"
mkdir "%RELEASE_DIR%"

REM Copy executables
xcopy /E /I /Y "dist\MT5_Master_Server" "%RELEASE_DIR%\Master_Server"
xcopy /E /I /Y "dist\MT5_Slave_Server" "%RELEASE_DIR%\Slave_Server"

REM Copy config
xcopy /E /I /Y "config" "%RELEASE_DIR%\config"

REM Copy documentation
copy "README.md" "%RELEASE_DIR%\"
copy "WINDOWS_GUIDE.md" "%RELEASE_DIR%\"
copy "QUICKSTART.md" "%RELEASE_DIR%\"
copy "CHEATSHEET.md" "%RELEASE_DIR%\"

REM Create launch scripts
echo @echo off > "%RELEASE_DIR%\start_master.bat"
echo title MT5 Master Server >> "%RELEASE_DIR%\start_master.bat"
echo cd Master_Server >> "%RELEASE_DIR%\start_master.bat"
echo MT5_Master_Server.exe --config ..\config\master_config.json >> "%RELEASE_DIR%\start_master.bat"
echo pause >> "%RELEASE_DIR%\start_master.bat"

echo @echo off > "%RELEASE_DIR%\start_slave.bat"
echo title MT5 Slave Server >> "%RELEASE_DIR%\start_slave.bat"
echo cd Slave_Server >> "%RELEASE_DIR%\start_slave.bat"
echo MT5_Slave_Server.exe --config ..\config\slave_config.json >> "%RELEASE_DIR%\start_slave.bat"
echo pause >> "%RELEASE_DIR%\start_slave.bat"

echo @echo off > "%RELEASE_DIR%\config_panel.bat"
echo title Configuration Panel >> "%RELEASE_DIR%\config_panel.bat"
echo python ..\config_panel.py >> "%RELEASE_DIR%\config_panel.bat"
echo pause >> "%RELEASE_DIR%\config_panel.bat"

echo [OK] Release package created
echo.

REM Summary
echo ===============================================
echo   Build Completed Successfully!
echo ===============================================
echo.
echo Output directory: %cd%\%RELEASE_DIR%
echo.
echo Contents:
echo   - Master_Server/     (Master server executable)
echo   - Slave_Server/      (Slave server executable)
echo   - config/            (Configuration files)
echo   - start_master.bat   (Launch master server)
echo   - start_slave.bat    (Launch slave server)
echo   - Documentation files
echo.
echo Next steps:
echo 1. Test the executables
echo 2. Configure using config_panel.bat
echo 3. Distribute the release package
echo.

pause
