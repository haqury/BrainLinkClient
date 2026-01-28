@echo off
REM Build standalone BrainLinkClient.exe via PyInstaller

REM Switch to script directory (project root)
cd /d "%~dp0"

echo [BrainLinkClient] Building Windows executable...

REM If there's a virtualenv, activate it (optional, safe if missing)
if exist "venv\Scripts\activate.bat" (
    call "venv\Scripts\activate.bat"
)

REM Build using spec file (which includes resources)
pyinstaller BrainLinkClient.spec

echo.
echo [BrainLinkClient] Build finished.
echo Executable should be in: dist\BrainLinkClient.exe
echo.
pause
