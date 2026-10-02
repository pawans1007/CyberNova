@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo Python launcher not found. Install Python 3.11 or 3.12 and enable Add to PATH.
  pause
  exit /b 1
)
py -3.12 -m venv .venv
if errorlevel 1 py -3 -m venv .venv
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto fail
echo.
echo Setup finished. Double-click START_CYBERNOVA.bat to launch.
pause
exit /b 0
:fail
echo Setup failed. Check the error above and README.md.
pause
exit /b 1
