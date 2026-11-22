@echo off
title EduDesk - Student Management System
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo Python is not installed or not in PATH. Install it from https://www.python.org/downloads/
  pause
  exit /b 1
)

if not exist venv (
  echo Creating virtual environment...
  python -m venv venv
)
call venv\Scripts\activate.bat
echo Installing requirements...
python -m pip install -q -r requirements.txt

start "" http://127.0.0.1:5000
python app.py
pause
