@echo off
chcp 65001 >nul
title MT5 Signal System - 统一管理平台 v2.0
color 0E

echo.
echo ========================================
echo   MT5 Signal System - 统一管理平台 v2.0
echo ========================================
echo.
echo   所有功能集成在一个窗口中
echo   - Master/Slave 作为后台服务
echo   - 授权管理 / 配置 / 监控 / 日志
echo ========================================
echo.

REM Get script directory
set SCRIPT_DIR=%~dp0

REM Check built-in Python runtime
set PYTHON_RUNTIME=%SCRIPT_DIR%python_runtime
set PYTHON_EXE=%PYTHON_RUNTIME%\python.exe

if exist "%PYTHON_EXE%" (
    echo [✓] 使用内置 Python 运行时
    "%PYTHON_EXE%" --version
) else (
    echo [!] 未找到内置 Python，尝试系统 Python...
    python --version >nul 2>&1
    if %errorlevel% equ 0 (
        echo [✓] 使用系统 Python
        python --version
        set PYTHON_EXE=python
    ) else (
        echo [✗] Python 未安装
        echo.
        echo 请先运行 install_python.bat 安装 Python
        pause
        exit /b 1
    )
)

echo.
echo [启动] 统一管理平台...
echo.

"%PYTHON_EXE%" "%SCRIPT_DIR%mt5_unified_manager.py"

pause
