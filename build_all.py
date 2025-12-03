#!/usr/bin/env python3
import sys
import os
import subprocess
import platform
from pathlib import Path

def build_windows():
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name", "ED_Multi_Route_Navigation_v2.3",
        "--icon", "explorer_icon.ico",
        "--add-data", "explorer_icon.ico;.",
        "--add-data", "explorer_icon.png;.",
        "--add-data", "edmrn_3d_minimap.py;.",
        "--add-data", "edmrn_overlay.py;.",
        "--add-data", "edmrn_backup.py;.",
        "--add-data", "edmrn_autosave.py;.",
        "--add-data", "edmrn_platform.py;.",
        "--hidden-import", "matplotlib.backends.backend_tkagg",
        "--hidden-import", "mpl_toolkits.mplot3d",
        "--hidden-import", "pandas._libs.tslibs.timedeltas",
        "--hidden-import", "PIL._tkinter_finder",
        "--hidden-import", "numpy.core._multiarray_umath",
        "--hidden-import", "scipy.spatial.ckdtree",
        "--hidden-import", "webbrowser",
        "--hidden-import", "certifi",
        "--hidden-import", "requests",
        "--hidden-import", "psutil._psutil_windows",
        "--hidden-import", "tqdm",
        "--hidden-import", "python_tsp",
        "--collect-all", "customtkinter",
        "--collect-all", "requests",
        "edmrn_gui.py"
    ]
    subprocess.run(cmd, check=True)

def build_linux():
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name", "ED_Multi_Route_Navigation_v2.3",
        "--icon", "explorer_icon.png",
        "--add-data", "explorer_icon.png:.",
        "--add-data", "explorer_icon.ico:.",
        "--add-data", "edmrn_3d_minimap.py:.",
        "--add-data", "edmrn_overlay.py:.",
        "--add-data", "edmrn_backup.py:.",
        "--add-data", "edmrn_autosave.py:.",
        "--add-data", "edmrn_platform.py:.",
        "--hidden-import", "matplotlib.backends.backend_tkagg",
        "--hidden-import", "mpl_toolkits.mplot3d",
        "--hidden-import", "pandas._libs.tslibs.timedeltas",
        "--hidden-import", "PIL._tkinter_finder",
        "--hidden-import", "numpy.core._multiarray_umath",
        "--hidden-import", "scipy.spatial.ckdtree",
        "--hidden-import", "webbrowser",
        "--hidden-import", "certifi",
        "--hidden-import", "requests",
        "--hidden-import", "psutil._psutil_posix",
        "--hidden-import", "tqdm",
        "--hidden-import", "python_tsp",
        "--collect-all", "customtkinter",
        "--collect-all", "requests",
        "edmrn_gui.py"
    ]
    subprocess.run(cmd, check=True)

def main():
    system = platform.system()
    if system == "Windows":
        build_windows()
    elif system == "Linux":
        build_linux()
    elif system == "Darwin":
        print("macOS build requires build_macos.sh")
        sys.exit(1)
    else:
        print(f"Unsupported platform: {system}")
        sys.exit(1)

if __name__ == "__main__":
    main()
