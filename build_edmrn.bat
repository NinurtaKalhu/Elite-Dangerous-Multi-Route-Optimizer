@echo off
echo Building EDMRN v3.1...
echo.

if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

python -m PyInstaller edmrn.spec --clean --noconfirm

if exist "dist\EDMRN_v3.1.exe" (
    echo.
    echo ✅ Build successful!
    echo EXE location: dist\EDMRN_v3.1.exe
    echo.
    echo File properties will show:
    echo - Product Name: ED Multi Route Navigation (EDMRN)
    echo - Version: 3.1
    echo - Company: Ninurta Kalhu (S.C.)
    echo - Copyright: © 2025-2026 Ninurta Kalhu (S.C.) - AGPL-3 License
    echo.
) else (
    echo ❌ Build failed!
)

pause