@echo off
setlocal
cd /d "%~dp0"
echo ==============================================
echo       CS2 PREMIER SYNC - ONE-TIME SETUP
echo ==============================================
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_gsi.ps1"
if errorlevel 1 (
  echo GSI installation could not complete. Fix the path, then run setup_once.bat again.
  pause
  exit /b 1
)
echo.
choice /C YN /M "Start the overlay automatically when Windows starts"
if errorlevel 2 goto skipstartup
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_startup.ps1"
if errorlevel 1 echo Startup shortcut could not be installed. You can still use run_overlay.bat manually.
:skipstartup
echo.
echo Setup complete. Run run_overlay.bat now, then restart CS2.
echo Add http://127.0.0.1:3000/ as an OBS Browser Source at 640 x 180.
pause
