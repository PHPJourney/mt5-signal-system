; TradeMind MT5 - Unified Installer
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

; Language - MUST be defined BEFORE including language files
!insertmacro MUI_LANGUAGE "SimpChinese"
!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_RESERVEFILE_LANGDLL

; NOW include language packs (after MUI_LANGUAGE declarations)
!include "..\lang\Chinese.nsh"
!include "..\lang\English.nsh"

; Variables
Var EnableMaster
Var EnableSlave

; Component sections
Section "$(SEC_PANEL_NAME)" SecPanel
    SectionIn RO
    
    SetOutPath "$INSTDIR"
    
    ; 复制管理面板 EXE（已打包所有代码和语言包）
    File "..\dist\MT5_Manager.exe"
    File "..\dist\icon.png"
    
    ; 复制语言文件（用于运行时切换语言）
    SetOutPath "$INSTDIR\lang"
    File "..\lang\Chinese.json"
    File "..\lang\English.json"
    
    SectionSetSize ${SecPanel} 35000
SectionEnd

Section "$(SEC_MASTER_NAME)" SecMaster
    SetOutPath "$INSTDIR"
    
    ; 复制 Master 服务 EXE（已打包所有代码和语言包）
    File "..\dist\MT5_Master.exe"
    
    ; 复制配置文件
    SetOutPath "$INSTDIR\config"
    IfFileExists "..\config\master_config.json" 0 +2
        File "..\config\master_config.json"
    
    SectionSetSize ${SecMaster} 20480
    
    StrCpy $EnableMaster "true"
SectionEnd

Section "$(SEC_SLAVE_NAME)" SecSlave
    SetOutPath "$INSTDIR"
    
    ; 复制 Slave 服务 EXE（已打包所有代码和语言包）
    File "..\dist\MT5_Slave.exe"
    
    ; 复制配置文件
    SetOutPath "$INSTDIR\config"
    IfFileExists "..\config\slave_config.json" 0 +2
        File "..\config\slave_config.json"
    
    SectionSetSize ${SecSlave} 20480
    
    StrCpy $EnableSlave "true"
SectionEnd

Section "$(SEC_DOCS_NAME)" SecDocs
    SetOutPath "$INSTDIR"
    
    IfFileExists "..\README.md" 0 +2
        File "..\README.md"
    IfFileExists "..\QUICKSTART.md" 0 +2
        File "..\QUICKSTART.md"
SectionEnd

; Post-installation: generate config and copy files
Section -Post
    SetOutPath "$INSTDIR"
    
    ; 生成配置文件（如果不存在）
    IfFileExists "$INSTDIR\config\master_config.json" config_exist_m 0
        DetailPrint "Creating master_config.json..."
        FileOpen $0 "$INSTDIR\config\master_config.json" w
        FileWrite $0 "{$\r$\n"
        FileWrite $0 '  "mqtt": {$\r$\n'
        FileWrite $0 '    "host": "localhost",$\r$\n'
        FileWrite $0 '    "port": 1883,$\r$\n'
        FileWrite $0 '    "username": "",$\r$\n'
        FileWrite $0 '    "password": "",$\r$\n'
        FileWrite $0 '    "client_id": "MT5_Master_001",$\r$\n'
        FileWrite $0 '    "topic_prefix": "trademind/",$\r$\n'
        FileWrite $0 '    "qos": 1,$\r$\n'
        FileWrite $0 '    "keepalive": 60$\r$\n'
        FileWrite $0 '  },$\r$\n'
        FileWrite $0 '  "mt5": {$\r$\n'
        FileWrite $0 '    "login": 0,$\r$\n'
        FileWrite $0 '    "password": "",$\r$\n'
        FileWrite $0 '    "server": ""$\r$\n'
        FileWrite $0 '  },$\r$\n'
        FileWrite $0 '  "logging": {$\r$\n'
        FileWrite $0 '    "file": "logs/master.log",$\r$\n'
        FileWrite $0 '    "level": "INFO"$\r$\n'
        FileWrite $0 '  },$\r$\n'
        FileWrite $0 '  "common": {$\r$\n'
        FileWrite $0 '    "check_interval": 5,$\r$\n'
        FileWrite $0 '    "reconnect_delay": 10,$\r$\n'
        FileWrite $0 '    "max_reconnect_attempts": 0$\r$\n'
        FileWrite $0 '  },$\r$\n'
        FileWrite $0 '  "alerts": {$\r$\n'
        FileWrite $0 '    "enabled": true,$\r$\n'
        FileWrite $0 '    "sound": true,$\r$\n'
        FileWrite $0 '    "popup": true,$\r$\n'
        FileWrite $0 '    "email": false,$\r$\n'
        FileWrite $0 '    "email_to": ""$\r$\n'
        FileWrite $0 '  }$\r$\n'
        FileWrite $0 "}$\r$\n"
        FileClose $0
    config_exist_m:
    
    IfFileExists "$INSTDIR\config\slave_config.json" config_exist_s 0
        DetailPrint "Creating slave_config.json..."
        FileOpen $0 "$INSTDIR\config\slave_config.json" w
        FileWrite $0 "{$\r$\n"
        FileWrite $0 '  "mqtt": {$\r$\n'
        FileWrite $0 '    "host": "localhost",$\r$\n'
        FileWrite $0 '    "port": 1883,$\r$\n'
        FileWrite $0 '    "username": "",$\r$\n'
        FileWrite $0 '    "password": "",$\r$\n'
        FileWrite $0 '    "client_id": "MT5_Slave_001",$\r$\n'
        FileWrite $0 '    "topic_prefix": "trademind/",$\r$\n'
        FileWrite $0 '    "qos": 1,$\r$\n'
        FileWrite $0 '    "keepalive": 60$\r$\n'
        FileWrite $0 '  },$\r$\n'
        FileWrite $0 '  "mt5": {$\r$\n'
        FileWrite $0 '    "login": 0,$\r$\n'
        FileWrite $0 '    "password": "",$\r$\n'
        FileWrite $0 '    "server": ""$\r$\n'
        FileWrite $0 '  },$\r$\n'
        FileWrite $0 '  "logging": {$\r$\n'
        FileWrite $0 '    "file": "logs/slave.log",$\r$\n'
        FileWrite $0 '    "level": "INFO"$\r$\n'
        FileWrite $0 '  },$\r$\n'
        FileWrite $0 '  "common": {$\r$\n'
        FileWrite $0 '    "follow_mode": "both",$\r$\n'
        FileWrite $0 '    "enable_alerts": true,$\r$\n'
        FileWrite $0 '    "stop_alert_on_price": false,$\r$\n'
        FileWrite $0 '    "reverse_trading": false,$\r$\n'
        FileWrite $0 '    "magic_number": 999999,$\r$\n'
        FileWrite $0 '    "slippage_points": 30,$\r$\n'
        FileWrite $0 '    "comment_prefix": "TM_"$\r$\n'
        FileWrite $0 '  },$\r$\n'
        FileWrite $0 '  "risk": {$\r$\n'
        FileWrite $0 '    "lot_mode": "multiplier",$\r$\n'
        FileWrite $0 '    "lot_multiplier": 1.0,$\r$\n'
        FileWrite $0 '    "fixed_lot": 0.01,$\r$\n'
        FileWrite $0 '    "min_lot": 0.01,$\r$\n'
        FileWrite $0 '    "max_lot": 100.0,$\r$\n'
        FileWrite $0 '    "lot_step": 0.01,$\r$\n'
        FileWrite $0 '    "max_positions": 10,$\r$\n'
        FileWrite $0 '    "max_daily_loss": 0,$\r$\n'
        FileWrite $0 '    "max_drawdown_percent": 0,$\r$\n'
        FileWrite $0 '    "stop_trading_on_loss": false$\r$\n'
        FileWrite $0 '  },$\r$\n'
        FileWrite $0 '  "filter": {$\r$\n'
        FileWrite $0 '    "enabled": false,$\r$\n'
        FileWrite $0 '    "min_lot": 0,$\r$\n'
        FileWrite $0 '    "max_lot": 0,$\r$\n'
        FileWrite $0 '    "require_profit_points": 0,$\r$\n'
        FileWrite $0 '    "require_loss_points": 0,$\r$\n'
        FileWrite $0 '    "max_price_deviation_points": 0,$\r$\n'
        FileWrite $0 '    "allowed_magics": [],$\r$\n'
        FileWrite $0 '    "required_comments": [],$\r$\n'
        FileWrite $0 '    "allowed_hours_start": "00:00:00",$\r$\n'
        FileWrite $0 '    "allowed_hours_end": "23:59:59",$\r$\n'
        FileWrite $0 '    "whitelist_symbols": [],$\r$\n'
        FileWrite $0 '    "blacklist_symbols": []$\r$\n'
        FileWrite $0 '  },$\r$\n'
        FileWrite $0 '  "trailing_stop": {$\r$\n'
        FileWrite $0 '    "enabled": false,$\r$\n'
        FileWrite $0 '    "profit_points": 0,$\r$\n'
        FileWrite $0 '    "trail_points": 0$\r$\n'
        FileWrite $0 '  },$\r$\n'
        FileWrite $0 '  "symbol_mapping": {},$\r$\n'
        FileWrite $0 '  "advanced": {$\r$\n'
        FileWrite $0 '    "refresh_interval_ms": 150,$\r$\n'
        FileWrite $0 '    "auto_clear_traces": true,$\r$\n'
        FileWrite $0 '    "disconnect_alert_seconds": 30,$\r$\n'
        FileWrite $0 '    "custom_comment": ""$\r$\n'
        FileWrite $0 '  }$\r$\n'
        FileWrite $0 "}$\r$\n"
        FileClose $0
    config_exist_s:
    
    create_links:
    ; Create shortcuts
    CreateDirectory "$SMPROGRAMS\$(SHORTCUT_FOLDER_NAME)"
    CreateShortCut "$SMPROGRAMS\$(SHORTCUT_FOLDER_NAME)\$(SHORTCUT_MANAGER).lnk" "$INSTDIR\MT5_Manager.exe"
    CreateShortCut "$DESKTOP\$(SHORTCUT_MANAGER).lnk" "$INSTDIR\MT5_Manager.exe"
    CreateShortCut "$SMPROGRAMS\$(SHORTCUT_FOLDER_NAME)\$(SHORTCUT_README).lnk" "$INSTDIR\README.md"
    CreateShortCut "$SMPROGRAMS\$(SHORTCUT_FOLDER_NAME)\$(SHORTCUT_UNINSTALL).lnk" "$INSTDIR\uninstall.exe"

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
    Delete "$INSTDIR\icon.png"

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
    !insertmacro MUI_DESCRIPTION_TEXT ${SecPanel} "$(SEC_PANEL_DESC)"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecMaster} "$(SEC_MASTER_DESC)"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecSlave} "$(SEC_SLAVE_DESC)"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecConfig} "$(SEC_CONFIG_DESC)"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecDocs} "$(SEC_DOCS_DESC)"
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
        "$(VALIDATION_MASTER_SLAVE_REQUIRED)" \
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
    SectionSetFlags ${SecConfig} ${SF_SELECTED}
    SectionSetFlags ${SecDocs} ${SF_SELECTED}
    
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
    
    ; Use language string for uninstall confirmation
    MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 \
        "$(MUI_UNTEXT_CONFIRM_TEXT)" \
        /SD IDNO \
        IDYES +2
    Abort
FunctionEnd