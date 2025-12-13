import os
import sys
from pathlib import Path

def get_data_files():
    data_files = []
    
    assets_dir = Path("assets")
    if assets_dir.exists():
        for file in assets_dir.glob("*"):
            data_files.append((str(file), "assets"))
    
    return data_files

block_cipher = None

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=get_data_files(),
    hiddenimports=[
        'matplotlib.backends.backend_tkagg',
        'scipy.spatial._qhull',
        'scipy.spatial.transform._rotation_groups',
        'scipy.special._ufuncs_cxx',
        'tqdm',
        'tqdm.cli',
        'PIL',
        'psutil',
        'customtkinter',
        'tkinter',
        'tkinter.ttk',
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

if sys.platform == 'win32':
    a.binaries += [
        ('vcruntime140.dll', 'C:\\Windows\\System32\\vcruntime140.dll', 'BINARY'),
        ('vcruntime140_1.dll', 'C:\\Windows\\System32\\vcruntime140_1.dll', 'BINARY'),
    ]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='EDMRN',
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
    icon='assets/explorer_icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='EDMRN',
)