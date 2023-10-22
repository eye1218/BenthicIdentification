# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main_window.py'],
    pathex=[r'D:\ProgramData\miniconda3\envs\ai\Lib\site-packages'],
    binaries=[],
    datas=[('resources', 'resources')],
    hiddenimports=['openpyxl', 'image_utils'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='benthic_identification',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='benthic_identification',
)
