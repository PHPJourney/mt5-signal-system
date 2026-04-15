"""
MT5 Signal System - 一键打包脚本
同时打包 Master 和 Slave，生成独立的安装包
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


def create_master_spec():
    """创建 Master 的 PyInstaller spec 文件"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-
# MT5 Master Server Spec File

block_cipher = None

a = Analysis(
    ['master/signal_sender.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config/master_config.json', 'config'),
        ('common', 'common'),
        ('master', 'master'),
    ],
    hiddenimports=[
        'paho.mqtt.client',
        'MetaTrader5',
        'common',
        'common.models',
        'common.utils',
        'common.mqtt_client',
        'master',
        'master.auth_manager',
        'master.mqtt_auth_bridge',
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
    name='MT5_Master_Server',
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
    name='MT5_Master_Server',
)
'''

    with open('build/master.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)


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


def build_exe(component):
    """构建可执行文件"""
    print(f"\n开始构建 {component} 可执行文件...")
    print("=" * 60)

    try:
        # 运行PyInstaller
        subprocess.check_call([
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            f'build/{component}.spec'
        ])

        print(f"\n✓ {component} 构建成功!")
        print(f"输出目录: {os.path.abspath(f'dist/MT5_{component.capitalize()}_Server')}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"\n✗ {component} 构建失败: {e}")
        return False
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        return False


def create_portable(component):
    """创建便携版"""
    print(f"\n创建 {component} 便携版...")

    release_dir = f'dist/MT5_{component.capitalize()}_Portable'
    if os.path.exists(release_dir):
        shutil.rmtree(release_dir)
    os.makedirs(release_dir)

    # 复制必要文件
    files_to_copy = [
        (f'config/{component}_config.json', f'config/{component}_config.json'),
        ('common', 'common'),
        (component, component),
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
    bat_content = f"""@echo off
chcp 65001 >nul
title MT5 {component.capitalize()} Server
echo ========================================
echo   MT5 Signal System - {component.capitalize()} Server
echo ========================================
echo.

if not exist "config\\\\{component}_config.json" (
    echo ERROR: Config file not found: config\\\\{component}_config.json
    pause
    exit /b 1
)

echo Starting {component.capitalize()} Server...
echo.

python {component}\\\\signal_{"sender" if component == "master" else "receiver"}.py --config config\\\\{component}_config.json

pause
"""

    with open(os.path.join(release_dir, f'start_{component}.bat'), 'w', encoding='gbk') as f:
        f.write(bat_content)

    # 创建使用说明
    readme_txt = f"""MT5 {component.capitalize()} Server - 便携版
================================

使用方法:
1. 确保已安装 Python 3.8+
2. 安装依赖: pip install -r requirements.txt
3. 编辑 config/{component}_config.json 配置参数
4. 双击 start_{component}.bat 启动服务

配置文件:
- config/{component}_config.json: {component.capitalize()} 服务器配置

日志文件:
- logs/{component}.log: 运行日志

技术支持:
如有问题请查看 README.md
"""

    with open(os.path.join(release_dir, '使用说明.txt'), 'w', encoding='utf-8') as f:
        f.write(readme_txt)

    print(f"✓ {component.capitalize()} 便携版已创建: {os.path.abspath(release_dir)}")


def create_installer_nsis(component):
    """创建 NSIS 安装脚本"""
    print(f"\n创建 {component.capitalize()} NSIS 安装脚本...")

    nsis_script = f"""; MT5 {component.capitalize()} Server Installer Script
!include "MUI2.nsh"

Name "MT5 {component.capitalize()} Server"
OutFile "dist/MT5_{component.capitalize()}_Server_Installer.exe"
InstallDir "$PROGRAMFILES\\\\MT5{component.capitalize()}Server"
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
    File /r "dist\\MT5_{component.capitalize()}_Portable\\*.*"

    ; 创建开始菜单快捷方式
    CreateDirectory "$SMPROGRAMS\\\\MT5 {component.capitalize()} Server"
    CreateShortCut "$SMPROGRAMS\\\\MT5 {component.capitalize()} Server\\\\{component.capitalize()} Server.lnk" "$INSTDIR\\\\start_{component}.bat"
    CreateShortCut "$SMPROGRAMS\\\\MT5 {component.capitalize()} Server\\\\卸载.lnk" "$INSTDIR\\\\uninstall.exe"

    ; 创建桌面快捷方式
    CreateShortCut "$DESKTOP\\\\MT5 {component.capitalize()} Server.lnk" "$INSTDIR\\\\start_{component}.bat"

    ; 写入注册表
    WriteUninstaller "$INSTDIR\\\\uninstall.exe"
    WriteRegStr HKLM "Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\MT5{component.capitalize()}Server" "DisplayName" "MT5 {component.capitalize()} Server"
    WriteRegStr HKLM "Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\MT5{component.capitalize()}Server" "UninstallString" "$INSTDIR\\\\uninstall.exe"
    WriteRegStr HKLM "Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\MT5{component.capitalize()}Server" "DisplayIcon" "$INSTDIR\\\\start_{component}.bat"
    WriteRegStr HKLM "Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\MT5{component.capitalize()}Server" "Publisher" "MT5 Signal System"
SectionEnd

Section "Uninstall"
    RMDir /r "$INSTDIR"
    RMDir /r "$SMPROGRAMS\\\\MT5 {component.capitalize()} Server"
    Delete "$DESKTOP\\\\MT5 {component.capitalize()} Server.lnk"
    DeleteRegKey HKLM "Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\MT5{component.capitalize()}Server"
SectionEnd
"""

    with open(f'build/{component}_installer.nsi', 'w', encoding='utf-8') as f:
        f.write(nsis_script)

    print(f"✓ {component.capitalize()} NSIS 安装脚本已创建: build/{component}_installer.nsi")


def create_readme():
    """创建发布说明"""
    readme = """MT5 Signal System - 发布包说明
================================

本目录包含 MT5 Signal System 的独立安装包：

📦 可用版本
-----------

1. MT5_Master_Portable/
   - Master Server 便携版
   - 无需安装，解压即用
   - 适合开发测试环境

2. MT5_Slave_Portable/
   - Slave Server 便携版
   - 无需安装，解压即用
   - 适合开发测试环境

3. MT5_Master_Server_Installer.exe (需要编译 NSIS)
   - Master Server 安装程序
   - 自动创建快捷方式
   - 支持标准 Windows 卸载

4. MT5_Slave_Server_Installer.exe (需要编译 NSIS)
   - Slave Server 安装程序
   - 自动创建快捷方式
   - 支持标准 Windows 卸载

🚀 快速开始
-----------

便携版使用步骤:
1. 解压到目标目录
2. 确保已安装 Python 3.8+
3. 安装依赖: pip install -r requirements.txt
4. 编辑配置文件 (config/*.json)
5. 双击 start_*.bat 启动服务

安装版使用步骤:
1. 双击 Installer.exe
2. 选择安装路径
3. 完成安装后从开始菜单或桌面启动

⚙️ 配置说明
-----------

Master 配置: config/master_config.json
- MQTT Broker 地址
- Master MT5 账户信息
- 信号发送参数

Slave 配置: config/slave_config.json
- MQTT Broker 地址
- Slave MT5 账户信息
- 订阅的 Master ID
- 风险管理参数

📝 注意事项
-----------

1. Master 和 Slave 可以部署在不同机器上
2. 确保 MQTT Broker 可访问
3. 首次运行前必须配置正确的 MT5 账户
4. 建议先测试便携版，确认无误后再使用安装版

🔧 技术支持
-----------

详细文档请查看项目根目录的:
- README.md
- QUICKSTART.md
- ARCHITECTURE.md

如遇问题请查看日志文件: logs/*.log
"""

    with open('dist/发布说明.txt', 'w', encoding='utf-8') as f:
        f.write(readme)


def main():
    """主函数"""
    print("=" * 60)
    print("MT5 Signal System - 一键打包工具")
    print("=" * 60)
    print()

    # 检查 PyInstaller
    if not check_pyinstaller():
        return

    # 确保 build 目录存在
    os.makedirs('build', exist_ok=True)
    os.makedirs('dist', exist_ok=True)

    # 创建 spec 文件
    print("\n创建打包配置...")
    create_master_spec()
    create_slave_spec()
    print("✓ 打包配置创建完成")

    # 询问用户选择打包方式
    print("\n请选择打包方式:")
    print("1. 仅创建便携版 (推荐，无需编译，跨平台)")
    print("2. 创建 PyInstaller 可执行文件 (Windows 专用)")
    print("3. 两者都创建 + NSIS 安装脚本")
    print("4. 统一管理平台 (Unified Manager - 单一 EXE)")
    print()

    choice = input("请输入选项 (1/2/3/4, 默认1): ").strip() or "1"

    if choice == "1":
        # 仅便携版
        create_portable('master')
        create_portable('slave')

    elif choice == "2":
        # PyInstaller + 便携版
        print("\n开始构建 Master...")
        if build_exe('master'):
            create_portable('master')

        print("\n开始构建 Slave...")
        if build_exe('slave'):
            create_portable('slave')

    elif choice == "3":
        # 全部
        print("\n开始构建 Master...")
        if build_exe('master'):
            create_portable('master')
            create_installer_nsis('master')

        print("\n开始构建 Slave...")
        if build_exe('slave'):
            create_portable('slave')
            create_installer_nsis('slave')

        print("\n" + "=" * 60)
        print("NSIS 安装程序编译说明:")
        print("=" * 60)
        print("\n如需编译 NSIS 安装程序，请运行:")
        print("  makensis build/master_installer.nsi")
        print("  makensis build/slave_installer.nsi")
        print("\nNSIS 下载地址: https://nsis.sourceforge.io/Download")

    elif choice == "4":
        # 统一管理平台
        print("\n构建统一管理平台...")
        try:
            subprocess.check_call([sys.executable, 'build_unified.py'])
        except subprocess.CalledProcessError as e:
            print(f"\n✗ 统一管理平台构建失败: {e}")
        except Exception as e:
            print(f"\n✗ 错误: {e}")

    else:
        print("无效选项")
        return

    # 创建发布说明
    create_readme()

    print("\n" + "=" * 60)
    print("打包完成!")
    print("=" * 60)
    print(f"\n发布目录: {os.path.abspath('dist')}")
    print("\n生成的文件:")

    # 列出生成的文件
    for root, dirs, files in os.walk('dist'):
        level = root.replace('dist', '').count(os.sep)
        indent = ' ' * 2 * level
        print(f'{indent}{os.path.basename(root)}/')
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            filepath = os.path.join(root, file)
            size = os.path.getsize(filepath)
            if size > 1024 * 1024:
                size_str = f"{size / (1024 * 1024):.1f} MB"
            elif size > 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size} B"
            print(f'{subindent}{file} ({size_str})')

    print("\n下一步:")
    print("1. 测试生成的程序")
    print("2. 分发 portable 版本或编译 installer")
    print("3. 查看 dist/发布说明.txt 了解详细信息")


if __name__ == "__main__":
    main()
