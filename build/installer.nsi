; MT5 Signal System - Unified Installer
; 统一安装器 - 面板必选，主从二选一

!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "FileFunc.nsh"

; Change to project root directory
!cd ".."

; Set code page to UTF-8
Unicode true

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
Section "管理面板 (必需)" SecPanel
    SectionIn RO  ; 必选，不可取消
    
    ; 标记面板已安装
    StrCpy $EnablePanel "true"
SectionEnd

Section "Master 信号管理 (主服务器)" SecMaster
    ; 标记启用 Master
    StrCpy $EnableMaster "true"
    StrCpy $EnableSlave "false"  ; 互斥：选择 Master 则禁用 Slave
SectionEnd

Section "Slave 信号管理 (从服务器)" SecSlave
    ; 标记启用 Slave
    StrCpy $EnableSlave "true"
    StrCpy $EnableMaster "false"  ; 互斥：选择 Slave 则禁用 Master
SectionEnd

Section "系统说明文档" SecDeps
    ; 始终安装
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

; 生成安装配置文件并复制文件
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

    ; 始终复制面板程序
    File "dist\MT5_Manager.exe"
    File "dist\icon.ico"

    ; 根据选择复制 Master 或 Slave
    StrCmp $EnableMaster "true" master_section slave_check
    
    master_section:
        File "dist\MT5_Master.exe"
        Goto copy_done
    
    slave_check:
    StrCmp $EnableSlave "true" slave_section copy_done
    
    slave_section:
        File "dist\MT5_Slave.exe"
        Goto copy_done
    
    copy_done:

    ; 创建系统说明
    FileOpen $0 "$INSTDIR\系统说明.txt" w
    FileWrite $0 "========================================$\r$\n"
    FileWrite $0 "MT5 Signal System - 系统说明$\r$\n"
    FileWrite $0 "========================================$\r$\n"
    FileWrite $0 "$\r$\n"
    FileWrite $0 "本系统已编译为独立的 Windows 可执行文件，$\r$\n"
    FileWrite $0 "无需安装 Python 环境！$\r$\n"
    FileWrite $0 "$\r$\n"
    FileWrite $0 "安装组件：$\r$\n"
    FileWrite $0 "✓ MT5_Manager.exe  : 管理面板（图形界面）$\r$\n"
    
    StrCmp $EnableMaster "true" 0 +2
    FileWrite $0 "✓ MT5_Master.exe   : Master 信号服务$\r$\n"
    
    StrCmp $EnableSlave "true" 0 +2
    FileWrite $0 "✓ MT5_Slave.exe    : Slave 信号服务$\r$\n"
    
    FileWrite $0 "$\r$\n"
    FileWrite $0 "使用方法：$\r$\n"
    FileWrite $0 "1. 双击 MT5_Manager.exe 启动管理面板$\r$\n"
    FileWrite $0 "2. 在面板中配置参数$\r$\n"
    FileWrite $0 "3. 点击'启动'按钮运行服务$\r$\n"
    FileWrite $0 "$\r$\n"
    FileWrite $0 "注意：如果使用交易功能，需要安装 MetaTrader 5 终端$\r$\n"
    FileClose $0

    ; 创建桌面快捷方式
    CreateShortCut "$DESKTOP\MT5 Manager.lnk" "$INSTDIR\MT5_Manager.exe" "" "$INSTDIR\icon.ico"
    
    ; 创建开始菜单
    CreateDirectory "$SMPROGRAMS\MT5 Signal System"
    CreateShortCut "$SMPROGRAMS\MT5 Signal System\MT5 Manager.lnk" "$INSTDIR\MT5_Manager.exe" "" "$INSTDIR\icon.ico"
    CreateShortCut "$SMPROGRAMS\MT5 Signal System\系统说明.lnk" "$INSTDIR\系统说明.txt"
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
    Delete "$INSTDIR\MT5_Master.exe"
    Delete "$INSTDIR\MT5_Slave.exe"
    Delete "$INSTDIR\icon.ico"
    Delete "$INSTDIR\install_config.json"
    Delete "$INSTDIR\系统说明.txt"
    Delete "$INSTDIR\README.md"
    Delete "$INSTDIR\QUICKSTART.md"
    Delete "$INSTDIR\uninstall.exe"

    ; 删除快捷方式
    Delete "$DESKTOP\MT5 Manager.lnk"
    Delete "$SMPROGRAMS\MT5 Signal System\MT5 Manager.lnk"
    Delete "$SMPROGRAMS\MT5 Signal System\系统说明.lnk"
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
    !insertmacro MUI_DESCRIPTION_TEXT ${SecPanel} "管理面板 - 用于配置和监控（必需）"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecMaster} "Master 信号管理 - 作为主服务器发送交易信号（与 Slave 二选一）"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecSlave} "Slave 信号管理 - 作为从服务器接收并执行交易（与 Master 二选一）"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecDeps} "系统说明文档"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecConfig} "配置文件模板和示例"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecDocs} "用户手册和快速入门指南"
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; 自定义函数 - 实现 Master/Slave 互斥
Function .onSelChange
    ; 如果选择了 Master，取消 Slave
    SectionGetFlags ${SecMaster} $R0
    IntOp $R0 $R0 & ${SF_SELECTED}
    IntCmp $R0 ${SF_SELECTED} 0 check_slave
    
    ; Master 被选中，取消 Slave
    SectionSetFlags ${SecSlave} 0
    Goto done
    
    check_slave:
    ; 如果选择了 Slave，取消 Master
    SectionGetFlags ${SecSlave} $R0
    IntOp $R0 $R0 & ${SF_SELECTED}
    IntCmp $R0 ${SF_SELECTED} 0 done
    
    ; Slave 被选中，取消 Master
    SectionSetFlags ${SecMaster} 0
    
    done:
FunctionEnd

Function .onInit
    ; 初始化变量
    StrCpy $EnableMaster "false"
    StrCpy $EnableSlave "false"
    StrCpy $EnablePanel "true"
    
    ; 设置默认选择
    SectionSetFlags ${SecPanel} ${SF_SELECTED}    ; 面板必选
    SectionSetFlags ${SecMaster} ${SF_SELECTED}   ; 默认选择 Master
    SectionSetFlags ${SecSlave} 0                  ; Slave 未选
    SectionSetFlags ${SecDeps} ${SF_SELECTED}
FunctionEnd

Function un.onInit
    MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 "确定要完全卸载 MT5 Signal System 吗？" IDYES +2
    Abort
FunctionEnd