# PyInstaller runtime hook for tksheet
import sys
import os

# Add tksheet to sys.path at runtime
if getattr(sys, 'frozen', False):
    # Running in PyInstaller bundle
    bundle_dir = sys._MEIPASS
    tksheet_path = os.path.join(bundle_dir, 'tksheet')
    if os.path.exists(tksheet_path) and tksheet_path not in sys.path:
        sys.path.insert(0, os.path.dirname(tksheet_path))
        print(f"[HOOK] Added tksheet to sys.path: {tksheet_path}")
