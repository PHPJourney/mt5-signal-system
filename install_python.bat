@echo off
chcp 65001 >nul
title MT5 Signal System - Python 环境安装器
color 0B

echo.
echo ========================================
echo   MT5 Signal System - Python 环境安装
echo ========================================
echo.

REM 检查 Python 是否已安装
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [✓] Python 已安装
    python --version
    echo.
    set /p confirm="Python 已存在，是否重新安装？(y/N): "
    if /i not "%confirm%"=="y" (
        echo [跳过] 保持现有 Python 环境
        goto install_deps
    )
)

echo [信息] 正在下载 Python 3.11...
echo.

REM 创建临时目录
set TEMP_DIR=%TEMP%\mt5_python_install
mkdir "%TEMP_DIR%" 2>nul

REM Python 3.11.9 嵌入式版本（便携版，无需安装）
set PYTHON_URL=https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip
set PYTHON_ZIP=%TEMP_DIR%\python-3.11.9-embed-amd64.zip

echo [下载] 正在从官方源下载 Python 嵌入式版本...
echo         这可能需要几分钟时间，请耐心等待...
echo.

REM 使用 PowerShell 下载
powershell -Command "& { ^
    $ProgressPreference = 'SilentlyContinue'; ^
    Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%PYTHON_ZIP%'; ^
    if ($?) { ^
        Write-Host '[✓] 下载完成' -ForegroundColor Green; ^
        exit 0; ^
    } else { ^
        Write-Host '[✗] 下载失败' -ForegroundColor Red; ^
        exit 1; ^
    } ^
}"

if %errorlevel% neq 0 (
    echo.
    echo [错误] 下载失败！请检查网络连接后重试
    echo 或者手动下载: %PYTHON_URL%
    echo 然后解压到本目录的 python_runtime 文件夹
    echo.
    pause
    exit /b 1
)

echo.
echo [解压] 正在解压 Python 运行时...

REM 解压到 python_runtime 目录
set PYTHON_RUNTIME=%~dp0python_runtime
mkdir "%PYTHON_RUNTIME%" 2>nul

powershell -Command "& { ^
    Expand-Archive -Path '%PYTHON_ZIP%' -DestinationPath '%PYTHON_RUNTIME%' -Force; ^
    if ($?) { ^
        Write-Host '[✓] 解压完成' -ForegroundColor Green; ^
        exit 0; ^
    } else { ^
        Write-Host '[✗] 解压失败' -ForegroundColor Red; ^
        exit 1; ^
    } ^
}"

if %errorlevel% neq 0 (
    echo [错误] 解压失败！
    pause
    exit /b 1
)

REM 启用 pip（嵌入式 Python 默认禁用了 pip）
echo.
echo [配置] 正在启用 pip 包管理器...
(
    echo import site
    echo site.main()
) >> "%PYTHON_RUNTIME%\python311._pth"

REM 清理临时文件
del "%PYTHON_ZIP%" 2>nul
rmdir "%TEMP_DIR%" 2>nul

echo.
echo [✓] Python 运行时安装完成！
echo     路径: %PYTHON_RUNTIME%
echo.

:install_deps
echo ========================================
echo   安装 Python 依赖包
echo ========================================
echo.

REM 使用嵌入式 Python 的 pip
set PYTHON_EXE=%PYTHON_RUNTIME%\python.exe
if not exist "%PYTHON_EXE%" (
    REM 尝试系统 Python
    set PYTHON_EXE=python
)

echo [安装] 正在安装必需的依赖包...
echo 这可能需要几分钟时间...
echo.

"%PYTHON_EXE%" -m pip install --upgrade pip
"%PYTHON_EXE%" -m pip install paho-mqtt
"%PYTHON_EXE%" -m pip install numpy
"%PYTHON_EXE%" -m pip install psutil
"%PYTHON_EXE%" -m pip install MetaTrader5

if %errorlevel% equ 0 (
    echo.
    echo [✓] 所有依赖包安装完成！
) else (
    echo.
    echo [警告] 部分依赖包安装失败
    echo 如果 MetaTrader5 安装失败，请确保已安装 MT5 客户端
    echo 其他功能仍可正常使用
)

echo.
echo ========================================
echo   安装完成！
echo ========================================
echo.
echo 您现在可以：
echo   1. 双击 start_manager.bat 启动管理面板
echo   2. 双击 start_master.bat 启动主服务器
echo   3. 双击 start_slave.bat 启动从服务器
echo.
pause
