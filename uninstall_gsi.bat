@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0uninstall_gsi.ps1"
set "OVERLAY_EXIT=%ERRORLEVEL%"
echo.
pause
exit /b %OVERLAY_EXIT%
