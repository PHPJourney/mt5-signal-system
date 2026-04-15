@echo off
chcp 65001 >nul
title MT5 Signal System - Configuration Panel
color 0E

echo.
echo ========================================
echo   MT5 Configuration Panel
echo ========================================
echo.
echo 正在启动配置面板...
echo.

REM 检查Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] Python未安装或未添加到PATH
    echo 请先安装Python 3.7+: https://www.python.org/downloads/
    pause
    exit /b 1
)

python config_panel.py

if %errorlevel% neq 0 (
    echo.
    echo [错误] 配置面板启动失败
    pause
)
