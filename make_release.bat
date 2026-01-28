@echo off
REM Build BrainLinkClient.exe and pack release archive

REM Switch to script directory (project root)
cd /d "%~dp0"

echo [BrainLinkClient] Building exe...
if exist "build.bat" (
    call build.bat
) else (
    echo build.bat not found, running PyInstaller directly...
    if exist "venv\Scripts\activate.bat" (
        call "venv\Scripts\activate.bat"
    )
    pyinstaller BrainLinkClient.spec
)

REM Create release folder
if not exist "release" (
    mkdir "release"
)

echo.
echo [BrainLinkClient] Packing release zip...

REM Use PowerShell Compress-Archive to create zip
powershell -NoLogo -NoProfile -Command ^
 "Compress-Archive -Path 'dist\\BrainLinkClient.exe','README.md','INSTALL.md','LICENSE' -DestinationPath 'release\\BrainLinkClient_win64.zip' -Force"

echo.
echo [BrainLinkClient] Release created: release\BrainLinkClient_win64.zip
echo.
pause

