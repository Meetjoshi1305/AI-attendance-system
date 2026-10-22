@echo off
title FaceAttend PRO - Anti-Proxy AI Attendance
cd /d "%~dp0"

echo ========================================================
echo   Starting FaceAttend PRO (Anti-Proxy AI Attendance)
echo ========================================================
echo.

python app.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Application stopped with error code %ERRORLEVEL%.
    pause
)
