; MT5 Signal System - Unified Installer
; 统一安装器 - 面板必选，主从至少选一个

!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "FileFunc.nsh"

; Change to project root directory
!cd ".."

; Set code page to UTF-8
Unicode true
!define MUI_LANGDLL_ALLLANGUAGES

; General settings
Name "MT5 Signal System"
OutFile "dist\MT5_Signal_System_Installer.exe"
InstallDir "$PROGRAMFILES\MT5SignalSystem"
RequestExecutionLevel admin
ShowInstDetails show
ShowUninstDetails show

; Version without git hash
!define VERSION "2.0.0"
VIProductVersion "${VERSION}.0"
VIAddVersionKey "ProductName" "MT5 Signal System"
VIAddVersionKey "FileVersion" "${VERSION}"
VIAddVersionKey "ProductVersion" "${VERSION}"
VIAddVersionKey "LegalCopyright" "MT5 Signal System"
VIAddVersionKey "FileDescription" "MT5 Trading Signal Management System"

; UI settings
!define MUI_ABORTWARNING
!define MUI_ICON "icon.ico"
!define MUI_UNICON "icon.ico"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Language
!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "SimpChinese"
!insertmacro MUI_RESERVEFILE_LANGDLL

; Variables
Var EnableMaster
Var EnableSlave

; 组件选择
Section "管理面板 (必需)" SecPanel
    SectionIn RO  ; 必选，不可取消
SectionEnd

Section "Master 信号管理 (主服务器)" SecMaster
    ; 标记启用 Master
    StrCpy $EnableMaster "true"
SectionEnd

Section "Slave 信号管理 (从服务器)" SecSlave
    ; 标记启用 Slave
    StrCpy $EnableSlave "true"
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

    ; 根据选择复制 Master
    StrCmp $EnableMaster "true" 0 +2
        File "dist\MT5_Master.exe"

    ; 根据选择复制 Slave
    StrCmp $EnableSlave "true" 0 +2
        File "dist\MT5_Slave.exe"

    ; 创建系统说明（使用 UTF-8 BOM）
    FileOpen $0 "$INSTDIR\system_readme.txt" w
    FileWriteUTF16LE $0 "========================================$\r$\n"
    FileWriteUTF16LE $0 "MT5 Signal System - System Instructions$\r$\n"
    FileWriteUTF16LE $0 "========================================$\r$\n"
    FileWriteUTF16LE $0 "$\r$\n"
    FileWriteUTF16LE $0 "This system is compiled as standalone Windows executables.$\r$\n"
    FileWriteUTF16LE $0 "No Python environment installation required!$\r$\n"
    FileWriteUTF16LE $0 "$\r$\n"
    FileWriteUTF16LE $0 "Installed components:$\r$\n"
    FileWriteUTF16LE $0 "MT5_Manager.exe  : Management Panel (GUI)$\r$\n"
    
    StrCmp $EnableMaster "true" 0 +2
    FileWriteUTF16LE $0 "MT5_Master.exe   : Master Signal Service$\r$\n"
    
    StrCmp $EnableSlave "true" 0 +2
    FileWriteUTF16LE $0 "MT5_Slave.exe    : Slave Signal Service$\r$\n"
    
    FileWriteUTF16LE $0 "$\r$\n"
    FileWriteUTF16LE $0 "Usage:$\r$\n"
    FileWriteUTF16LE $0 "1. Double-click MT5_Manager.exe to start the panel$\r$\n"
    FileWriteUTF16LE $0 "2. Configure parameters in the panel$\r$\n"
    FileWriteUTF16LE $0 "3. Click 'Start' button to run services$\r$\n"
    FileWriteUTF16LE $0 "$\r$\n"
    FileWriteUTF16LE $0 "Note: MetaTrader 5 terminal required for trading functions$\r$\n"
    FileClose $0

    ; 创建桌面快捷方式
    CreateShortCut "$DESKTOP\MT5 Manager.lnk" "$INSTDIR\MT5_Manager.exe" "" "$INSTDIR\icon.ico"
    
    ; 创建开始菜单
    CreateDirectory "$SMPROGRAMS\MT5 Signal System"
    CreateShortCut "$SMPROGRAMS\MT5 Signal System\MT5 Manager.lnk" "$INSTDIR\MT5_Manager.exe" "" "$INSTDIR\icon.ico"
    CreateShortCut "$SMPROGRAMS\MT5 Signal System\System Instructions.lnk" "$INSTDIR\system_readme.txt"
    CreateShortCut "$SMPROGRAMS\MT5 Signal System\Uninstall.lnk" "$INSTDIR\uninstall.exe"

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
                     "DisplayVersion" "${VERSION}"
    
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
    Delete "$INSTDIR\system_readme.txt"
    Delete "$INSTDIR\README.md"
    Delete "$INSTDIR\QUICKSTART.md"
    Delete "$INSTDIR\uninstall.exe"

    ; 删除快捷方式
    Delete "$DESKTOP\MT5 Manager.lnk"
    Delete "$SMPROGRAMS\MT5 Signal System\MT5 Manager.lnk"
    Delete "$SMPROGRAMS\MT5 Signal System\System Instructions.lnk"
    Delete "$SMPROGRAMS\MT5 Signal System\Uninstall.lnk"

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
    !insertmacro MUI_DESCRIPTION_TEXT ${SecPanel} "Management Panel - Configuration and Monitoring (Required)"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecMaster} "Master Signal Management - Send trading signals as master server"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecSlave} "Slave Signal Management - Receive and execute trades as slave server"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecDeps} "System instructions document"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecConfig} "Configuration file templates and examples"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecDocs} "User manual and quick start guide"
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; 自定义函数 - 验证至少选择一个
Function .onLeaveComponents
    ; 检查 Master 和 Slave 是否都未选
    SectionGetFlags ${SecMaster} $R0
    IntOp $R0 $R0 & ${SF_SELECTED}
    
    SectionGetFlags ${SecSlave} $R1
    IntOp $R1 $R1 & ${SF_SELECTED}
    
    ; 如果两者都未选，显示错误
    IntCmp $R0 0 0 skip_check
    IntCmp $R1 0 0 skip_check
    
    MessageBox MB_ICONEXCLAMATION|MB_OK "Please select at least one: Master or Slave!$\n$\nCannot leave both unselected."
    Abort
    
    skip_check:
FunctionEnd

Function .onInit
    ; 初始化变量
    StrCpy $EnableMaster "false"
    StrCpy $EnableSlave "false"
    
    ; 设置默认选择（两者都选）
    SectionSetFlags ${SecPanel} ${SF_SELECTED}    ; 面板必选
    SectionSetFlags ${SecMaster} ${SF_SELECTED}   ; 默认选择 Master
    SectionSetFlags ${SecSlave} ${SF_SELECTED}    ; 默认选择 Slave
    SectionSetFlags ${SecDeps} ${SF_SELECTED}
    
    ; 语言选择
    !insertmacro MUI_LANGDLL_DISPLAY
FunctionEnd

Function un.onInit
    ; 获取语言设置
    !insertmacro MUI_UNGETLANGUAGE
    
    ; 使用英文避免乱码
    MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 \
        "Are you sure you want to completely uninstall MT5 Signal System?$\n$\nThis will remove all installed files." \
        IDYES +2
    Abort
FunctionEnd