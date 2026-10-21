@echo off
echo ========================================
echo    Building ErpPharmacy (single file)...
echo ========================================

pyinstaller --clean ErpPharmacy.spec

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo    Build complete!
echo    Output: dist\ErpPharmacy.exe
echo    Share this single file with any PC.
echo ========================================
pause
