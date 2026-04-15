# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['mt5_unified_manager.py'],
    pathex=[],
    binaries=[],
    datas=[('config', 'config'), ('common', 'common'), ('master', 'master'), ('slave', 'slave')],
    hiddenimports=['paho.mqtt.client', 'psutil', 'ttkbootstrap', 'master.signal_sender', 'master.auth_manager', 'slave.signal_receiver', 'slave.symbol_mapper'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='MT5_Unified_Manager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
app = BUNDLE(
    exe,
    name='MT5_Unified_Manager.app',
    icon=None,
    bundle_identifier=None,
)
