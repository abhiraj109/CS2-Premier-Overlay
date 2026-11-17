@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (py -3 send_test_data.py) else (python send_test_data.py)
set "OVERLAY_EXIT=%ERRORLEVEL%"
pause
exit /b %OVERLAY_EXIT%
