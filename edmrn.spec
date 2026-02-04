# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from pathlib import Path

# Get absolute paths
spec_root = os.path.abspath(SPECPATH)
project_root = os.path.dirname(spec_root)

# Find tksheet package location (avoid importing venv packages into build env)
local_tksheet = os.path.join(spec_root, 'tksheet')
venv_root = os.path.join(project_root, '.venv_clean')
venv_site = os.path.join(venv_root, 'Lib', 'site-packages')
venv_tksheet = os.path.join(venv_site, 'tksheet')

if os.path.isdir(local_tksheet):
    tksheet_datas = [(local_tksheet, 'tksheet')]
    print(f"[SPEC] tksheet found in build folder: {local_tksheet}")
elif os.path.isdir(venv_tksheet):
    tksheet_datas = [(venv_tksheet, 'tksheet')]
    print(f"[SPEC] tksheet found via venv path: {venv_tksheet}")
else:
    tksheet_datas = []
    print("[SPEC] WARNING: tksheet not found!")

block_cipher = None

a = Analysis(
    [os.path.join(spec_root, 'main.py')],
    pathex=[spec_root, project_root],
    binaries=[],
    datas=[
        (os.path.join(spec_root, 'assets'), 'assets'), 
        (os.path.join(spec_root, 'edmrn', 'themes'), 'edmrn/themes')
    ] + tksheet_datas,
    hiddenimports=[
        # EDMRN Core modules - ALL modules
        'edmrn',
        'edmrn.app',
        'edmrn.gui',
        'edmrn.system_info_section',
        'edmrn.logger',
        'edmrn.journal',
        'edmrn.journal_operations',
        'edmrn.table_widget',
        'edmrn.column_display_names',
        'edmrn.codex_translation',
        'edmrn.autocomplete_entry',
        'edmrn.edmrn_sheet',
        'edmrn.config',
        'edmrn.utils',
        'edmrn.updater',
        'edmrn.theme_manager',
        'edmrn.theme_editor',
        'edmrn.settings_manager',
        'edmrn.optimizer',
        'edmrn.route_manager',
        'edmrn.route_management',
        'edmrn.tracker',
        'edmrn.splash',
        'edmrn.overlay',
        'edmrn.backup',
        'edmrn.autosave',
        'edmrn.file_operations',
        'edmrn.galaxy_plotter',
        'edmrn.minimap',
        'edmrn.neutron',
        'edmrn.neutron_manager',
        'edmrn.platform',
        'edmrn.platform_detector',
        'edmrn.slef_store',
        'edmrn.system_autocomplete',
        'edmrn.ui_components',
        'edmrn.visit_history',
        'edmrn.visit_history_dialog',
        'edmrn.icons',
        'edmrn.ed_theme',
        'edmrn.exceptions',
        # External modules - CORRECTED
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
        'python_tsp',
        'python_tsp.heuristics',
        'tqdm',
        'psutil',
        'tkinter',
        'tkinter.filedialog',
        'tkinter.messagebox',
        # tksheet - complete package with ALL submodules
        'tksheet',
        'tksheet.colors',
        'tksheet.column_headers',
        'tksheet.constants',
        'tksheet.find_window',
        'tksheet.formatters',
        'tksheet.functions',
        'tksheet.main_table',
        'tksheet.menus',
        'tksheet.other_classes',
        'tksheet.row_index',
        'tksheet.sheet',
        'tksheet.sheet_options',
        'tksheet.sorting',
        'tksheet.text_editor',
        'tksheet.themes',
        'tksheet.tksheet_types',
        'tksheet.tooltip',
        'tksheet.top_left_rectangle',
        'tkinterweb',
        'tkinterweb_tkhtml',
        'requests',
        'bs4',  # FIXED: was beautifulsoup4
        'bs4.builder',
        'bs4.builder._html5lib',
        'bs4.builder._htmlparser',
        'bs4.builder._lxml',
        'soupsieve',
        'pyperclip',
        'webbrowser',
        'json',
        'hashlib',
        'threading',
        'queue',
        'copy',
        're',
        'datetime',
        'collections',
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
    runtime_hooks=[os.path.join(spec_root, 'hook-tksheet.py')],
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
    name='EDMRN_v3.2',
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
    icon=os.path.join(spec_root, 'assets', 'explorer_icon.ico'),
    version=os.path.join(spec_root, 'version_info.txt')
)