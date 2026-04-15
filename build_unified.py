"""
MT5 Signal System - Multi-Mode Build Script

Supports building three modes:
- master: Master Server management panel only
- slave: Slave Server management panel only
- unified: Full unified management panel

Each mode produces a separate EXE with only the relevant features.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def check_pyinstaller():
    """Check if PyInstaller is installed"""
    try:
        import PyInstaller
        print("✓ PyInstaller is installed")
        return True
    except ImportError:
        print("✗ PyInstaller not found")
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        return True


def create_mode_spec(mode):
    """Create PyInstaller spec file for a specific mode"""
    mode_info = {
        'master': {
            'entry': 'master_panel.py',
            'name': 'MT5_Master_Panel',
            'desc': 'Master Management Panel'
        },
        'slave': {
            'entry': 'slave_panel.py',
            'name': 'MT5_Slave_Panel',
            'desc': 'Slave Management Panel'
        },
        'unified': {
            'entry': 'mt5_unified_manager.py',
            'name': 'MT5_Unified_Manager',
            'desc': 'Unified Management Panel'
        }
    }

    info = mode_info[mode]

    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
# MT5 {info["desc"]} Spec File

block_cipher = None

a = Analysis(
    ['{info["entry"]}'],
    pathex=[],
    binaries=[],
    datas=[
        ('config', 'config'),
        ('common', 'common'),
        ('master', 'master'),
        ('slave', 'slave'),
    ],
    hiddenimports=[
        'paho.mqtt.client',
        'MetaTrader5',
        'psutil',
        'ttkbootstrap',
        'common',
        'common.models',
        'common.utils',
        'common.mqtt_client',
        'master',
        'master.signal_sender',
        'master.auth_manager',
        'master.mqtt_auth_bridge',
        'slave',
        'slave.signal_receiver',
        'slave.symbol_mapper',
        'slave.risk_manager',
        'slave.authenticated_client',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        'tkinter.test',
        'unittest',
        'test',
        'tests',
    ],
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
    name='{info["name"]}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI application, no console window
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
    name='{info["name"]}',
)
'''

    os.makedirs('build', exist_ok=True)
    spec_path = f'build/{mode}_panel.spec'
    with open(spec_path, 'w', encoding='utf-8') as f:
        f.write(spec_content)

    print(f"✓ Spec file created: {spec_path}")
    return spec_path


def build_mode_exe(mode):
    """Build executable for a specific mode"""
    mode_names = {
        'master': 'Master Panel',
        'slave': 'Slave Panel',
        'unified': 'Unified Manager'
    }

    print(f"\n{'=' * 60}")
    print(f"Building MT5 {mode_names[mode]}...")
    print(f"{'=' * 60}")

    # Create spec file
    spec_path = create_mode_spec(mode)

    try:
        # Run PyInstaller
        result = subprocess.run(
            [sys.executable, '-m', 'PyInstaller', '--clean', spec_path],
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode == 0:
            print(f"\n✓ {mode_names[mode]} build successful!")
            output_dir = Path(f'dist/MT5_{mode.capitalize()}_Panel')
            if output_dir.exists():
                print(f"Output directory: {output_dir.absolute()}")

                # List generated files
                print("\nGenerated files:")
                for root, dirs, files in os.walk(output_dir):
                    level = root.replace(str(output_dir), '').count(os.sep)
                    indent = ' ' * 2 * level
                    print(f'{indent}{os.path.basename(root)}/')
                    subindent = ' ' * 2 * (level + 1)
                    for file in sorted(files):
                        filepath = os.path.join(root, file)
                        size = os.path.getsize(filepath)
                        if size > 1024 * 1024:
                            size_str = f"{size / (1024 * 1024):.1f} MB"
                        elif size > 1024:
                            size_str = f"{size / 1024:.1f} KB"
                        else:
                            size_str = f"{size} B"
                        print(f'{subindent}{file} ({size_str})')
            return True
        else:
            print(f"\n✗ {mode_names[mode]} build failed!")
            print(f"Error output:\n{result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print(f"\n✗ Build timed out (5 minutes)")
        return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False


def create_portable_version(mode):
    """Create a portable version for a specific mode"""
    mode_names = {
        'master': 'Master Panel',
        'slave': 'Slave Panel',
        'unified': 'Unified Manager'
    }
    mode_entries = {
        'master': 'master_panel.py',
        'slave': 'slave_panel.py',
        'unified': 'mt5_unified_manager.py'
    }

    print(f"\nCreating {mode_names[mode]} portable version...")

    release_dir = Path(f'dist/MT5_{mode.capitalize()}_Panel_Portable')
    if release_dir.exists():
        shutil.rmtree(release_dir)
    release_dir.mkdir(parents=True)

    # Copy necessary directories and files
    items_to_copy = [
        mode_entries[mode],
        'mt5_unified_manager.py',
        'master_panel.py',
        'slave_panel.py',
        'config_panel.py',
        'common',
        'master',
        'slave',
        'config',
        'requirements.txt',
        'README.md',
    ]

    for item in items_to_copy:
        src = Path(item)
        dst = release_dir / item

        if src.exists():
            if src.is_dir():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
            print(f"  ✓ Copied: {item}")
        else:
            print(f"  ⚠ Skipped (not found): {item}")

    # Create startup batch file
    bat_content = f"""@echo off
chcp 65001 >nul
title MT5 {mode_names[mode]}
echo ========================================
echo   MT5 Signal System - {mode_names[mode]}
echo ========================================
echo.

if not exist "python.exe" (
    echo Starting with system Python...
    python {mode_entries[mode]}
) else (
    echo Starting with bundled Python...
    .\\python.exe {mode_entries[mode]}
)

pause
"""

    with open(release_dir / f'start_{mode}_panel.bat', 'w', encoding='gbk') as f:
        f.write(bat_content)

    # Create README for portable version
    mode_features = {
        'master': "- Master Server management\n- Master configuration editor\n- Master service control\n- Log viewer",
        'slave': "- Slave Server management\n- Slave configuration editor\n- Trading parameters\n- Symbol mapping\n- Risk management\n- Log viewer",
        'unified': "- Master Server management\n- Slave Server management\n- License management\n- Real-time monitoring\n- Log viewer\n- Configuration editor"
    }

    readme_txt = f"""MT5 {mode_names[mode]} - Portable Version
{'=' * (len(mode_names[mode]) + 22)}

This is the portable version of MT5 {mode_names[mode]}.

Features:
{mode_features[mode]}

Usage:
1. Ensure Python 3.8+ is installed
2. Install dependencies: pip install -r requirements.txt
3. Double-click start_{mode}_panel.bat

Or run directly:
    python {mode_entries[mode]}

Configuration files are stored in: config/
Log files are stored in: logs/

For support, see the main README.md
"""

    with open(release_dir / 'PORTABLE_README.txt', 'w', encoding='utf-8') as f:
        f.write(readme_txt)

    print(f"\n✓ Portable version created: {release_dir.absolute()}")


def main():
    """Main entry point"""
    print("=" * 60)
    print("MT5 Signal System - Multi-Mode Builder")
    print("=" * 60)
    print()

    # Check PyInstaller
    if not check_pyinstaller():
        return

    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)

    # Ask user for mode and build type
    print("\nSelect build mode:")
    print("1. Master Panel (Master management only)")
    print("2. Slave Panel (Slave management only)")
    print("3. Unified Manager (Full features)")
    print("4. All three modes")
    print()

    mode_choice = input("Enter choice (1/2/3/4, default 3): ").strip() or "3"

    modes = []
    if mode_choice == "1":
        modes = ['master']
    elif mode_choice == "2":
        modes = ['slave']
    elif mode_choice == "3":
        modes = ['unified']
    elif mode_choice == "4":
        modes = ['master', 'slave', 'unified']
    else:
        print("Invalid choice")
        return

    print("\nSelect build type:")
    print("1. Single EXE (PyInstaller, recommended for distribution)")
    print("2. Portable version (source code, for development)")
    print("3. Both")
    print()

    build_choice = input("Enter choice (1/2/3, default 1): ").strip() or "1"

    for mode in modes:
        mode_names = {
            'master': 'Master Panel',
            'slave': 'Slave Panel',
            'unified': 'Unified Manager'
        }
        print(f"\n{'#' * 60}")
        print(f"# Building: {mode_names[mode]}")
        print(f"{'#' * 60}")

        if build_choice == "1":
            build_mode_exe(mode)
        elif build_choice == "2":
            create_portable_version(mode)
        elif build_choice == "3":
            if build_mode_exe(mode):
                print("\n" + "-" * 40)
            create_portable_version(mode)

    print("\n" + "=" * 60)
    print("Build complete!")
    print("=" * 60)
    print(f"\nOutput directory: {Path('dist').absolute()}")
    print("\nNext steps:")
    print("1. Test the built application(s)")
    print("2. Distribute to users")
    print("3. See dist/ folder for all outputs")


if __name__ == "__main__":
    main()
