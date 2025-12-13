@echo off
echo Building EDMRN v2.3.0...

python -m venv venv
call venv\Scripts\activate.bat

pip install -r requirements.txt
pip install pyinstaller

pyinstaller --clean --onefile --noconsole ^
  --icon=assets/explorer_icon.ico ^
  --add-data "assets;assets" ^
  --name EDMRN ^
  run.py

echo Build complete! Check dist/ folder.
pause