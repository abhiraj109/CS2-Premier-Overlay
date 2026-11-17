@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
  py -3 server.py --stop
) else (
  python server.py --stop
)
if errorlevel 1 (
  pause
  exit /b 1
)
