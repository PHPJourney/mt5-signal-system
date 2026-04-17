@echo off
chcp 65001 >nul
title Build MT5 Manager Panel
color 0A

echo.
echo ===============================================
echo   Building MT5 Manager Panel (管理面板)
echo ===============================================
echo.

REM Check Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    pause
    exit /b 1
)

echo [OK] Python found
python --version
echo.

REM Install PyInstaller if needed
python -c "import PyInstaller" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

echo.
echo Building MT5_Manager.exe...
echo.

pyinstaller --name="MT5_Manager" ^
    --onedir ^
    --windowed ^
    --icon=dist\icon.ico ^
    --add-data "lang;lang" ^
    --add-data "ui;ui" ^
    --add-data "services;services" ^
    --hidden-import=tkinter ^
    --hidden-import=tkinter.ttk ^
    --hidden-import=requests ^
    --hidden-import=common ^
    --hidden-import=common.i18n ^
    --hidden-import=common.models ^
    --hidden-import=common.utils ^
    --hidden-import=common.account_reporter ^
    --hidden-import=services ^
    --hidden-import=services.mt5_detector ^
    --hidden-import=services.process_manager ^
    --hidden-import=services.config_manager ^
    --hidden-import=ui ^
    --hidden-import=ui.dashboard ^
    --hidden-import=ui.master_config ^
    --hidden-import=ui.slave_config ^
    --hidden-import=ui.monitoring ^
    --hidden-import=ui.logs ^
    mt5_manager.py

if %errorlevel% neq 0 (
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo [OK] MT5_Manager.exe built successfully!
echo Output: dist\MT5_Manager\
echo.

REM Copy icon to dist
if exist "dist\icon.ico" (
    copy "dist\icon.ico" "dist\MT5_Manager\" >nul
)

echo Done!
pause