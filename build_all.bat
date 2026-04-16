@echo off
chcp 65001 >nul
REM ========================================
REM   MT5 Signal System - 一键打包脚本
REM   同时打包 Master 和 Slave
REM ========================================

echo.
echo ========================================
echo   MT5 Signal System - 一键打包工具
echo ========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

echo [信息] 检测到 Python:
python --version
echo.

REM 检查 PyInstaller
echo [检查] PyInstaller...
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo [安装] PyInstaller 未安装，正在安装...
    python -m pip install pyinstaller
    if errorlevel 1 (
        echo [错误] PyInstaller 安装失败
        pause
        exit /b 1
    )
) else (
    echo [OK] PyInstaller 已安装
)
echo.

REM 选择打包方式
echo 请选择打包方式:
echo 1. 仅创建便携版 (推荐，无需编译，跨平台)
echo 2. 创建 PyInstaller 可执行文件 (Windows 专用)
echo 3. 两者都创建 + NSIS 安装脚本
echo.
set /p choice="请输入选项 (1/2/3, 默认1): "
if "%choice%"=="" set choice=1
echo.

REM 创建必要目录
if not exist "build" mkdir build
if not exist "dist" mkdir dist

REM 根据选择执行打包
if "%choice%"=="1" goto PORTABLE_ONLY
if "%choice%"=="2" goto EXE_BUILD
if "%choice%"=="3" goto FULL_BUILD
goto INVALID_CHOICE

:PORTABLE_ONLY
echo.
echo ========================================
echo   创建便携版...
echo ========================================
call :CREATE_PORTABLE master
call :CREATE_PORTABLE slave
goto CREATE_README

:EXE_BUILD
echo.
echo ========================================
echo   构建 Master 可执行文件...
echo ========================================
python -m PyInstaller --clean build/master.spec
if errorlevel 1 (
    echo [警告] Master 构建失败，继续创建便携版
) else (
    echo [成功] Master 构建完成
)
call :CREATE_PORTABLE master

echo.
echo ========================================
echo   构建 Slave 可执行文件...
echo ========================================
python -m PyInstaller --clean build/slave.spec
if errorlevel 1 (
    echo [警告] Slave 构建失败，继续创建便携版
) else (
    echo [成功] Slave 构建完成
)
call :CREATE_PORTABLE slave
goto CREATE_README

:FULL_BUILD
echo.
echo ========================================
echo   构建 Master 可执行文件...
echo ========================================
python -m PyInstaller --clean build/master.spec
if errorlevel 1 (
    echo [警告] Master 构建失败
) else (
    echo [成功] Master 构建完成
)
call :CREATE_PORTABLE master
call :CREATE_NSIS master

echo.
echo ========================================
echo   构建 Slave 可执行文件...
echo ========================================
python -m PyInstaller --clean build/slave.spec
if errorlevel 1 (
    echo [警告] Slave 构建失败
) else (
    echo [成功] Slave 构建完成
)
call :CREATE_PORTABLE slave
call :CREATE_NSIS slave

echo.
echo ========================================
echo   NSIS 安装程序编译说明
echo ========================================
echo.
echo 如需编译 NSIS 安装程序，请运行:
echo   makensis build\master_installer.nsi
echo   makensis build\slave_installer.nsi
echo.
echo NSIS 下载地址: https://nsis.sourceforge.io/Download
echo.
goto CREATE_README

:CREATE_PORTABLE
set COMPONENT=%1
echo.
echo 创建 %COMPONENT% 便携版...

REM 清理旧目录
if exist "dist\MT5_%COMPONENT:_=_%_Portable" rmdir /s /q "dist\MT5_%COMPONENT:_=_%_Portable"
mkdir "dist\MT5_%COMPONENT:_=_%_Portable"

REM 复制文件
xcopy /E /I /Y "common" "dist\MT5_%COMPONENT:_=_%_Portable\common" >nul
xcopy /E /I /Y "%COMPONENT%" "dist\MT5_%COMPONENT:_=_%_Portable\%COMPONENT%" >nul
if not exist "dist\MT5_%COMPONENT:_=_%_Portable\config" mkdir "dist\MT5_%COMPONENT:_=_%_Portable\config"
copy "config\%COMPONENT%_config.json" "dist\MT5_%COMPONENT:_=_%_Portable\config\" >nul 2>&1

REM 复制语言文件
if exist "lang" (
    if not exist "dist\MT5_%COMPONENT:_=_%_Portable\lang" mkdir "dist\MT5_%COMPONENT:_=_%_Portable\lang"
    xcopy /E /I /Y "lang\*.json" "dist\MT5_%COMPONENT:_=_%_Portable\lang\" >nul 2>&1
)

copy "README.md" "dist\MT5_%COMPONENT:_=_%_Portable\" >nul 2>&1
copy "requirements.txt" "dist\MT5_%COMPONENT:_=_%_Portable\" >nul 2>&1

REM 创建启动脚本
if "%COMPONENT%"=="master" (
    set SCRIPT_NAME=signal_sender
) else (
    set SCRIPT_NAME=signal_receiver
)

(
echo @echo off
echo chcp 65001 ^>nul
echo title MT5 %COMPONENT:_=^ % Server
echo echo ========================================
echo echo   MT5 Signal System - %COMPONENT:_=^ % Server
echo echo ========================================
echo echo.
echo.
echo if not exist "config\\%COMPONENT%_config.json" ^(
echo     echo ERROR: Config file not found: config\\%COMPONENT%_config.json
echo     pause
echo     exit /b 1
echo ^)
echo.
echo echo Starting %COMPONENT:_=^ % Server...
echo echo.
echo.
echo python %COMPONENT%\\%SCRIPT_NAME%.py --config config\\%COMPONENT%_config.json
echo.
echo pause
) > "dist\MT5_%COMPONENT:_=_%_Portable\start_%COMPONENT%.bat"

REM 创建使用说明
(
echo MT5 %COMPONENT:_=^ % Server - 便携版
echo ================================
echo.
echo 使用方法:
echo 1. 确保已安装 Python 3.8+
echo 2. 安装依赖: pip install -r requirements.txt
echo 3. 编辑 config/%COMPONENT%_config.json 配置参数
echo 4. 双击 start_%COMPONENT%.bat 启动服务
echo.
echo 配置文件:
echo - config/%COMPONENT%_config.json: %COMPONENT:_=^ % 服务器配置
echo.
echo 日志文件:
echo - logs/%COMPONENT%.log: 运行日志
echo.
echo 技术支持:
echo 如有问题请查看 README.md
) > "dist\MT5_%COMPONENT:_=_%_Portable\使用说明.txt"

echo [成功] %COMPONENT:_=^ % 便携版已创建
goto :EOF

:CREATE_NSIS
set COMPONENT=%1
echo.
echo 创建 %COMPONENT:_=^ % NSIS 安装脚本...

(
echo ; MT5 %COMPONENT:_=^ % Server Installer Script
echo !include "MUI2.nsh"
echo.
echo Name "MT5 %COMPONENT:_=^ % Server"
echo OutFile "dist\MT5_%COMPONENT:_=_%_Server_Installer.exe"
echo InstallDir "$PROGRAMFILES\\MT5%COMPONENT:_=^ %Server"
echo RequestExecutionLevel admin
echo.
echo !define MUI_ABORTWARNING
echo !define MUI_ICON ""
echo !define MUI_UNICON ""
echo.
echo Page directory
echo Page instfiles
echo UninstPage uninstConfirm
echo UninstPage instfiles
echo.
echo !insertmacro MUI_LANGUAGE "SimpChinese"
echo.
echo Section "MainSection" SEC01
echo     SetOutPath "$INSTDIR"
echo.
echo     ; 复制所有文件
echo     File /r "dist\MT5_%COMPONENT:_=_%_Portable\*.*"
echo.
echo     ; 创建开始菜单快捷方式
echo     CreateDirectory "$SMPROGRAMS\\MT5 %COMPONENT:_=^ % Server"
echo     CreateShortCut "$SMPROGRAMS\\MT5 %COMPONENT:_=^ % Server\\%COMPONENT:_=^ % Server.lnk" "$INSTDIR\\start_%COMPONENT%.bat"
echo     CreateShortCut "$SMPROGRAMS\\MT5 %COMPONENT:_=^ % Server\\卸载.lnk" "$INSTDIR\\uninstall.exe"
echo.
echo     ; 创建桌面快捷方式
echo     CreateShortCut "$DESKTOP\\MT5 %COMPONENT:_=^ % Server.lnk" "$INSTDIR\\start_%COMPONENT%.bat"
echo.
echo     ; 写入注册表
echo     WriteUninstaller "$INSTDIR\\uninstall.exe"
echo     WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\MT5%COMPONENT:_=^ %Server" "DisplayName" "MT5 %COMPONENT:_=^ % Server"
echo     WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\MT5%COMPONENT:_=^ %Server" "UninstallString" "$INSTDIR\\uninstall.exe"
echo     WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\MT5%COMPONENT:_=^ %Server" "DisplayIcon" "$INSTDIR\\start_%COMPONENT%.bat"
echo     WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\MT5%COMPONENT:_=^ %Server" "Publisher" "MT5 Signal System"
echo SectionEnd
echo.
echo Section "Uninstall"
echo     RMDir /r "$INSTDIR"
echo     RMDir /r "$SMPROGRAMS\\MT5 %COMPONENT:_=^ % Server"
echo     Delete "$DESKTOP\\MT5 %COMPONENT:_=^ % Server.lnk"
echo     DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\MT5%COMPONENT:_=^ %Server"
echo SectionEnd
) > "build\%COMPONENT%_installer.nsi"

echo [成功] %COMPONENT:_=^ % NSIS 安装脚本已创建
goto :EOF

:CREATE_README
echo.
echo 创建发布说明...

(
echo MT5 Signal System - 发布包说明
echo ================================
echo.
echo 本目录包含 MT5 Signal System 的独立安装包：
echo.
echo 📦 可用版本
echo -----------
echo.
echo 1. MT5_Master_Portable/
echo    - Master Server 便携版
echo    - 无需安装，解压即用
echo    - 适合开发测试环境
echo.
echo 2. MT5_Slave_Portable/
echo    - Slave Server 便携版
echo    - 无需安装，解压即用
echo    - 适合开发测试环境
echo.
echo 3. MT5_Master_Server_Installer.exe (需要编译 NSIS)
echo    - Master Server 安装程序
echo    - 自动创建快捷方式
echo    - 支持标准 Windows 卸载
echo.
echo 4. MT5_Slave_Server_Installer.exe (需要编译 NSIS)
echo    - Slave Server 安装程序
echo    - 自动创建快捷方式
echo    - 支持标准 Windows 卸载
echo.
echo 🚀 快速开始
echo -----------
echo.
echo 便携版使用步骤:
echo 1. 解压到目标目录
echo 2. 确保已安装 Python 3.8+
echo 3. 安装依赖: pip install -r requirements.txt
echo 4. 编辑配置文件 (config/*.json)
echo 5. 双击 start_*.bat 启动服务
echo.
echo 安装版使用步骤:
echo 1. 双击 Installer.exe
echo 2. 选择安装路径
echo 3. 完成安装后从开始菜单或桌面启动
echo.
echo ⚙️ 配置说明
echo -----------
echo.
echo Master 配置: config/master_config.json
echo - MQTT Broker 地址
echo - Master MT5 账户信息
echo - 信号发送参数
echo.
echo Slave 配置: config/slave_config.json
echo - MQTT Broker 地址
echo - Slave MT5 账户信息
echo - 订阅的 Master ID
echo - 风险管理参数
echo.
echo 📝 注意事项
echo -----------
echo.
echo 1. Master 和 Slave 可以部署在不同机器上
echo 2. 确保 MQTT Broker 可访问
echo 3. 首次运行前必须配置正确的 MT5 账户
echo 4. 建议先测试便携版，确认无误后再使用安装版
echo.
echo 🔧 技术支持
echo -----------
echo.
echo 详细文档请查看项目根目录的:
echo - README.md
echo - QUICKSTART.md
echo - ARCHITECTURE.md
echo.
echo 如遇问题请查看日志文件: logs/*.log
) > "dist\发布说明.txt"

echo [成功] 发布说明已创建
goto FINISH

:INVALID_CHOICE
echo [错误] 无效选项
pause
exit /b 1

:FINISH
echo.
echo ========================================
echo   打包完成!
echo ========================================
echo.
echo 发布目录: %cd%\dist
echo.
echo 生成的文件:
dir /b dist
echo.
echo 下一步:
echo 1. 测试生成的程序
echo 2. 分发 portable 版本或编译 installer
echo 3. 查看 dist\发布说明.txt 了解详细信息
echo.
pause
