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

; Include language packs
!include "lang\Chinese.nsh"
!include "lang\English.nsh"

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
Section "$(SEC_PANEL_NAME)" SecPanel
    SectionIn RO
    
    SetOutPath "$INSTDIR"
    
    File "..\dist\MT5_Manager.exe"
    File "..\dist\icon.png"
    
    ; 创建语言目录并复制语言文件
    SetOutPath "$INSTDIR\lang"
    File "..\lang\Chinese.json"
    File "..\lang\English.json"
    
    ; 复制国际化模块
    SetOutPath "$INSTDIR\common"
    File "..\common\i18n.py"
    File "..\common\__init__.py"
    File "..\common\models.py"
    File "..\common\utils.py"
    File "..\common\mqtt_client.py"
    
    SectionSetSize ${SecPanel} 15360
SectionEnd

Section "$(SEC_MASTER_NAME)" SecMaster
    SetOutPath "$INSTDIR"
    
    File "..\dist\MT5_Master.exe"
    
    SectionSetSize ${SecMaster} 10240
    
    StrCpy $EnableMaster "true"
SectionEnd

Section "$(SEC_SLAVE_NAME)" SecSlave
    SetOutPath "$INSTDIR"
    
    File "..\dist\MT5_Slave.exe"
    
    SectionSetSize ${SecSlave} 10240
    
    StrCpy $EnableSlave "true"
SectionEnd

Section "$(SEC_CONFIG_NAME)" SecConfig
    SetOutPath "$INSTDIR\config"
    
    IfFileExists "..\config\master_config.json" 0 +2
        File "..\config\master_config.json"
    IfFileExists "..\config\slave_config.json" 0 +2
        File "..\config\slave_config.json"
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
    FileWrite $0 '    "client_id": "master_001",$\r$\n'
    FileWrite $0 '    "topic_prefix": "mt5/signal"$\r$\n'
    FileWrite $0 '  },$\r$\n'
    FileWrite $0 '  "mt5": {$\r$\n'
    FileWrite $0 '    "terminal_path": "",$\r$\n'
    FileWrite $0 '    "auto_select": true$\r$\n'
    FileWrite $0 '  },$\r$\n'
    FileWrite $0 '  "signal": {$\r$\n'
    FileWrite $0 '    "broadcast_interval": 1,$\r$\n'
    FileWrite $0 '    "include_positions": true,$\r$\n'
    FileWrite $0 '    "include_orders": true$\r$\n'
    FileWrite $0 '  },$\r$\n'
    FileWrite $0 '  "logging": {$\r$\n'
    FileWrite $0 '    "file": "logs/master.log",$\r$\n'
    FileWrite $0 '    "level": "INFO"$\r$\n'
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
    FileWrite $0 '    "client_id": "slave_001",$\r$\n'
    FileWrite $0 '    "topic_prefix": "mt5/signal"$\r$\n'
    FileWrite $0 '  },$\r$\n'
    FileWrite $0 '  "mt5": {$\r$\n'
    FileWrite $0 '    "terminal_path": "",$\r$\n'
    FileWrite $0 '    "auto_select": true$\r$\n'
    FileWrite $0 '  },$\r$\n'
    FileWrite $0 '  "subscription": {$\r$\n'
    FileWrite $0 '    "master_id": "master_001"$\r$\n'
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
    FileWrite $0 '  "security": {$\r$\n'
    FileWrite $0 '    "allow_auto_trading": true,$\r$\n'
    FileWrite $0 '    "allow_dll_import": false$\r$\n'
    FileWrite $0 '  },$\r$\n'
    FileWrite $0 '  "risk": {$\r$\n'
    FileWrite $0 '    "max_drawdown_percent": 10.0,$\r$\n'
    FileWrite $0 '    "max_drawdown_usd": 1000.0,$\r$\n'
    FileWrite $0 '    "max_profit_percent": 20.0,$\r$\n'
    FileWrite $0 '    "max_profit_usd": 2000.0,$\r$\n'
    FileWrite $0 '    "session_loss_usd": 0.0,$\r$\n'
    FileWrite $0 '    "session_profit_usd": 0.0,$\r$\n'
    FileWrite $0 '    "cooldown_minutes": 0,$\r$\n'
    FileWrite $0 '    "max_positions": 3,$\r$\n'
    FileWrite $0 '    "max_total_lots": 10.0,$\r$\n'
    FileWrite $0 '    "lot_mode": "multiplier",$\r$\n'
    FileWrite $0 '    "lot_multiplier": 1.0,$\r$\n'
    FileWrite $0 '    "fixed_lot": 0.1,$\r$\n'
    FileWrite $0 '    "balance_ratio": 1.0,$\r$\n'
    FileWrite $0 '    "usd_per_lot": 1000.0,$\r$\n'
    FileWrite $0 '    "incremental_base": 0.01,$\r$\n'
    FileWrite $0 '    "incremental_step": 0.01,$\r$\n'
    FileWrite $0 '    "min_lot": 0.01,$\r$\n'
    FileWrite $0 '    "max_lot": 888.8,$\r$\n'
    FileWrite $0 '    "skip_lot_less_than": 0.01,$\r$\n'
    FileWrite $0 '    "skip_lot_greater_than": 888.8$\r$\n'
    FileWrite $0 '  },$\r$\n'
    FileWrite $0 '  "filter": {$\r$\n'
    FileWrite $0 '    "follow_buy": true,$\r$\n'
    FileWrite $0 '    "follow_sell": true,$\r$\n'
    FileWrite $0 '    "follow_market_orders": true,$\r$\n'
    FileWrite $0 '    "follow_pending_orders": false,$\r$\n'
    FileWrite $0 '    "follow_old_orders": false,$\r$\n'
    FileWrite $0 '    "max_order_age_minutes": 0.0,$\r$\n'
    FileWrite $0 '    "allow_duplicate_follow": false,$\r$\n'
    FileWrite $0 '    "follow_close": true,$\r$\n'
    FileWrite $0 '    "follow_sl_tp": false,$\r$\n'
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