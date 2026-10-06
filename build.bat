@echo off
echo =============================================
echo   Building ERP Pharmacy Application
echo =============================================
echo.

echo [1/4] Installing PyInstaller...
pip install pyinstaller
if errorlevel 1 (
    echo ERROR: pip failed. Check your internet connection.
    pause
    exit /b 1
)

echo.
echo [2/4] Generating app icon...
python save_icon.py

echo.
echo [3/4] Building executable with PyInstaller...
python -m PyInstaller --noconfirm ErpPharmacy.spec
if errorlevel 1 (
    echo ERROR: PyInstaller failed. See messages above.
    pause
    exit /b 1
)

echo.
if not exist dist\ErpPharmacy\ErpPharmacy.exe (
    echo ERROR: dist\ErpPharmacy\ErpPharmacy.exe not found after build.
    pause
    exit /b 1
)

echo [4/4] Building installer with Inno Setup...

set ISCC=
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe
if exist "C:\Program Files\Inno Setup 6\ISCC.exe"       set ISCC=C:\Program Files\Inno Setup 6\ISCC.exe

if "%ISCC%"=="" (
    echo.
    echo WARNING: Inno Setup 6 not found.
    echo Download from: https://jrsoftware.org/isdl.php
    echo Then run build.bat again.
    echo.
    echo PyInstaller output is ready at: dist\ErpPharmacy\
) else (
    if not exist installer_output mkdir installer_output
    "%ISCC%" installer.iss
    if errorlevel 1 (
        echo ERROR: Inno Setup compilation failed.
    ) else (
        echo.
        echo =============================================
        echo   SUCCESS!
        echo   Installer: installer_output\ErpPharmacy_Setup.exe
        echo =============================================
    )
)

pause
