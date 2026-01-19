@echo off
REM Setup BrainLink SDK - Copy DLL files

echo ===================================
echo BrainLink SDK Setup
echo ===================================
echo.

REM Install pythonnet
echo [1/3] Installing pythonnet...
pip install pythonnet
echo.

REM Copy DLL files
echo [2/3] Copying DLL files...

set SOURCE=C:\Users\haqury\source\repos\BrainLinkConnect\bin\Release
set DEST=C:\Users\haqury\PycharmProjects\BrainLinkClient\services

if not exist "%SOURCE%" (
    echo ERROR: Source directory not found: %SOURCE%
    echo Please check C# project location
    pause
    exit /b 1
)

if not exist "%DEST%" (
    mkdir "%DEST%"
)

echo Copying from: %SOURCE%
echo Copying to:   %DEST%
echo.

copy "%SOURCE%\BrainLinkSDK_Windows.dll" "%DEST%\" /Y
copy "%SOURCE%\wclBluetoothFramework.dll" "%DEST%\" /Y
copy "%SOURCE%\wclCommon.dll" "%DEST%\" /Y
copy "%SOURCE%\wclCommunication.dll" "%DEST%\" /Y

echo.
echo [3/3] Verification...
if exist "%DEST%\BrainLinkSDK_Windows.dll" (
    echo ✓ BrainLinkSDK_Windows.dll copied
) else (
    echo ✗ BrainLinkSDK_Windows.dll NOT found
)

if exist "%DEST%\wclBluetoothFramework.dll" (
    echo ✓ wclBluetoothFramework.dll copied
) else (
    echo ✗ wclBluetoothFramework.dll NOT found
)

if exist "%DEST%\wclCommon.dll" (
    echo ✓ wclCommon.dll copied
) else (
    echo ✗ wclCommon.dll NOT found
)

if exist "%DEST%\wclCommunication.dll" (
    echo ✓ wclCommunication.dll copied
) else (
    echo ✗ wclCommunication.dll NOT found
)

echo.
echo ===================================
echo Setup Complete!
echo ===================================
echo.
echo You can now run: python main.py
echo.
pause
