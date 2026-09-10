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

set ICON_FLAG=
if exist icon.ico set ICON_FLAG=--icon=icon.ico
if exist icon.png set ICON_FLAG=--icon=icon.png

python -m PyInstaller --windowed --onedir --name "ErpPharmacy" ^
    --hidden-import=arabic_reshaper ^
    --hidden-import=bidi ^
    --hidden-import=bidi.algorithm ^
    --hidden-import=reportlab.pdfgen ^
    --hidden-import=reportlab.pdfbase.ttfonts ^
    --hidden-import=reportlab.lib.pagesizes ^
    --hidden-import=reportlab.lib.colors ^
    --hidden-import=sqlite3 ^
    %ICON_FLAG% ^
    main.py

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
