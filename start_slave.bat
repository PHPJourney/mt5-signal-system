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

REM 检查Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] Python未安装或未添加到PATH
    echo 请先安装Python 3.7+: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [✓] Python已安装
python --version
echo.

REM 检查配置文件
if not exist "config\slave_config.json" (
    echo [错误] 配置文件不存在: config\slave_config.json
    echo.
    echo 请先运行配置面板进行配置
    start config_panel.bat
    pause
    exit /b 1
)

echo [✓] 配置文件存在
echo.

REM 检查依赖
echo 正在检查依赖...
python -c "import MetaTrader5" 2>nul
if %errorlevel% neq 0 (
    echo [警告] MetaTrader5模块未安装
    echo 正在安装依赖...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
) else (
    echo [✓] 依赖检查通过
)

echo.
echo ========================================
echo 启动从服务器...
echo ========================================
echo.
echo 提示: 按 Ctrl+C 停止服务器
echo.

python slave\signal_receiver.py --config config\slave_config.json

if %errorlevel% neq 0 (
    echo.
    echo [错误] 从服务器异常退出
    pause
)
