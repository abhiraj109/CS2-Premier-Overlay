@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_startup.ps1"
set "OVERLAY_EXIT=%ERRORLEVEL%"
pause
exit /b %OVERLAY_EXIT%
