@echo off
echo =============================================
echo   بناء تطبيق صيدلية عباد الرحمان
echo =============================================
echo.

echo [1/3] تثبيت PyInstaller...
pip install pyinstaller
if errorlevel 1 (
    echo فشل تثبيت PyInstaller. تأكد من اتصالك بالانترنت.
    pause
    exit /b 1
)

echo.
echo [2/3] إنشاء أيقونة التطبيق...
python save_icon.py

echo.
echo [3/3] بناء الملف التنفيذي...

rem Uses ErpPharmacy.spec (hidden imports, icon, pyodbc for the Access import).
python -m PyInstaller --noconfirm ErpPharmacy.spec

echo.
if exist dist\ErpPharmacy\ErpPharmacy.exe (
    echo =============================================
    echo   تم البناء بنجاح!
    echo   المجلد الجاهز للنسخ: dist\ErpPharmacy\
    echo   انسخ هذا المجلد كاملاً للكمبيوتر الآخر
    echo   وشغّل ErpPharmacy.exe
    echo =============================================
) else (
    echo حدث خطأ أثناء البناء. راجع الرسائل أعلاه.
)

pause
