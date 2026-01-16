# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['../main.py'],
    pathex=['..'],
    binaries=[],
    datas=[('../assets', 'assets'), ('../edmrn/themes', 'edmrn/themes')],
    hiddenimports=[
        'customtkinter',
        'PIL._tkinter_finder',
        'numpy',
        'numpy.core._multiarray_umath',
        'pandas',
        'pandas._libs',
        'pandas._libs.tslibs',
        'pandas._libs.tslibs.offsets',
        'pandas.core.api',
        'matplotlib',
        'matplotlib.backends.backend_tkagg',
        'scipy.optimize',
        'scipy.special',
        'scipy.spatial',
        'python_tsp.heuristics',
        'tqdm',
        'psutil',
        'tkinter',
        'tkinter.filedialog',
        'tkinter.messagebox',
        # pkg_resources dependencies
        'pkg_resources',
        'setuptools',
        'platformdirs',
        'importlib_metadata',
        'importlib_resources',
        'zipp',
        'more_itertools',
        'jaraco',
        'jaraco.text',
        'jaraco.functools',
        'jaraco.context',
        'jaraco.classes'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter.test',
        'doctest',
        'PySide6',
        'PyQt5',
        'PyQt6',
        'wx'
    ],
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
    name='EDMRN_v3.1',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='../assets/explorer_icon.ico',
    version='version_info.txt'
)