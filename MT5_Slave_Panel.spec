# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['slave_panel.py'],
    pathex=[],
    binaries=[],
    datas=[('config', 'config'), ('common', 'common'), ('master', 'master'), ('slave', 'slave')],
    hiddenimports=['paho.mqtt.client', 'psutil', 'ttkbootstrap', 'slave.signal_receiver', 'slave.symbol_mapper', 'slave.risk_manager'],
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
    name='MT5_Slave_Panel',
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
    name='MT5_Slave_Panel.app',
    icon=None,
    bundle_identifier=None,
)
