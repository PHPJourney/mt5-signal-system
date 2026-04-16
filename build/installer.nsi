; TradeMind MT5 - Unified Installer
; 交易智慧 - 面板必选，主从至少选一个
# 文件编码
Unicode True

; TradeMind MT5 Installer Script

!define PRODUCT_NAME "TradeMind MT5"
!define PRODUCT_VERSION "1.0.0"
!define PRODUCT_PUBLISHER "TradeMind"
!define PRODUCT_WEB_SITE "https://trademind.dev"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\TradeMindMT5"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"

SetCompressor /SOLID lzma

; MUI 2.0
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
    
    SetOutPath "$INSTDIR"
    
    ; Copy Manager executable
    IfFileExists "..\dist\MT5_Manager.exe" 0 +3
        File "..\dist\MT5_Manager.exe"
        Goto +2
        DetailPrint "Warning: MT5_Manager.exe not found"
    
    ; Set fixed size for display (in KB)
    SectionSetSize ${SecPanel} 15360  ; 15 MB for Manager EXE
SectionEnd

Section "策略引擎 (Master)" SecMaster
    SetOutPath "$INSTDIR"
    
    ; Copy Master executable
    IfFileExists "..\dist\MT5_Master.exe" 0 +3
        File "..\dist\MT5_Master.exe"
        Goto +2
        DetailPrint "Warning: MT5_Master.exe not found"
    
    ; Set fixed size for display (in KB)
    SectionSetSize ${SecMaster} 10240  ; 10 MB for Master EXE
    
    StrCpy $EnableMaster "true"
SectionEnd

Section "执行节点 (Slave)" SecSlave
    SetOutPath "$INSTDIR"
    
    ; Copy Slave executable
    IfFileExists "..\dist\MT5_Slave.exe" 0 +3
        File "..\dist\MT5_Slave.exe"
        Goto +2
        DetailPrint "Warning: MT5_Slave.exe not found"
    
    ; Set fixed size for display (in KB)
    SectionSetSize ${SecSlave} 10240  ; 10 MB for Slave EXE
    
    StrCpy $EnableSlave "true"
SectionEnd

Section "系统文档" SecDeps
    SectionSetSize ${SecDeps} 0
SectionEnd

Section "配置模板" SecConfig
    SetOutPath "$INSTDIR\config"
    
    ; Copy config files
    IfFileExists "..\config\master_config.json" 0 +2
        File "..\config\master_config.json"
    IfFileExists "..\config\slave_config.json" 0 +2
        File "..\config\slave_config.json"
    
    SetOutPath "$INSTDIR"
SectionEnd

Section "用户手册" SecDocs
    SetOutPath "$INSTDIR"
    
    ; Copy documentation
    IfFileExists "..\README.md" 0 +2
        File "..\README.md"
    IfFileExists "..\QUICKSTART.md" 0 +2
        File "..\QUICKSTART.md"
    IfFileExists "..\INSTALL_GUIDE.md" 0 +2
        File "..\INSTALL_GUIDE.md"
SectionEnd

; Post-installation: generate config and copy files
Section -Post
    SetOutPath "$INSTDIR"

    ; Create directories
    CreateDirectory "$INSTDIR\config"
    CreateDirectory "$INSTDIR\logs"

    ; Generate default master_config.json if not exists
    IfFileExists "$INSTDIR\config\master_config.json" 0 gen_master
    Goto check_slave
    
    gen_master:
    FileOpen $0 "$INSTDIR\config\master_config.json" w
    FileWrite $0 "{$\r$\n"
    FileWrite $0 '  "enabled": true,$\r$\n'
    FileWrite $0 '  "mqtt": {$\r$\n'
    FileWrite $0 '    "broker": "localhost",$\r$\n'
    FileWrite $0 '    "port": 1883,$\r$\n'
    FileWrite $0 '    "username": "master",$\r$\n'
    FileWrite $0 '    "password": "",$\r$\n'
    FileWrite $0 '    "client_id": "master_001"$\r$\n'
    FileWrite $0 '  },$\r$\n'
    FileWrite $0 '  "mt5": {$\r$\n'
    FileWrite $0 '    "terminal_path": "",$\r$\n'
    FileWrite $0 '    "auto_select": true$\r$\n'
    FileWrite $0 '  },$\r$\n'
    FileWrite $0 '  "signal": {$\r$\n'
    FileWrite $0 '    "symbols": ["EURUSD", "GBPUSD", "USDJPY"],$\r$\n'
    FileWrite $0 '    "max_positions": 5,$\r$\n'
    FileWrite $0 '    "lot_size": 0.01$\r$\n'
    FileWrite $0 '  }$\r$\n'
    FileWrite $0 "}$\r$\n"
    FileClose $0
    
    check_slave:
    IfFileExists "$INSTDIR\config\slave_config.json" 0 gen_slave
    Goto create_links
    
    gen_slave:
    FileOpen $0 "$INSTDIR\config\slave_config.json" w
    FileWrite $0 "{$\r$\n"
    FileWrite $0 '  "enabled": true,$\r$\n'
    FileWrite $0 '  "mqtt": {$\r$\n'
    FileWrite $0 '    "broker": "localhost",$\r$\n'
    FileWrite $0 '    "port": 1883,$\r$\n'
    FileWrite $0 '    "username": "slave",$\r$\n'
    FileWrite $0 '    "password": "",$\r$\n'
    FileWrite $0 '    "client_id": "slave_001"$\r$\n'
    FileWrite $0 '  },$\r$\n'
    FileWrite $0 '  "mt5": {$\r$\n'
    FileWrite $0 '    "terminal_path": "",$\r$\n'
    FileWrite $0 '    "auto_select": true$\r$\n'
    FileWrite $0 '  },$\r$\n'
    FileWrite $0 '  "subscription": {$\r$\n'
    FileWrite $0 '    "master_id": "master_001"$\r$\n'
    FileWrite $0 '  },$\r$\n'
    FileWrite $0 '  "risk": {$\r$\n'
    FileWrite $0 '    "max_drawdown": 10,$\r$\n'
    FileWrite $0 '    "max_positions": 3,$\r$\n'
    FileWrite $0 '    "lot_multiplier": 1.0$\r$\n'
    FileWrite $0 '  }$\r$\n'
    FileWrite $0 "}$\r$\n"
    FileClose $0
    
    create_links:
    ; Create shortcuts
    CreateDirectory "$SMPROGRAMS\TradeMind MT5"
    CreateShortCut "$SMPROGRAMS\TradeMind MT5\TradeMind Manager.lnk" "$INSTDIR\MT5_Manager.exe"
    CreateShortCut "$DESKTOP\TradeMind Manager.lnk" "$INSTDIR\MT5_Manager.exe"
    CreateShortCut "$SMPROGRAMS\TradeMind MT5\README.lnk" "$INSTDIR\README.md"
    CreateShortCut "$SMPROGRAMS\TradeMind MT5\Uninstall.lnk" "$INSTDIR\uninstall.exe"

    ; Write uninstall information
    WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayName" "${PRODUCT_NAME}"
    WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninstall.exe"
    WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\MT5_Manager.exe"
    WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
    WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"

    ; Create uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"
SectionEnd

; Uninstall section
Section "Uninstall"
    Delete "$INSTDIR\MT5_Manager.exe"
    Delete "$INSTDIR\MT5_Master.exe"
    Delete "$INSTDIR\MT5_Slave.exe"
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
