; TradeMind MT5 - Unified Installer
; 交易智慧 - 面板必选，主从至少选一个

!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "FileFunc.nsh"

; DO NOT change directory - work from build/
; !cd ".."  ; <-- Remove this line

; Set code page to UTF-8
Unicode true
!define MUI_LANGDLL_ALLLANGUAGES

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

; Component sections
Section "Management Panel (Required)" SecPanel
    SectionIn RO  ; Required, cannot be unchecked
SectionEnd

Section "Master Strategy Engine" SecMaster
    StrCpy $EnableMaster "true"
SectionEnd

Section "Slave Execution Node" SecSlave
    StrCpy $EnableSlave "true"
SectionEnd

Section "System Documentation" SecDeps
SectionEnd

Section "Configuration Templates" SecConfig
    SetOutPath "$INSTDIR\config"

    IfFileExists "..\config\*.*" 0 +3
        File /r "..\config\*.*"
    Goto +2
        CreateDirectory "$INSTDIR\config"

    SetOutPath "$INSTDIR"
SectionEnd

Section "Documents" SecDocs
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
    FileWriteUTF16LE $0 "$\r$\n"
    FileWriteUTF16LE $0 "This system provides intelligent trading strategies.$\r$\n"
    FileWriteUTF16LE $0 "Signals are distributed via MQTT to execution nodes.$\r$\n"
    FileWriteUTF16LE $0 "$\r$\n"
    FileWriteUTF16LE $0 "Installed components:$\r$\n"
    FileWriteUTF16LE $0 "- MT5_Manager.exe  : Management Panel (GUI)$\r$\n"
    
    StrCmp $EnableMaster "true" 0 +2
    FileWriteUTF16LE $0 "- MT5_Master.exe   : Strategy Engine (Master)$\r$\n"
    
    StrCmp $EnableSlave "true" 0 +2
    FileWriteUTF16LE $0 "- MT5_Slave.exe    : Execution Node (Slave)$\r$\n"
    
    FileWriteUTF16LE $0 "$\r$\n"
    FileWriteUTF16LE $0 "Usage:$\r$\n"
    FileWriteUTF16LE $0 "1. Double-click MT5_Manager.exe to start$\r$\n"
    FileWriteUTF16LE $0 "2. Configure strategy parameters$\r$\n"
    FileWriteUTF16LE $0 "3. Click 'Start' to run trading strategies$\r$\n"
    FileWriteUTF16LE $0 "$\r$\n"
    FileWriteUTF16LE $0 "Note: MetaTrader 5 terminal required for execution$\r$\n"
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
SectionEnd

; Descriptions
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SecPanel} "Management Panel - Configuration and Monitoring (Required)"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecMaster} "Strategy Engine - Intelligent trading strategies (Master)"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecSlave} "Execution Node - Signal execution and order management (Slave)"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecDeps} "System documentation"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecConfig} "Configuration templates"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecDocs} "User manual"
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; Validation: at least one of Master/Slave must be selected
Function .onLeaveComponents
    SectionGetFlags ${SecMaster} $R0
    IntOp $R0 $R0 & ${SF_SELECTED}
    
    SectionGetFlags ${SecSlave} $R1
    IntOp $R1 $R1 & ${SF_SELECTED}
    
    IntCmp $R0 0 0 skip_check
    IntCmp $R1 0 0 skip_check
    
    MessageBox MB_ICONEXCLAMATION|MB_OK "Please select at least one: Master or Slave!$\n$\nBoth cannot be unselected."
    Abort
    
    skip_check:
FunctionEnd

Function .onInit
    StrCpy $EnableMaster "false"
    StrCpy $EnableSlave "false"
    
    SectionSetFlags ${SecPanel} ${SF_SELECTED}
    SectionSetFlags ${SecMaster} ${SF_SELECTED}
    SectionSetFlags ${SecSlave} ${SF_SELECTED}
    SectionSetFlags ${SecDeps} ${SF_SELECTED}
    
    !insertmacro MUI_LANGDLL_DISPLAY
FunctionEnd

Function un.onInit
    !insertmacro MUI_UNGETLANGUAGE
    MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 \
        "Are you sure you want to completely uninstall TradeMind MT5?$\n$\nThis will remove all files." \
        IDYES +2
    Abort
FunctionEnd