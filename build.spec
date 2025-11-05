# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['edmrn_gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('explorer_icon.png', '.'),
        ('explorer_icon.ico', '.'),
        ('edmrn_3d_minimap.py', '.')
    ],
    hiddenimports=[
        'customtkinter',
        'matplotlib',
        'mpl_toolkits.mplot3d',
        'scipy.spatial._distance_pybind',
        'python_tsp',
        'PIL',
        'requests'
    ],
    hookspath=[],
    hooksconfig={},
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
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ED Multi Route Navigation v2.0',
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
    icon='explorer_icon.ico',
)
