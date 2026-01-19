@echo off
REM BrainLink Client Launcher for Windows

echo Starting BrainLink Client...
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then: venv\Scripts\activate
    echo And: pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate

REM Check if dependencies are installed
python -c "import PyQt5" 2>nul
if errorlevel 1 (
    echo Dependencies not installed!
    echo Installing requirements...
    pip install -r requirements.txt
)

REM Run application
python main.py

REM Deactivate virtual environment
deactivate

echo.
echo Application closed.
pause
