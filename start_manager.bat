@echo off
chcp 65001 >nul
title MT5 Signal System - Manager
echo ========================================
echo   MT5 Signal System - Management Panel
echo ========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

echo [信息] 正在启动管理面板...
echo.

REM 安装依赖（如果需要）
pip show psutil >nul 2>&1
if errorlevel 1 (
    echo [安装] 正在安装依赖包 psutil...
    pip install psutil
)

REM 尝试安装 ttkbootstrap（美化主题）
pip show ttkbootstrap >nul 2>&1
if errorlevel 1 (
    echo [提示] ttkbootstrap 未安装，将使用默认主题
    echo [提示] 如需美化界面，请运行: pip install ttkbootstrap
)

echo.
python mt5_manager.py

pause
