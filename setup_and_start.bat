@echo off
chcp 65001 >nul
title MT5 Signal System - 一键启动
color 0E

echo.
echo ========================================
echo   MT5 Signal System - 一键启动
echo ========================================
echo.

REM 获取脚本所在目录
set SCRIPT_DIR=%~dp0
set PYTHON_RUNTIME=%SCRIPT_DIR%python_runtime
set PYTHON_EXE=%PYTHON_RUNTIME%\python.exe

REM 检查 Python 运行时是否存在
if not exist "%PYTHON_EXE%" (
    echo [!] 未找到内置 Python 运行时
    echo.
    echo 正在尝试使用系统 Python...
    python --version >nul 2>&1
    if %errorlevel% equ 0 (
        echo [✓] 找到系统 Python
        python --version
        set PYTHON_EXE=python
        goto check_deps
    ) else (
        echo [!] 系统也未安装 Python
        echo.
        set /p install="是否现在自动下载并安装 Python？(Y/n): "
        if /i "%install%"=="n" (
            echo.
            echo [取消] 已退出
            echo.
            echo 您可以手动安装 Python:
            echo   https://www.python.org/downloads/
            pause
            exit /b 1
        ) else (
            echo.
            echo 正在启动安装程序...
            start /wait "" "%SCRIPT_DIR%install_python.bat"
            echo.
            echo 安装完成！重新启动启动器...
            echo.
            REM 重新执行本脚本
            "%SCRIPT_DIR%setup_and_start.bat"
            exit /b 0
        )
    )
)

echo [✓] 找到内置 Python 运行时
"%PYTHON_EXE%" --version
echo.

:check_deps
echo ========================================
echo   检查依赖包
echo ========================================
echo.

REM 检查必需的依赖
set MISSING_DEPS=0

"%PYTHON_EXE%" -c "import paho.mqtt" 2>nul
if %errorlevel% neq 0 (
    echo [!] 缺少: paho-mqtt
    set MISSING_DEPS=1
)

"%PYTHON_EXE%" -c "import numpy" 2>nul
if %errorlevel% neq 0 (
    echo [!] 缺少: numpy
    set MISSING_DEPS=1
)

"%PYTHON_EXE%" -c "import psutil" 2>nul
if %errorlevel% neq 0 (
    echo [!] 缺少: psutil
    set MISSING_DEPS=1
)

if %MISSING_DEPS% equ 1 (
    echo.
    echo [安装] 正在安装缺失的依赖包...
    "%PYTHON_EXE%" -m pip install paho-mqtt numpy psutil MetaTrader5 --quiet
    if %errorlevel% equ 0 (
        echo [✓] 依赖包安装完成
    ) else (
        echo [!] 依赖包安装可能有误，但将继续启动
    )
    echo.
) else (
    echo [✓] 所有依赖包已就绪
    echo.
)

:show_menu
echo ========================================
echo   请选择要启动的服务
echo ========================================
echo.
echo   1. 启动管理面板 (UI)
echo   2. 启动 Master Server
echo   3. 启动 Slave Server
echo   4. 启动 Master + Slave
echo   5. 退出
echo.
set /p choice="请输入选项 (1-5): "

if "%choice%"=="1" goto start_manager
if "%choice%"=="2" goto start_master
if "%choice%"=="3" goto start_slave
if "%choice%"=="4" goto start_both
if "%choice%"=="5" goto exit
echo [!] 无效选项，请重新输入
echo.
goto show_menu

:start_manager
echo.
echo ========================================
echo   启动统一管理平台
echo ========================================
echo.
"%PYTHON_EXE%" "%SCRIPT_DIR%mt5_unified_manager.py"
goto exit

:start_master
echo.
echo ========================================
echo   启动 Master Server
echo ========================================
echo.
"%PYTHON_EXE%" "%SCRIPT_DIR%master\signal_sender.py" --config "%SCRIPT_DIR%config\master_config.json"
goto exit

:start_slave
echo.
echo ========================================
echo   启动 Slave Server
echo ========================================
echo.
"%PYTHON_EXE%" "%SCRIPT_DIR%slave\signal_receiver.py" --config "%SCRIPT_DIR%config\slave_config.json"
goto exit

:start_both
echo.
echo ========================================
echo   启动统一管理平台（推荐）
echo ========================================
echo.
echo [提示] 统一管理平台集成了所有功能
echo        Master/Slave 在面板内作为后台服务运行
echo.
start "MT5 Unified Manager" "%PYTHON_EXE%" "%SCRIPT_DIR%mt5_unified_manager.py"
echo [✓] 统一管理平台已启动
echo.
pause
goto exit

:exit
echo.
echo 感谢使用 MT5 Signal System！
echo.
pause
