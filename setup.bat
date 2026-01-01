@echo off
REM Secure Edge Vision System - Setup Script for Windows
REM Run this script to set up the project

echo ============================================
echo  Secure Edge Vision System - Setup
echo ============================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.9+
    pause
    exit /b 1
)

echo [1/5] Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo Created venv
) else (
    echo venv already exists
)

echo.
echo [2/5] Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo [3/5] Upgrading pip...
python -m pip install --upgrade pip

echo.
echo [4/5] Installing dependencies...
pip install -r requirements.txt

echo.
echo [5/5] Creating directories...
if not exist "models" mkdir models
if not exist "keys" mkdir keys
if not exist "recordings\public" mkdir recordings\public
if not exist "recordings\evidence" mkdir recordings\evidence

echo.
echo ============================================
echo  Setup Complete!
echo ============================================
echo.
echo Next steps:
echo   1. Activate venv: venv\Scripts\activate
echo   2. Test components: python demo.py
echo   3. Run system: python main.py
echo   4. Open browser: http://localhost:8000
echo.
pause
