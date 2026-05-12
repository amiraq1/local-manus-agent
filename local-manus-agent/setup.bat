@echo off
echo ================================================
echo Local Manus Agent - Setup (Windows)
echo ================================================
echo.

python scripts\check_requirements.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Fix missing requirements first.
    pause
    exit /b 1
)

echo.
python scripts\setup.py
pause
