# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from pathlib import Path

block_cipher = None

# Ana dizin
base_dir = Path(os.getcwd()).absolute()

# Data dosyaları (Linux formatı)
datas = [
    ('explorer_icon.ico', '.'),
    ('explorer_icon.png', '.'),
    ('edmrn_3d_minimap.py', '.'),
    ('edmrn_overlay.py', '.'),
    ('edmrn_backup.py', '.'),
    ('edmrn_autosave.py', '.'),
    ('edmrn_platform.py', '.'),
]

# Hidden imports (Linux için)
hiddenimports = [
    'matplotlib.backends.backend_tkagg',
    'mpl_toolkits.mplot3d',
    'matplotlib.backends.backend_tk',
    'pandas._libs.tslibs.timedeltas',
    'pandas._libs.tslibs.base',
    'PIL._tkinter_finder',
    'numpy.core._multiarray_umath',
    'numpy.core._dtype_ctypes',
    'scipy.spatial.ckdtree',
    'scipy.spatial._qhull',
    'scipy.special._ufuncs_cxx',
    'webbrowser',
    'certifi',
    'requests',
    'urllib3',
    'chardet',
    'idna',
    'json',
    'tkinter',
    'queue',
    'threading',
    'typing',
    'dataclasses',
    'concurrent.futures',
    'ctypes',
    'psutil._psutil_posix',
    'tqdm',
    'distro',
    'tkcalendar',
    'python_tsp',
    'python_tsp.distances',
    'python_tsp.heuristics',
]

# Excludes
excludes = [
    'test',
    'unittest',
    'pytest',
    'tkinter.test',
    'matplotlib.tests',
    'numpy.test',
    'pandas.tests',
    'scipy.tests',
    'pillow.tests',
]

# PyInstaller ayarları
a = Analysis(
    ['edmrn_gui.py'],
    pathex=[str(base_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
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
    name='ED_Multi_Route_Navigation_v2.3',
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
    icon='explorer_icon.png',
)
