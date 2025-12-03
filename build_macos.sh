#!/bin/bash

# EDMRN macOS Build Script
# Note: Must be run on macOS with Xcode command line tools installed

APP_NAME="ED_Multi_Route_Navigation"
APP_BUNDLE="${APP_NAME}.app"
ICON_PATH="explorer_icon.icns"
MAIN_FILE="edmrn_gui.py"

if [ ! -f "$ICON_PATH" ]; then
    echo "Creating macOS icon file..."
    mkdir "${APP_NAME}.iconset"
    sips -z 16 16 explorer_icon.png --out "${APP_NAME}.iconset/icon_16x16.png"
    sips -z 32 32 explorer_icon.png --out "${APP_NAME}.iconset/icon_16x16@2x.png"
    sips -z 32 32 explorer_icon.png --out "${APP_NAME}.iconset/icon_32x32.png"
    sips -z 64 64 explorer_icon.png --out "${APP_NAME}.iconset/icon_32x32@2x.png"
    sips -z 128 128 explorer_icon.png --out "${APP_NAME}.iconset/icon_128x128.png"
    sips -z 256 256 explorer_icon.png --out "${APP_NAME}.iconset/icon_128x128@2x.png"
    sips -z 256 256 explorer_icon.png --out "${APP_NAME}.iconset/icon_256x256.png"
    sips -z 512 512 explorer_icon.png --out "${APP_NAME}.iconset/icon_256x256@2x.png"
    sips -z 512 512 explorer_icon.png --out "${APP_NAME}.iconset/icon_512x512.png"
    sips -z 1024 1024 explorer_icon.png --out "${APP_NAME}.iconset/icon_512x512@2x.png"
    iconutil -c icns "${APP_NAME}.iconset" -o "$ICON_PATH"
    rm -rf "${APP_NAME}.iconset"
fi

echo "Building EDMRN for macOS..."

pyinstaller \
    --name "$APP_NAME" \
    --icon "$ICON_PATH" \
    --windowed \
    --onedir \
    --osx-bundle-identifier "com.ninurtakalhu.edmrn" \
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

echo "Build complete! App bundle created in dist/$APP_BUNDLE"
echo "You may need to codesign the app for distribution:"
echo "  codesign --deep --force --verify --verbose --sign \"Developer ID Application: Your Name\" \"dist/$APP_BUNDLE\""
