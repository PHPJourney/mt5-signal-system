; MT5 Signal System - Unified Installer
; 统一安装器 - 根据安装选择生成对应的配置文件

!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "FileFunc.nsh"

; General settings
Name "MT5 Signal System"
OutFile "dist\MT5_Signal_System_Installer.exe"
InstallDir "$PROGRAMFILES\MT5SignalSystem"
RequestExecutionLevel admin
ShowInstDetails show
ShowUninstDetails show

; UI settings
!define MUI_ABORTWARNING

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Language
!insertmacro MUI_LANGUAGE "SimpChinese"

; Variables
Var EnableMaster
Var EnableSlave

; 组件选择
Section "Master 信号管理 (主服务器)" SecMaster
    SectionIn RO
    SetOutPath "$INSTDIR"

    ; 复制主程序和图标
    File "dist\MT5_Manager\MT5_Manager.exe"
    File "dist\MT5_Manager\icon.ico"

    ; 标记启用 Master
    StrCpy $EnableMaster "true"
SectionEnd

Section "Slave 信号管理 (从服务器)" SecSlave
    SetOutPath "$INSTDIR"

    ; 标记启用 Slave
    StrCpy $EnableSlave "true"
SectionEnd

Section "Python 依赖安装工具" SecDeps
    SetOutPath "$INSTDIR"

    ; 创建依赖检查脚本
    FileOpen $0 "$INSTDIR\安装依赖.bat" w
    FileWrite $0 "@echo off$\r$\n"
    FileWrite $0 "chcp 65001 >nul$\r$\n"
    FileWrite $0 "echo ========================================$\r$\n"
    FileWrite $0 "echo MT5 Signal System - Python 环境检查$\r$\n"
    FileWrite $0 "echo ========================================$\r$\n"
    FileWrite $0 "echo.$\r$\n"
    FileWrite $0 "echo [1/3] 检查 Python 环境...$\r$\n"
    FileWrite $0 "echo.$\r$\n"
    FileWrite $0 "$\r$\n"
    FileWrite $0 "python --version >nul 2>&1$\r$\n"
    FileWrite $0 "if %errorlevel% neq 0 ($\r$\n"
    FileWrite $0 "    echo [错误] 未找到 Python 环境$\r$\n"
    FileWrite $0 "    echo.$\r$\n"
    FileWrite $0 "    echo 请按照以下步骤安装 Python:$\r$\n"
    FileWrite $0 "    echo 1. 访问 https://www.python.org/downloads/$\r$\n"
    FileWrite $0 "    echo 2. 下载 Python 3.11 或更高版本$\r$\n"
    FileWrite $0 "    echo 3. 安装时务必勾选 'Add Python to PATH'$\r$\n"
    FileWrite $0 "    echo 4. 重新运行此脚本$\r$\n"
    FileWrite $0 "    echo.$\r$\n"
    FileWrite $0 "    pause$\r$\n"
    FileWrite $0 "    exit /b 1$\r$\n"
    FileWrite $0 ")$\r$\n"
    FileWrite $0 "$\r$\n"
    FileWrite $0 "python --version$\r$\n"
    FileWrite $0 "echo ✓ Python 环境正常$\r$\n"
    FileWrite $0 "echo.$\r$\n"
    FileWrite $0 "$\r$\n"
    FileWrite $0 "echo [2/3] 升级 pip...$\r$\n"
    FileWrite $0 "echo.$\r$\n"
    FileWrite $0 "python -m pip install --upgrade pip$\r$\n"
    FileWrite $0 "echo.$\r$\n"
    FileWrite $0 "$\r$\n"
    FileWrite $0 "echo [3/3] 安装依赖包...$\r$\n"
    FileWrite $0 "echo.$\r$\n"
    FileWrite $0 "$\r$\n"
    FileWrite $0 "echo 正在安装必需包...$\r$\n"
    FileWrite $0 "python -m pip install paho-mqtt numpy psutil ttkbootstrap$\r$\n"
    FileWrite $0 "echo.$\r$\n"
    FileWrite $0 "$\r$\n"
    FileWrite $0 "echo 是否安装 MetaTrader5? (仅 Windows，需要 MT5 终端)$\r$\n"
    FileWrite $0 "echo 如果不需要交易功能，可以跳过$\r$\n"
    FileWrite $0 "echo.$\r$\n"
    FileWrite $0 "set /p install_mt5=安装 MetaTrader5? (y/n): $\r$\n"
    FileWrite $0 "if /i '%install_mt5%'=='y' ($\r$\n"
    FileWrite $0 "    echo.$\r$\n"
    FileWrite $0 "    echo 正在安装 MetaTrader5...$\r$\n"
    FileWrite $0 "    python -m pip install MetaTrader5$\r$\n"
    FileWrite $0 ") else ($\r$\n"
    FileWrite $0 "    echo 跳过 MetaTrader5 安装$\r$\n"
    FileWrite $0 ")$\r$\n"
    FileWrite $0 "$\r$\n"
    FileWrite $0 "echo.$\r$\n"
    FileWrite $0 "echo ========================================$\r$\n"
    FileWrite $0 "echo 依赖安装完成！$\r$\n"
    FileWrite $0 "echo ========================================$\r$\n"
    FileWrite $0 "echo.$\r$\n"
    FileWrite $0 "echo 现在可以双击桌面图标启动 MT5 Manager 了$\r$\n"
    FileWrite $0 "echo.$\r$\n"
    FileWrite $0 "pause$\r$\n"
    FileClose $0

    ; 创建依赖检查快捷方式
    CreateShortCut "$SMPROGRAMS\MT5 Signal System\安装依赖.lnk" "$INSTDIR\安装依赖.bat"
    CreateShortCut "$DESKTOP\安装依赖.lnk" "$INSTDIR\安装依赖.bat"
SectionEnd

Section "配置文件模板" SecConfig
    SetOutPath "$INSTDIR\config"

    IfFileExists "config\*.*" 0 +3
        File /r "config\*.*"
    Goto +2
        CreateDirectory "$INSTDIR\config"

    SetOutPath "$INSTDIR"
SectionEnd

Section "文档" SecDocs
    SetOutPath "$INSTDIR"

    IfFileExists "README.md" 0 +2
        File "README.md"
    IfFileExists "QUICKSTART.md" 0 +2
        File "QUICKSTART.md"
SectionEnd

; 生成安装配置文件
Section -Post
    SetOutPath "$INSTDIR"

    ; 生成 install_config.json
    FileOpen $0 "$INSTDIR\install_config.json" w
    FileWrite $0 "{$\r$\n"
    
    ; Master 配置
    StrCmp $EnableMaster "true" 0 +3
    FileWrite $0 '  "enable_master": true,$\r$\n'
    Goto +2
    FileWrite $0 '  "enable_master": false,$\r$\n'
    
    ; Slave 配置
    StrCmp $EnableSlave "true" 0 +3
    FileWrite $0 '  "enable_slave": true,$\r$\n'
    Goto +2
    FileWrite $0 '  "enable_slave": false$\r$\n'
    
    FileWrite $0 "}$\r$\n"
    FileClose $0

    ; 创建桌面快捷方式
    CreateShortCut "$DESKTOP\MT5 Manager.lnk" "$INSTDIR\MT5_Manager.exe" "" "$INSTDIR\icon.ico"
    
    ; 创建开始菜单
    CreateDirectory "$SMPROGRAMS\MT5 Signal System"
    CreateShortCut "$SMPROGRAMS\MT5 Signal System\MT5 Manager.lnk" "$INSTDIR\MT5_Manager.exe" "" "$INSTDIR\icon.ico"
    CreateShortCut "$SMPROGRAMS\MT5 Signal System\卸载.lnk" "$INSTDIR\uninstall.exe"

    ; 写入卸载信息
    WriteUninstaller "$INSTDIR\uninstall.exe"
    
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\MT5SignalSystem" \
                     "DisplayName" "MT5 Signal System"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\MT5SignalSystem" \
                     "UninstallString" "$INSTDIR\uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\MT5SignalSystem" \
                     "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\MT5SignalSystem" \
                     "DisplayIcon" "$INSTDIR\icon.ico"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\MT5SignalSystem" \
                     "Publisher" "MT5 Signal System"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\MT5SignalSystem" \
                     "DisplayVersion" "2.0"
    
    SetOutPath "$INSTDIR"
SectionEnd

; 卸载部分
Section "Uninstall"
    ; 删除文件
    Delete "$INSTDIR\MT5_Manager.exe"
    Delete "$INSTDIR\icon.ico"
    Delete "$INSTDIR\install_config.json"
    Delete "$INSTDIR\安装依赖.bat"
    Delete "$INSTDIR\README.md"
    Delete "$INSTDIR\QUICKSTART.md"
    Delete "$INSTDIR\uninstall.exe"

    ; 删除快捷方式
    Delete "$DESKTOP\MT5 Manager.lnk"
    Delete "$DESKTOP\安装依赖.lnk"
    Delete "$SMPROGRAMS\MT5 Signal System\MT5 Manager.lnk"
    Delete "$SMPROGRAMS\MT5 Signal System\安装依赖.lnk"
    Delete "$SMPROGRAMS\MT5 Signal System\卸载.lnk"

    ; 删除目录
    RMDir "$SMPROGRAMS\MT5 Signal System"
    RMDir /r "$INSTDIR\config"
    RMDir /r "$INSTDIR\logs"
    RMDir "$INSTDIR"

    ; 删除注册表
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\MT5SignalSystem"
SectionEnd

; 描述
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SecMaster} "Master 信号管理功能 - 作为主服务器发送交易信号"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecSlave} "Slave 信号管理功能 - 作为从服务器接收并执行交易"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecDeps} "Python 环境检查和依赖自动安装工具"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecConfig} "配置文件模板和示例"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecDocs} "用户手册和快速入门指南"
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; 自定义函数
Function .onInit
    ; 初始化变量
    StrCpy $EnableMaster "false"
    StrCpy $EnableSlave "false"
    
    ; 设置默认选择（两者都选）
    SectionSetFlags ${SecMaster} ${SF_SELECTED}
    SectionSetFlags ${SecSlave} ${SF_SELECTED}
    SectionSetFlags ${SecDeps} ${SF_SELECTED}
FunctionEnd

Function un.onInit
    MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 "确定要完全卸载 MT5 Signal System 吗？" IDYES +2
    Abort
FunctionEnd