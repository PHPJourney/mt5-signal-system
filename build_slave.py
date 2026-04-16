"""
TradeMind MT5 - Slave 独立打包脚本
生成 Slave Server 的独立可执行文件和安装包
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


def create_slave_spec():
    """创建 Slave 的 PyInstaller spec 文件"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-
# MT5 Slave Server Spec File

block_cipher = None

a = Analysis(
    ['slave/signal_receiver.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config/slave_config.json', 'config'),
        ('common', 'common'),
        ('slave', 'slave'),
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
        'slave.authenticated_client',
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

exe = EXE(
    pyz,
    a.scripts[0],
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
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MT5_Slave_Server',
)
'''

    with open('build/slave.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)

    print("✓ 已创建 Slave spec 文件")


def build_slave_exe():
    """构建 Slave 可执行文件"""
    print("\n开始构建 Slave 可执行文件...")
    print("=" * 60)

    # 确保 build 目录存在
    os.makedirs('build', exist_ok=True)

    try:
        # 清理旧的构建
        if os.path.exists('build/temp'):
            shutil.rmtree('build/temp')

        # 运行PyInstaller
        subprocess.check_call([
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            'build/slave.spec'
        ])

        print("\n✓ Slave 构建成功!")
        print(f"输出目录: {os.path.abspath('dist/MT5_Slave_Server')}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"\n✗ 构建失败: {e}")
        return False
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        return False


def create_slave_portable():
    """创建 Slave 便携版"""
    print("\n创建 Slave 便携版...")

    release_dir = 'dist/MT5_Slave_Portable'
    if os.path.exists(release_dir):
        shutil.rmtree(release_dir)
    os.makedirs(release_dir)

    # 复制必要文件
    files_to_copy = [
        ('config/slave_config.json', 'config/slave_config.json'),
        ('common', 'common'),
        ('slave', 'slave'),
        ('README.md', 'README.md'),
        ('requirements.txt', 'requirements.txt'),
    ]

    for src, dst in files_to_copy:
        full_dst = os.path.join(release_dir, dst)
        if os.path.isdir(src):
            if os.path.exists(full_dst):
                shutil.rmtree(full_dst)
            shutil.copytree(src, full_dst)
        else:
            os.makedirs(os.path.dirname(full_dst), exist_ok=True)
            shutil.copy2(src, full_dst)

    # 创建启动脚本
    slave_bat = """@echo off
chcp 65001 >nul
title MT5 Slave Server
echo ========================================
echo   TradeMind MT5 - Slave Server
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

    with open(os.path.join(release_dir, 'start_slave.bat'), 'w', encoding='gbk') as f:
        f.write(slave_bat)

    # 创建使用说明
    readme_txt = """MT5 Slave Server - 便携版
================================

使用方法:
1. 确保已安装 Python 3.8+
2. 安装依赖: pip install -r requirements.txt
3. 编辑 config/slave_config.json 配置参数
4. 双击 start_slave.bat 启动服务

配置文件:
- config/slave_config.json: Slave 服务器配置

日志文件:
- logs/slave.log: 运行日志

技术支持:
如有问题请查看 README.md
"""

    with open(os.path.join(release_dir, '使用说明.txt'), 'w', encoding='utf-8') as f:
        f.write(readme_txt)

    print(f"✓ Slave 便携版已创建: {os.path.abspath(release_dir)}")


def create_slave_installer_nsis():
    """创建 Slave 的 NSIS 安装脚本"""
    print("\n创建 Slave NSIS 安装脚本...")

    nsis_script = """; MT5 Slave Server Installer Script
!include "MUI2.nsh"

Name "MT5 Slave Server"
OutFile "dist/MT5_Slave_Server_Installer.exe"
InstallDir "$PROGRAMFILES\\\\MT5SlaveServer"
RequestExecutionLevel admin

!define MUI_ABORTWARNING
!define MUI_ICON ""
!define MUI_UNICON ""

Page directory
Page instfiles
UninstPage uninstConfirm
UninstPage instfiles

!insertmacro MUI_LANGUAGE "SimpChinese"

Section "MainSection" SEC01
    SetOutPath "$INSTDIR"

    ; 复制所有文件
    File /r "dist\\MT5_Slave_Portable\\*.*"

    ; 创建开始菜单快捷方式
    CreateDirectory "$SMPROGRAMS\\\\MT5 Slave Server"
    CreateShortCut "$SMPROGRAMS\\\\MT5 Slave Server\\\\Slave Server.lnk" "$INSTDIR\\\\start_slave.bat"
    CreateShortCut "$SMPROGRAMS\\\\MT5 Slave Server\\\\卸载.lnk" "$INSTDIR\\\\uninstall.exe"

    ; 创建桌面快捷方式
    CreateShortCut "$DESKTOP\\\\MT5 Slave Server.lnk" "$INSTDIR\\\\start_slave.bat"

    ; 写入注册表
    WriteUninstaller "$INSTDIR\\\\uninstall.exe"
    WriteRegStr HKLM "Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\MT5SlaveServer" "DisplayName" "MT5 Slave Server"
    WriteRegStr HKLM "Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\MT5SlaveServer" "UninstallString" "$INSTDIR\\\\uninstall.exe"
    WriteRegStr HKLM "Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\MT5SlaveServer" "DisplayIcon" "$INSTDIR\\\\start_slave.bat"
    WriteRegStr HKLM "Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\MT5SlaveServer" "Publisher" "TradeMind MT5"
SectionEnd

Section "Uninstall"
    RMDir /r "$INSTDIR"
    RMDir /r "$SMPROGRAMS\\\\MT5 Slave Server"
    Delete "$DESKTOP\\\\MT5 Slave Server.lnk"
    DeleteRegKey HKLM "Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\MT5SlaveServer"
SectionEnd
"""

    with open('build/slave_installer.nsi', 'w', encoding='utf-8') as f:
        f.write(nsis_script)

    print("✓ Slave NSIS 安装脚本已创建: build/slave_installer.nsi")
    print("注意: 需要安装 NSIS 才能编译安装程序")
    print("下载地址: https://nsis.sourceforge.io/Download")


def main():
    """主函数"""
    print("=" * 60)
    print("MT5 Slave Server - 打包工具")
    print("=" * 60)
    print()

    # 检查 PyInstaller
    if not check_pyinstaller():
        return

    # 创建 spec 文件
    create_slave_spec()

    # 询问用户选择打包方式
    print("\n请选择打包方式:")
    print("1. 仅创建便携版 (推荐，无需编译)")
    print("2. 创建 PyInstaller 可执行文件")
    print("3. 两者都创建 + 安装脚本")
    print()

    choice = input("请输入选项 (1/2/3, 默认1): ").strip() or "1"

    if choice == "1":
        create_slave_portable()
    elif choice == "2":
        if build_slave_exe():
            create_slave_portable()
    elif choice == "3":
        if build_slave_exe():
            create_slave_portable()
            create_slave_installer_nsis()
            print("\n如需编译 NSIS 安装程序，请运行:")
            print("makensis build/slave_installer.nsi")
    else:
        print("无效选项")
        return

    print("\n" + "=" * 60)
    print("Slave 打包完成!")
    print("=" * 60)
    print(f"\n发布目录: {os.path.abspath('dist')}")
    print("\n下一步:")
    print("1. 测试生成的程序")
    print("2. 分发 portable 版本或 installer")


if __name__ == "__main__":
    main()
