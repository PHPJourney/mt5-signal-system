@echo off
chcp 65001 >nul
title MT5 Signal System - Slave Server
color 0B

echo.
echo ========================================
echo   MT5 Signal System - Slave Server
echo ========================================
echo.
echo 正在检查环境...
echo.

REM 获取脚本所在目录
set SCRIPT_DIR=%~dp0

REM 检查内置 Python 运行时
set PYTHON_RUNTIME=%SCRIPT_DIR%python_runtime
set PYTHON_EXE=%PYTHON_RUNTIME%\python.exe

if exist "%PYTHON_EXE%" (
    echo [✓] 使用内置 Python 运行时
    "%PYTHON_EXE%" --version
) else (
    REM 尝试使用系统 Python
    echo [!] 未找到内置 Python，尝试系统 Python...
    where python >nul 2>&1
    if %errorlevel% neq 0 (
        echo [错误] Python未安装
        echo.
        echo 请先安装 Python 3.8+: https://www.python.org/downloads/
        echo 或者双击 install_python.bat 自动安装
        pause
        exit /b 1
    )
    echo [✓] 使用系统 Python
    python --version
    set PYTHON_EXE=python
)

echo.

REM 检查配置文件
if not exist "%SCRIPT_DIR%config\slave_config.json" (
    echo [错误] 配置文件不存在: config\slave_config.json
    echo.
    echo 请先运行管理面板进行配置
    start "" "%SCRIPT_DIR%start_manager.bat"
    pause
    exit /b 1
)

echo [✓] 配置文件存在
echo.

REM 检查依赖
echo [检查] 正在验证依赖包...
"%PYTHON_EXE%" -c "import MetaTrader5" 2>nul
if %errorlevel% neq 0 (
    echo [警告] MetaTrader5 模块未安装
    echo [提示] 如果只需要测试信号功能，可以跳过
    echo.
) else (
    echo [✓] MetaTrader5 依赖已就绪
    echo.
)

echo ========================================
echo 启动从服务器...
echo ========================================
echo.
echo [提示] 按 Ctrl+C 停止服务器
echo.

"%PYTHON_EXE%" "%SCRIPT_DIR%slave\signal_receiver.py" --config "%SCRIPT_DIR%config\slave_config.json"

if %errorlevel% neq 0 (
    echo.
    echo [错误] 从服务器异常退出
    pause
)
