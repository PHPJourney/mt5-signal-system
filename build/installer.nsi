; TradeMind MT5 - Unified Installer
# 文件编码
Unicode True

; TradeMind MT5 Installer Script

!define PRODUCT_NAME "TradeMind MT5"
!define PRODUCT_VERSION "1.0.0"
!define PRODUCT_PUBLISHER "TradeMind"
!define PRODUCT_WEB_SITE "https://mt5data.cidhub.com"
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
VIAddVersionKey "LegalCopyright" "版权所有 © 2026 TradeMind - mt5data.cidhub.com"
VIAddVersionKey "FileDescription" "MT5 智能交易策略跟单系统"
VIAddVersionKey "LegalTrademarks" "TradeMind MT5"
VIAddVersionKey "CompanyName" "TradeMind"
VIAddVersionKey "Comments" "官方网站: https://mt5data.cidhub.com"

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

; 自定义完成页面（添加版权和链接信息）
!define MUI_PAGE_CUSTOMFUNCTION_SHOW ShowFinishPage
!insertmacro MUI_PAGE_FINISH

; 创建自定义函数声明
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

; 自定义完成页面显示函数
Function ShowFinishPage
    ; 获取完成页面文本框控件
    FindWindow $R0 "#32770" "" $HWNDPARENT
    GetDlgItem $R1 $R0 1006  ; MUI 完成页面文本框 ID
    
    ; 如果有控件，添加版权信息
    ${If} $R1 != 0
        ; 设置新的文本内容（包含版权和链接）
        SendMessage $R1 ${WM_SETTEXT} 0 "STR:TradeMind MT5 安装完成！$\n$\n$\n📄 版权所有 © 2026 TradeMind$\n🔗 官方网站: https://mt5data.cidhub.com$\n📧 技术支持: 请访问官网获取帮助$\n$\n感谢您的使用！"
    ${EndIf}
FunctionEnd

; Variables
Var EnableMaster
Var EnableSlave

; Component sections
Section "$(SEC_PANEL_NAME)" SecPanel
    SectionIn RO
    
    SetOutPath "$INSTDIR"
    
    ; 复制管理面板 EXE（已打包所有代码和语言包）
    DetailPrint "$(MSG_INSTALLING_PANEL)"
    File "..\dist\MT5_Manager.exe"
    DetailPrint "$(MSG_INSTALLING_ICON)"
    File "..\dist\icon.png"
    
    ; 创建版权信息文件
    DetailPrint "$(MSG_CREATING_COPYRIGHT)"
    FileOpen $0 "$INSTDIR\版权说明.txt" w
    FileWrite $0 "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$\r$\n"
    FileWrite $0 "   TradeMind MT5 - 智能交易策略跟单系统$\r$\n"
    FileWrite $0 "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$\r$\n$\r$\n"
    FileWrite $0 "版权所有 © 2026 TradeMind$\r$\n$\r$\n"
    FileWrite $0 "官方网站: https://mt5data.cidhub.com$\r$\n"
    FileWrite $0 "技术支持: 请访问官网获取帮助$\r$\n$\r$\n"
    FileWrite $0 "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$\r$\n$\r$\n"
    FileWrite $0 "功能说明：$\r$\n"
    FileWrite $0 "- Master 策略引擎：监控 MT5 交易信号并推送$\r$\n"
    FileWrite $0 "- Slave 执行节点：接收信号并执行跟单交易$\r$\n"
    FileWrite $0 "- 管理面板：可视化配置和监控$\r$\n$\r$\n"
    FileWrite $0 "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$\r$\n"
    FileClose $0
    
    ; 复制语言文件（用于运行时切换语言）
    DetailPrint "$(MSG_INSTALLING_LANG)"
    SetOutPath "$INSTDIR\lang"
    File "..\lang\Chinese.json"
    File "..\lang\English.json"
    
    DetailPrint "$(MSG_PANEL_COMPLETE)"
    SectionSetSize ${SecPanel} 35000
SectionEnd

Section "$(SEC_MASTER_NAME)" SecMaster
    SetOutPath "$INSTDIR"
    
    ; 复制 Master 服务 EXE（已打包所有代码和语言包）
    DetailPrint "$(MSG_INSTALLING_MASTER)"
    File "..\dist\MT5_Master.exe"
    
    ; 复制配置文件
    DetailPrint "$(MSG_INSTALLING_MASTER_CONFIG)"
    SetOutPath "$INSTDIR\config"
    IfFileExists "..\config\master_config.json" 0 +2
        File "..\config\master_config.json"
    
    DetailPrint "$(MSG_MASTER_COMPLETE)"
    SectionSetSize ${SecMaster} 20480
    
    StrCpy $EnableMaster "true"
SectionEnd

Section "$(SEC_SLAVE_NAME)" SecSlave
    SetOutPath "$INSTDIR"
    
    ; 复制 Slave 服务 EXE（已打包所有代码和语言包）
    DetailPrint "$(MSG_INSTALLING_SLAVE)"
    File "..\dist\MT5_Slave.exe"
    
    ; 复制配置文件
    DetailPrint "$(MSG_INSTALLING_SLAVE_CONFIG)"
    SetOutPath "$INSTDIR\config"
    IfFileExists "..\config\slave_config.json" 0 +2
        File "..\config\slave_config.json"
    
    DetailPrint "$(MSG_SLAVE_COMPLETE)"
    SectionSetSize ${SecSlave} 20480
    
    StrCpy $EnableSlave "true"
SectionEnd

Section "$(SEC_DOCS_NAME)" SecDocs
    SetOutPath "$INSTDIR"
    
    DetailPrint "$(MSG_INSTALLING_DOCS)"
    IfFileExists "..\README.md" 0 +2
        File "..\README.md"
    IfFileExists "..\QUICKSTART.md" 0 +2
        File "..\QUICKSTART.md"
    
    DetailPrint "$(MSG_DOCS_COMPLETE)"
SectionEnd

; Post-installation: generate config and copy files
Section -Post
    SetOutPath "$INSTDIR"
    
    DetailPrint "$(MSG_GENERATING_CONFIG)"
    
    ; 生成配置文件（如果不存在）
    IfFileExists "$INSTDIR\config\master_config.json" config_exist_m 0
        DetailPrint "$(MSG_CREATING_MASTER_CONFIG)"
        CreateDirectory "$INSTDIR\config"
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
        DetailPrint "$(MSG_MASTER_CONFIG_CREATED)"
    config_exist_m:
    
    IfFileExists "$INSTDIR\config\slave_config.json" config_exist_s 0
        DetailPrint "$(MSG_CREATING_SLAVE_CONFIG)"
        CreateDirectory "$INSTDIR\config"
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
        DetailPrint "$(MSG_SLAVE_CONFIG_CREATED)"
    config_exist_s:
    
    DetailPrint "$(MSG_CREATING_SHORTCUTS)"
    create_links:
    ; Create shortcuts
    CreateDirectory "$SMPROGRAMS\$(SHORTCUT_FOLDER_NAME)"
    CreateShortCut "$SMPROGRAMS\$(SHORTCUT_FOLDER_NAME)\$(SHORTCUT_MANAGER).lnk" "$INSTDIR\MT5_Manager.exe"
    CreateShortCut "$DESKTOP\$(SHORTCUT_MANAGER).lnk" "$INSTDIR\MT5_Manager.exe"
    CreateShortCut "$SMPROGRAMS\$(SHORTCUT_FOLDER_NAME)\$(SHORTCUT_README).lnk" "$INSTDIR\README.md"
    CreateShortCut "$SMPROGRAMS\$(SHORTCUT_FOLDER_NAME)\$(SHORTCUT_UNINSTALL).lnk" "$INSTDIR\uninstall.exe"
    CreateShortCut "$SMPROGRAMS\$(SHORTCUT_FOLDER_NAME)\$(SHORTCUT_WEBSITE).lnk" "https://mt5data.cidhub.com"

    DetailPrint "$(MSG_REGISTERING_UNINSTALL)"
    ; Write uninstall information
    WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayName" "${PRODUCT_NAME}"
    WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninstall.exe"
    WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\MT5_Manager.exe"
    WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
    WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
    WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "https://mt5data.cidhub.com"
    WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "URLUpdateInfo" "https://mt5data.cidhub.com"

    DetailPrint "$(MSG_CREATING_UNINSTALLER)"
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"
    
    DetailPrint "$(MSG_POST_INSTALL_COMPLETE)"
SectionEnd

; Uninstall section
Section "Uninstall"
    Delete "$INSTDIR\MT5_Manager.exe"
    Delete "$INSTDIR\MT5_Master.exe"
    Delete "$INSTDIR\MT5_Slave.exe"
    Delete "$INSTDIR\uninstall.exe"
    Delete "$INSTDIR\icon.png"
    Delete "$INSTDIR\版权说明.txt"

    Delete "$DESKTOP\TradeMind Manager.lnk"
    Delete "$SMPROGRAMS\TradeMind MT5\TradeMind Manager.lnk"
    Delete "$SMPROGRAMS\TradeMind MT5\README.lnk"
    Delete "$SMPROGRAMS\TradeMind MT5\Uninstall.lnk"
    Delete "$SMPROGRAMS\TradeMind MT5\官方网站.lnk"

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
    
    ; Display language selection dialog FIRST
    !insertmacro MUI_LANGDLL_DISPLAY
    
    ; Set default selections AFTER language selection
    SectionSetFlags ${SecPanel} ${SF_SELECTED}
    SectionSetFlags ${SecMaster} ${SF_SELECTED}
    SectionSetFlags ${SecSlave} ${SF_SELECTED}
    SectionSetFlags ${SecDocs} ${SF_SELECTED}
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