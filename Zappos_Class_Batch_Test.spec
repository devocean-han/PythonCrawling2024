# -*- mode: python ; coding: utf-8 -*-

added_files = [
    ('.env', '.'), 
    ('requirements.txt', '.'), 
    ('python-crawling-gspread-145332f402e3.json', '.'), 
    ('테스트 결과물 샘플\error.log', '.\테스트 결과물 샘플')
]

a = Analysis(
    ['Zappos_Class_Batch_Test.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[],
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
    a.binaries,
    a.datas,
    [],
    name='Zappos_Class_Batch_Test',
    debug=False,
    uac_admin=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
