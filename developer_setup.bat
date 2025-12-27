@echo off
TITLE Knob Generator Developer Setup
echo ==========================================
      Knob Generator Dev Setup
echo ==========================================
echo.
echo This script will set up a Python virtual environment
echo and install necessary dependencies for development.
echo.

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Starting Knob Generator (Dev Mode)...
python run_app.py
pause
