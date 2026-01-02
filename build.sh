echo "Building EDMRN v2.3.1..."

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
pip install pyinstaller

if [[ "$OSTYPE" == "darwin"* ]]; then
    pyinstaller --clean --onefile --noconsole \
      --icon=assets/explorer_icon.icns \
      --add-data "assets:assets" \
      --name EDMRN \
      run.py
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    pyinstaller --clean --onefile --noconsole \
      --icon=assets/explorer_icon.png \
      --add-data "assets:assets" \
      --name EDMRN \
      run.py
else
    echo "Unsupported OS"
    exit 1
fi

echo "Build complete! Check dist/ folder."