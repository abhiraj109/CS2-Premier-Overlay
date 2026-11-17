@echo off
setlocal
cd /d "%~dp0"
set "PYEXE="
where py >nul 2>nul
if not errorlevel 1 set "PYEXE=py -3"
if not defined PYEXE (
  where python >nul 2>nul
  if not errorlevel 1 set "PYEXE=python"
)
if not defined PYEXE (
  echo Python 3 was not found.
  echo Install Python 3.10 or newer from https://www.python.org/downloads/windows/
  echo During installation, enable the Python launcher and Add Python to PATH.
  pause
  exit /b 1
)
%PYEXE% -c "import sys; print('Python', sys.version.split()[0]); raise SystemExit(0 if sys.version_info >= (3,10) else 1)"
if errorlevel 1 (
  echo This overlay requires Python 3.10 or newer.
  pause
  exit /b 1
)
echo.
echo Starting CS2 Premier Sync Overlay...
echo OBS Browser Source: http://127.0.0.1:3000/
echo Browser Source size: 640 x 180
echo One-time fallback setup: http://127.0.0.1:3000/settings
echo.
%PYEXE% server.py %*
set "OVERLAY_EXIT=%ERRORLEVEL%"
if not "%OVERLAY_EXIT%"=="0" pause
exit /b %OVERLAY_EXIT%
