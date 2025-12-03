#!/bin/bash

# EDMRN Linux Build Script
# Usage: ./build_linux.sh [--onefile|--onedir]

BUILD_TYPE=${1:-"--onefile"}
APP_NAME="ED_Multi_Route_Navigation"
ICON_PATH="explorer_icon.png"
MAIN_FILE="edmrn_gui.py"

echo "Building EDMRN for Linux..."

echo "Checking Python dependencies..."
pip install -r requirements.txt

if [ "$BUILD_TYPE" == "--onedir" ]; then
    echo "Building as directory..."
    pyinstaller \
        --name "$APP_NAME" \
        --icon "$ICON_PATH" \
        --windowed \
        --onedir \
        --add-data "explorer_icon.png:." \
        --add-data "explorer_icon.ico:." \
        --add-data "edmrn_3d_minimap.py:." \
        --add-data "edmrn_overlay.py:." \
        --add-data "edmrn_backup.py:." \
        --add-data "edmrn_autosave.py:." \
        --add-data "edmrn_platform.py:." \
        --hidden-import "matplotlib.backends.backend_tkagg" \
        --hidden-import "mpl_toolkits.mplot3d" \
        --hidden-import "matplotlib.backends.backend_tk" \
        --hidden-import "pandas._libs.tslibs.timedeltas" \
        --hidden-import "PIL._tkinter_finder" \
        --hidden-import "numpy.core._multiarray_umath" \
        --hidden-import "scipy.spatial.ckdtree" \
        --hidden-import "scipy.spatial._qhull" \
        --hidden-import "webbrowser" \
        --hidden-import "certifi" \
        --hidden-import "requests" \
        --hidden-import "urllib3" \
        --hidden-import "psutil._psutil_posix" \
        --collect-all "customtkinter" \
        --collect-all "requests" \
        --clean \
        "$MAIN_FILE"
else
    echo "Building as single executable..."
    pyinstaller \
        --name "$APP_NAME" \
        --icon "$ICON_PATH" \
        --windowed \
        --onefile \
        --add-data "explorer_icon.png:." \
        --add-data "explorer_icon.ico:." \
        --add-data "edmrn_3d_minimap.py:." \
        --add-data "edmrn_overlay.py:." \
        --add-data "edmrn_backup.py:." \
        --add-data "edmrn_autosave.py:." \
        --add-data "edmrn_platform.py:." \
        --hidden-import "matplotlib.backends.backend_tkagg" \
        --hidden-import "mpl_toolkits.mplot3d" \
        --hidden-import "matplotlib.backends.backend_tk" \
        --hidden-import "pandas._libs.tslibs.timedeltas" \
        --hidden-import "PIL._tkinter_finder" \
        --hidden-import "numpy.core._multiarray_umath" \
        --hidden-import "scipy.spatial.ckdtree" \
        --hidden-import "scipy.spatial._qhull" \
        --hidden-import "webbrowser" \
        --hidden-import "certifi" \
        --hidden-import "requests" \
        --hidden-import "urllib3" \
        --hidden-import "psutil._psutil_posix" \
        --collect-all "customtkinter" \
        --collect-all "requests" \
        --clean \
        "$MAIN_FILE"
fi

echo "Build complete! Executable is in dist/ folder"
echo "To run: ./dist/$APP_NAME"
