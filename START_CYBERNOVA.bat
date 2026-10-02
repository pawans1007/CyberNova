@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo CyberNova environment not found. Run SETUP_CYBERNOVA.bat first.
  pause
  exit /b 1
)
.venv\Scripts\python.exe main.py
if errorlevel 1 pause
