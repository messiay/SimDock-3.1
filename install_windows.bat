@echo off
echo Installing SimDock 3.1...
echo.

echo Step 1: Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found! Please install Python 3.8+ first.
    pause
    exit /b 1
)

echo Step 2: Installing dependencies...
pip install -r requirements.txt

echo Step 3: Installing SimDock...
pip install -e .

echo.
echo Installation complete!
echo.
echo IMPORTANT: Make sure you have installed:
echo - UCSF ChimeraX
echo - AutoDock Vina  
echo - Open Babel
echo.
echo Run SimDock with: python main.py
pause