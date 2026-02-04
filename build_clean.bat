@echo off
echo ================================================
echo EDMRN v3.2 Clean Build Script
echo ================================================
echo.

cd /d "%~dp0"

echo [1/4] Cleaning previous build artifacts...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "*.log" del /q "*.log"
echo     Done.
echo.

echo [2/4] Verifying files...
if not exist "main.py" (
    echo ERROR: main.py not found!
    pause
    exit /b 1
)
if not exist "edmrn.spec" (
    echo ERROR: edmrn.spec not found!
    pause
    exit /b 1
)
if not exist "assets\explorer_icon.ico" (
    echo ERROR: Icon file not found!
    pause
    exit /b 1
)
echo     All required files present.
echo.

echo [3/4] Building EXE with PyInstaller...
python -m PyInstaller edmrn.spec --noconfirm --log-level=WARN
if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b 1
)
echo.

echo [4/4] Verifying output...
if exist "dist\EDMRN_v3.2.exe" (
    echo.
    echo ================================================
    echo BUILD SUCCESSFUL!
    echo ================================================
    echo.
    dir /b "dist\EDMRN_v3.2.exe"
    for %%A in ("dist\EDMRN_v3.2.exe") do echo Size: %%~zA bytes
    echo.
    echo EXE location: %CD%\dist\EDMRN_v3.2.exe
    echo.
) else (
    echo ERROR: EXE file was not created!
    pause
    exit /b 1
)

echo Build process completed.
echo.
pause
