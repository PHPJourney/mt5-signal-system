; TradeMind MT5 - Unified Installer
; 交易智慧 - 面板必选，主从至少选一个

!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "FileFunc.nsh"

; DO NOT change directory - work from build/
; !cd ".."  ; <-- Remove this line

; Set code page to UTF-8
Unicode true

; General settings
Name "TradeMind MT5"
OutFile "..\dist\TradeMind_MT5_Installer.exe"
InstallDir "$PROGRAMFILES\TradeMindMT5"
RequestExecutionLevel admin
ShowInstDetails show
ShowUninstDetails show

; Fixed version number (no git hash)
!define VERSION "2.0.0"
VIProductVersion "${VERSION}.0"
VIAddVersionKey "ProductName" "TradeMind MT5"
VIAddVersionKey "FileVersion" "${VERSION}"
VIAddVersionKey "ProductVersion" "${VERSION}"
VIAddVersionKey "LegalCopyright" "TradeMind MT5"
VIAddVersionKey "FileDescription" "Intelligent Trading Strategy Platform"

; UI settings - icon is in dist/ directory
!define MUI_ABORTWARNING
!define MUI_ICON "..\dist\icon.ico"
!define MUI_UNICON "..\dist\icon.ico"

; Language settings - Default to Simplified Chinese
!define MUI_LANGDLL_REGISTRY_ROOT "HKLM"
!define MUI_LANGDLL_REGISTRY_KEY "Software\TradeMindMT5"
!define MUI_LANGDLL_REGISTRY_VALUENAME "Installer Language"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\LICENSE"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; Language - Simplified Chinese first, then English
!insertmacro MUI_LANGUAGE "SimpChinese"
!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_RESERVEFILE_LANGDLL

; Variables
Var EnableMaster
Var EnableSlave

; Component sections
Section "管理面板 (必选)" SecPanel
    SectionIn RO  ; Required, cannot be unchecked
    
    ; Set fixed size for display (in KB)
    SectionSetSize ${SecPanel} 15360  ; 15 MB for Manager EXE
SectionEnd

Section "策略引擎 (Master)" SecMaster
    ; Set fixed size for display (in KB)
    SectionSetSize ${SecMaster} 10240  ; 10 MB for Master EXE
    
    StrCpy $EnableMaster "true"
SectionEnd

Section "执行节点 (Slave)" SecSlave
    ; Set fixed size for display (in KB)
    SectionSetSize ${SecSlave} 10240  ; 10 MB for Slave EXE
    
    StrCpy $EnableSlave "true"
SectionEnd

Section "系统文档" SecDeps
    SectionSetSize ${SecDeps} 0
SectionEnd

Section "配置模板" SecConfig
    SetOutPath "$INSTDIR\config"
    
    IfFileExists "..\config\*.*" 0 +3
        File /r "..\config\*.*"
    Goto +2
        CreateDirectory "$INSTDIR\config"
    
    SetOutPath "$INSTDIR"
SectionEnd

Section "用户手册" SecDocs
    SetOutPath "$INSTDIR"
    
    IfFileExists "..\README.md" 0 +2
        File "..\README.md"
    IfFileExists "..\QUICKSTART.md" 0 +2
        File "..\QUICKSTART.md"
SectionEnd

; Post-installation: generate config and copy files
Section -Post
    SetOutPath "$INSTDIR"

    ; Generate install_config.json
    FileOpen $0 "$INSTDIR\install_config.json" w
    FileWrite $0 "{$\r$\n"
    
    StrCmp $EnableMaster "true" 0 +3
    FileWrite $0 '  "enable_master": true,$\r$\n'
    Goto +2
    FileWrite $0 '  "enable_master": false,$\r$\n'
    
    StrCmp $EnableSlave "true" 0 +3
    FileWrite $0 '  "enable_slave": true,$\r$\n'
    Goto +2
    FileWrite $0 '  "enable_slave": false$\r$\n'
    
    FileWrite $0 "}$\r$\n"
    FileClose $0

    ; Copy files from dist/ directory
    File "..\dist\MT5_Manager.exe"
    File "..\dist\icon.ico"

    ; Copy Master if selected
    StrCmp $EnableMaster "true" 0 +2
        File "..\dist\MT5_Master.exe"

    ; Copy Slave if selected
    StrCmp $EnableSlave "true" 0 +2
        File "..\dist\MT5_Slave.exe"

    ; Create README (English to avoid encoding issues)
    FileOpen $0 "$INSTDIR\README.txt" w
    FileWriteUTF16LE $0 "========================================$\r$\n"
    FileWriteUTF16LE $0 "TradeMind MT5 - Intelligent Trading Platform$\r$\n"
    FileWriteUTF16LE $0 "========================================$\r$\n"
    FileWriteUTF16LE $0 "This system provides intelligent trading strategies.$\r$\n"
    FileWriteUTF16LE $0 "Signals are distributed via MQTT to execution nodes.$\r$\n"
    FileWriteUTF16LE $0 "$\r$\n"
    FileWriteUTF16LE $0 "Components installed:$\r$\n"
    
    StrCmp $EnableMaster "true" 0 +2
        FileWriteUTF16LE $0 "  - Master Strategy Engine$\r$\n"
    StrCmp $EnableSlave "true" 0 +2
        FileWriteUTF16LE $0 "  - Slave Execution Node$\r$\n"
    
    FileWriteUTF16LE $0 "$\r$\n"
    FileWriteUTF16LE $0 "Getting Started:$\r$\n"
    FileWriteUTF16LE $0 "1. Launch TradeMind Manager from Desktop$\r$\n"
    FileWriteUTF16LE $0 "2. Configure MT5 terminal and MQTT settings$\r$\n"
    FileWriteUTF16LE $0 "3. Start Master/Slave services$\r$\n"
    FileClose $0

    ; Create shortcuts
    CreateShortCut "$DESKTOP\TradeMind Manager.lnk" "$INSTDIR\MT5_Manager.exe" "" "$INSTDIR\icon.ico"
    
    CreateDirectory "$SMPROGRAMS\TradeMind MT5"
    CreateShortCut "$SMPROGRAMS\TradeMind MT5\TradeMind Manager.lnk" "$INSTDIR\MT5_Manager.exe" "" "$INSTDIR\icon.ico"
    CreateShortCut "$SMPROGRAMS\TradeMind MT5\README.lnk" "$INSTDIR\README.txt"
    CreateShortCut "$SMPROGRAMS\TradeMind MT5\Uninstall.lnk" "$INSTDIR\uninstall.exe"

    ; Write uninstall info
    WriteUninstaller "$INSTDIR\uninstall.exe"
    
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\TradeMindMT5" \
                     "DisplayName" "TradeMind MT5"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\TradeMindMT5" \
                     "UninstallString" "$INSTDIR\uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\TradeMindMT5" \
                     "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\TradeMindMT5" \
                     "DisplayIcon" "$INSTDIR\icon.ico"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\TradeMindMT5" \
                     "Publisher" "TradeMind MT5"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\TradeMindMT5" \
                     "DisplayVersion" "${VERSION}"
    
    SetOutPath "$INSTDIR"
SectionEnd

; Uninstall section
Section "Uninstall"
    Delete "$INSTDIR\MT5_Manager.exe"
    Delete "$INSTDIR\MT5_Master.exe"
    Delete "$INSTDIR\MT5_Slave.exe"
    Delete "$INSTDIR\icon.ico"
    Delete "$INSTDIR\install_config.json"
    Delete "$INSTDIR\README.txt"
    Delete "$INSTDIR\README.md"
    Delete "$INSTDIR\QUICKSTART.md"
    Delete "$INSTDIR\uninstall.exe"

    Delete "$DESKTOP\TradeMind Manager.lnk"
    Delete "$SMPROGRAMS\TradeMind MT5\TradeMind Manager.lnk"
    Delete "$SMPROGRAMS\TradeMind MT5\README.lnk"
    Delete "$SMPROGRAMS\TradeMind MT5\Uninstall.lnk"

    RMDir "$SMPROGRAMS\TradeMind MT5"
    RMDir /r "$INSTDIR\config"
    RMDir /r "$INSTDIR\logs"
    RMDir "$INSTDIR"

    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\TradeMindMT5"
    DeleteRegKey /ifempty HKLM "Software\TradeMindMT5"
SectionEnd

; Descriptions
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SecPanel} "管理面板 - 配置和监控（必选）"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecMaster} "策略引擎 - 智能交易策略（Master 主服务器）"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecSlave} "执行节点 - 信号执行和订单管理（Slave 从服务器）"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecDeps} "系统文档"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecConfig} "配置模板"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecDocs} "用户手册"
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; Validation: at least one of Master/Slave must be selected
Function .onLeaveComponents
    ; Check if Master is selected
    SectionGetFlags ${SecMaster} $R0
    IntOp $R0 $R0 & ${SF_SELECTED}
    
    ; Check if Slave is selected
    SectionGetFlags ${SecSlave} $R1
    IntOp $R1 $R1 & ${SF_SELECTED}
    
    ; If both are NOT selected (both flags are 0)
    IntCmp $R0 0 check_slave skip_check check_slave
    
    check_slave:
    IntCmp $R1 0 0 skip_check
    
    ; Both are unselected, show error
    MessageBox MB_ICONEXCLAMATION|MB_OK \
        "请至少选择一项：Master 策略引擎 或 Slave 执行节点！$\n$\n两者不能同时不选。" \
        /SD IDOK
    Abort
    
    skip_check:
FunctionEnd

Function .onInit
    ; Initialize variables
    StrCpy $EnableMaster "false"
    StrCpy $EnableSlave "false"
    
    ; Set default selections
    SectionSetFlags ${SecPanel} ${SF_SELECTED}
    SectionSetFlags ${SecMaster} ${SF_SELECTED}
    SectionSetFlags ${SecSlave} ${SF_SELECTED}
    SectionSetFlags ${SecDeps} ${SF_SELECTED}
    
    ; Display language selection dialog
    !insertmacro MUI_LANGDLL_DISPLAY
    
    ; Check if user cancelled language selection
    ; $Language will be 0 if cancelled
    StrCmp $Language 0 0 lang_ok
    
    ; User cancelled, abort installation
    Abort
    
    lang_ok:
    ; Continue with installation
FunctionEnd

Function un.onInit
    !insertmacro MUI_UNGETLANGUAGE
    
    MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 \
        "您确定要完全卸载 TradeMind MT5 吗？$\n$\n此操作将删除所有文件。" \
        /SD IDNO \
        IDYES +2
    Abort
FunctionEnd