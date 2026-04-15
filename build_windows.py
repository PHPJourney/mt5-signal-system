"""
Windows Packaging Script for MT5 Signal System
Creates standalone executable using PyInstaller
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def check_pyinstaller():
    """检查是否安装了PyInstaller"""
    try:
        import PyInstaller
        print("✓ PyInstaller 已安装")
        return True
    except ImportError:
        print("✗ PyInstaller 未安装")
        print("正在安装 PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        return True


def create_spec_file():
    """创建PyInstaller spec文件"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['master/signal_sender.py', 'slave/signal_receiver.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config', 'config'),
        ('README.md', '.'),
        ('QUICKSTART.md', '.'),
    ],
    hiddenimports=[
        'paho.mqtt.client',
        'MetaTrader5',
        'common',
        'common.models',
        'common.utils',
        'common.mqtt_client',
        'slave',
        'slave.symbol_mapper',
        'slave.risk_manager',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe_master = EXE(
    pyz,
    a.scripts[0],
    [],
    exclude_binaries=True,
    name='MT5_Master_Server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon=None,
)

exe_slave = EXE(
    pyz,
    a.scripts[1],
    [],
    exclude_binaries=True,
    name='MT5_Slave_Server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon=None,
)

coll = COLLECT(
    exe_master,
    exe_slave,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MT5_Signal_System',
)
'''

    with open('mt5_signal.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)

    print("✓ 已创建 spec 文件")


def build_executable():
    """构建可执行文件"""
    print("\n开始构建可执行文件...")
    print("=" * 60)

    try:
        # 清理旧的构建
        if os.path.exists('build'):
            shutil.rmtree('build')
        if os.path.exists('dist'):
            shutil.rmtree('dist')

        # 运行PyInstaller
        subprocess.check_call([
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            'mt5_signal.spec'
        ])

        print("\n✓ 构建成功!")
        print(f"输出目录: {os.path.abspath('dist/MT5_Signal_System')}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"\n✗ 构建失败: {e}")
        return False
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        return False


def create_portable_package():
    """创建便携版安装包"""
    print("\n创建便携版安装包...")

    # 创建发布目录
    release_dir = 'dist/MT5_Signal_System_Portable'
    if os.path.exists(release_dir):
        shutil.rmtree(release_dir)
    os.makedirs(release_dir)

    # 复制必要文件
    files_to_copy = [
        'config',
        'README.md',
        'QUICKSTART.md',
        'ARCHITECTURE.md',
        'requirements.txt',
    ]

    for item in files_to_copy:
        src = item
        dst = os.path.join(release_dir, item)
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)

    # 创建启动脚本
    create_windows_launchers(release_dir)

    print(f"✓ 便携版已创建: {os.path.abspath(release_dir)}")


def create_windows_launchers(target_dir):
    """创建Windows启动脚本"""

    # 主服务器启动脚本
    master_bat = """@echo off
chcp 65001 >nul
title MT5 Signal System - Master Server
echo ========================================
echo   MT5 Signal System - Master Server
echo ========================================
echo.

if not exist "config\\master_config.json" (
    echo ERROR: Config file not found: config\\master_config.json
    pause
    exit /b 1
)

echo Starting Master Server...
echo.

python master\\signal_sender.py --config config\\master_config.json

pause
"""

    # 从服务器启动脚本
    slave_bat = """@echo off
chcp 65001 >nul
title MT5 Signal System - Slave Server
echo ========================================
echo   MT5 Signal System - Slave Server
echo ========================================
echo.

if not exist "config\\slave_config.json" (
    echo ERROR: Config file not found: config\\slave_config.json
    pause
    exit /b 1
)

echo Starting Slave Server...
echo.

python slave\\signal_receiver.py --config config\\slave_config.json

pause
"""

    # 配置面板启动脚本
    config_bat = """@echo off
chcp 65001 >nul
title MT5 Signal System - Configuration Panel
echo ========================================
echo   MT5 Configuration Panel
echo ========================================
echo.

python config_panel.py

pause
"""

    with open(os.path.join(target_dir, 'start_master.bat'), 'w', encoding='gbk') as f:
        f.write(master_bat)

    with open(os.path.join(target_dir, 'start_slave.bat'), 'w', encoding='gbk') as f:
        f.write(slave_bat)

    with open(os.path.join(target_dir, 'config_panel.bat'), 'w', encoding='gbk') as f:
        f.write(config_bat)


def create_installer():
    """创建Windows安装程序"""
    print("\n创建Windows安装程序...")

    # 创建NSIS脚本
    nsis_script = """
!include "MUI2.nsh"

Name "MT5 Signal System"
OutFile "MT5_Signal_System_Installer.exe"
InstallDir "$PROGRAMFILES\\MT5SignalSystem"
RequestExecutionLevel admin

!define MUI_ABORTWARNING
!define MUI_ICON ""

Page directory
Page instfiles

!insertmacro MUI_LANGUAGE "SimpChinese"

Section "MainSection" SEC01
    SetOutPath "$INSTDIR"

    File /r "dist\\MT5_Signal_System_Portable\\*.*"

    CreateDirectory "$SMPROGRAMS\\MT5 Signal System"
    CreateShortCut "$SMPROGRAMS\\MT5 Signal System\\Master Server.lnk" "$INSTDIR\\start_master.bat"
    CreateShortCut "$SMPROGRAMS\\MT5 Signal System\\Slave Server.lnk" "$INSTDIR\\start_slave.bat"
    CreateShortCut "$SMPROGRAMS\\MT5 Signal System\\Configuration Panel.lnk" "$INSTDIR\\config_panel.bat"
    CreateShortCut "$DESKTOP\\MT5 Master Server.lnk" "$INSTDIR\\start_master.bat"
    CreateShortCut "$DESKTOP\\MT5 Slave Server.lnk" "$INSTDIR\\start_slave.bat"

    WriteUninstaller "$INSTDIR\\uninstall.exe"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\MT5SignalSystem" "DisplayName" "MT5 Signal System"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\MT5SignalSystem" "UninstallString" "$INSTDIR\\uninstall.exe"
SectionEnd

Section "Uninstall"
    RMDir /r "$INSTDIR"
    RMDir /r "$SMPROGRAMS\\MT5 Signal System"
    Delete "$DESKTOP\\MT5 Master Server.lnk"
    Delete "$DESKTOP\\MT5 Slave Server.lnk"
    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\MT5SignalSystem"
SectionEnd
"""

    with open('installer.nsi', 'w', encoding='utf-8') as f:
        f.write(nsis_script)

    print("✓ NSIS安装脚本已创建: installer.nsi")
    print("注意: 需要安装NSIS才能编译安装程序")
    print("下载地址: https://nsis.sourceforge.io/Download")


def main():
    """主函数"""
    print("=" * 60)
    print("MT5 Signal System - Windows Packaging Tool")
    print("=" * 60)
    print()

    # 检查PyInstaller
    if not check_pyinstaller():
        return

    # 创建spec文件
    create_spec_file()

    # 询问用户选择打包方式
    print("\n请选择打包方式:")
    print("1. 仅创建便携版 (推荐)")
    print("2. 创建PyInstaller可执行文件")
    print("3. 两者都创建")
    print()

    choice = input("请输入选项 (1/2/3, 默认1): ").strip() or "1"

    if choice == "1":
        create_portable_package()
    elif choice == "2":
        if build_executable():
            create_portable_package()
    elif choice == "3":
        if build_executable():
            create_portable_package()
            create_installer()
    else:
        print("无效选项")
        return

    print("\n" + "=" * 60)
    print("打包完成!")
    print("=" * 60)
    print(f"\n发布目录: {os.path.abspath('dist')}")
    print("\n下一步:")
    print("1. 测试生成的程序")
    print("2. 根据需要调整配置")
    print("3. 分发给用户")


if __name__ == "__main__":
    main()
