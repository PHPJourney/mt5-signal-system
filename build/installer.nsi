; MT5 Signal System - Unified Installer
; Supports selecting Master, Slave, or both components

!include "MUI2.nsh"

; General settings
Name "MT5 Signal System"
OutFile "dist\MT5_Signal_System_Installer.exe"
InstallDir "$PROGRAMFILES\MT5SignalSystem"
RequestExecutionLevel admin
ShowInstDetails show
ShowUninstDetails show

; UI settings
!define MUI_ABORTWARNING
!define MUI_ICON ""
!define MUI_UNICON ""
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP ""
!define MUI_WELCOMEFINISHPAGE_BITMAP ""

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

; Component sections
Section "Master Panel (主信号管理面板)" SecMaster
    SectionIn RO  ; Required if selected
    SetOutPath "$INSTDIR"

    ; Copy Master Panel executable
    File "dist\MT5_Master_Panel"
    File "dist\MT5_Master_Panel.app\Contents\MacOS\MT5_Master_Panel"

    ; Create shortcuts
    CreateDirectory "$SMPROGRAMS\MT5 Signal System"
    CreateShortCut "$SMPROGRAMS\MT5 Signal System\Master Panel.lnk" "$INSTDIR\MT5_Master_Panel"
    CreateShortCut "$DESKTOP\MT5 Master Panel.lnk" "$INSTDIR\MT5_Master_Panel"
SectionEnd

Section "Slave Panel (从信号管理面板)" SecSlave
    SetOutPath "$INSTDIR"

    ; Copy Slave Panel executable
    File "dist\MT5_Slave_Panel"
    File "dist\MT5_Slave_Panel.app\Contents\MacOS\MT5_Slave_Panel"

    ; Create shortcuts
    CreateShortCut "$SMPROGRAMS\MT5 Signal System\Slave Panel.lnk" "$INSTDIR\MT5_Slave_Panel"
    CreateShortCut "$DESKTOP\MT5 Slave Panel.lnk" "$INSTDIR\MT5_Slave_Panel"
SectionEnd

Section "Unified Manager (统一管理平台)" SecUnified
    SetOutPath "$INSTDIR"

    ; Copy Unified Manager executable
    File "dist\MT5_Unified_Manager"
    File "dist\MT5_Unified_Manager.app\Contents\MacOS\MT5_Unified_Manager"

    ; Create shortcuts
    CreateShortCut "$SMPROGRAMS\MT5 Signal System\Unified Manager.lnk" "$INSTDIR\MT5_Unified_Manager"
    CreateShortCut "$DESKTOP\MT5 Unified Manager.lnk" "$INSTDIR\MT5_Unified_Manager"
SectionEnd

Section "Configuration Files (配置文件)" SecConfig
    SetOutPath "$INSTDIR\config"

    ; Copy config directory if exists
    IfFileExists "config\*.*" 0 +3
        File /r "config\*.*"
    Goto +2
        ; Create default config directory
        CreateDirectory "$INSTDIR\config"

    SetOutPath "$INSTDIR"
SectionEnd

Section "Documentation (文档)" SecDocs
    SetOutPath "$INSTDIR"

    ; Copy documentation files
    IfFileExists "README.md" 0 +2
        File "README.md"
    IfFileExists "QUICKSTART.md" 0 +2
        File "QUICKSTART.md"
SectionEnd

; Uninstaller section
Section "Uninstall"
    ; Remove installed files
    Delete "$INSTDIR\MT5_Master_Panel"
    Delete "$INSTDIR\MT5_Slave_Panel"
    Delete "$INSTDIR\MT5_Unified_Manager"
    Delete "$INSTDIR\README.md"
    Delete "$INSTDIR\QUICKSTART.md"

    ; Remove shortcuts
    Delete "$SMPROGRAMS\MT5 Signal System\Master Panel.lnk"
    Delete "$SMPROGRAMS\MT5 Signal System\Slave Panel.lnk"
    Delete "$SMPROGRAMS\MT5 Signal System\Unified Manager.lnk"
    Delete "$DESKTOP\MT5 Master Panel.lnk"
    Delete "$DESKTOP\MT5 Slave Panel.lnk"
    Delete "$DESKTOP\MT5 Unified Manager.lnk"

    ; Remove directories
    RMDir "$SMPROGRAMS\MT5 Signal System"
    RMDir /r "$INSTDIR\config"
    RMDir /r "$INSTDIR\logs"
    RMDir "$INSTDIR"
SectionEnd

; Descriptions
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SecMaster} "Master 信号管理面板 - 用于管理和配置主信号服务器"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecSlave} "Slave 信号管理面板 - 用于管理和配置从信号服务器"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecUnified} "统一管理平台 - 集成 Master 和 Slave 的完整管理功能"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecConfig} "配置文件模板和示例"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecDocs} "用户手册和快速入门指南"
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; Custom functions
Function .onInit
    ; Set default selections
    SectionSetFlags ${SecMaster} ${SF_SELECTED}
    SectionSetFlags ${SecUnified} ${SF_SELECTED}
FunctionEnd
