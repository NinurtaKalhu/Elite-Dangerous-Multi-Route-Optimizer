#!/usr/bin/env python3
import sys
import os
import subprocess
import platform
from pathlib import Path

def build_windows():
    """Build for Windows"""
    print("Building for Windows...")
    
    spec_file = "build_windows.spec"
    if os.path.exists(spec_file):
        print(f"Using spec file: {spec_file}")
        subprocess.run(["pyinstaller", spec_file], check=True)
    else:
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
    
    print("Windows build complete!")

def build_linux():
    """Build for Linux"""
    print("Building for Linux...")
    
    spec_file = "build_linux.spec"
    if os.path.exists(spec_file):
        print(f"Using spec file: {spec_file}")
        subprocess.run(["pyinstaller", spec_file], check=True)
    else:
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
    
    print("Linux build complete!")

def main():
    print("EDMRN Build System v2.3")
    print("=" * 50)
    
    current_platform = platform.system()
    
    if current_platform == "Windows":
        build_windows()
    elif current_platform == "Linux":
        build_linux()
    elif current_platform == "Darwin":
        print("For macOS, please run build_macos.sh script")
        print("This requires macOS and Xcode command line tools")
    else:
        print(f"Unsupported platform: {current_platform}")
        sys.exit(1)
    
    print("\nBuild completed successfully!")
    print(f"Output in 'dist/' directory")

if __name__ == "__main__":
    main()
