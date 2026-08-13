@echo off
REM Build BrainLinkClient.exe and pack release archive

REM Switch to script directory (project root)
cd /d "%~dp0"

echo [BrainLinkClient] Building exe...
if exist "build.bat" (
    call build.bat
) else (
    echo build.bat not found, running PyInstaller directly...
    if exist ".venv\Scripts\activate.bat" (
        call ".venv\Scripts\activate.bat"
    ) else if exist "venv\Scripts\activate.bat" (
        call "venv\Scripts\activate.bat"
    )
    pyinstaller --noconfirm BrainLinkClient.spec
)

REM Create release folder
if not exist "release" (
    mkdir "release"
)

echo.
echo [BrainLinkClient] Packing release zip...

REM Pack exe + docs that exist
powershell -NoLogo -NoProfile -Command ^
 "$items=@('dist\\BrainLinkClient.exe'); foreach($f in @('README.md','INSTALL.md','LICENSE')){ if(Test-Path $f){ $items+=$f } }; Compress-Archive -Path $items -DestinationPath 'release\\BrainLinkClient_win64.zip' -Force"

echo.
echo [BrainLinkClient] Release created: release\BrainLinkClient_win64.zip
echo.

