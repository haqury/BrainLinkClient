@echo off
echo Attempting to install pythonnet...
echo.

REM Try different versions
echo [1] Trying pythonnet 3.0.3...
pip install pythonnet==3.0.3
if %errorlevel% equ 0 goto success

echo.
echo [2] Trying latest pythonnet...
pip install pythonnet --upgrade
if %errorlevel% equ 0 goto success

echo.
echo [3] Trying to install from wheel...
pip install --only-binary :all: pythonnet
if %errorlevel% equ 0 goto success

echo.
echo ========================================
echo Installation failed!
echo ========================================
echo.
echo But don't worry! The application will still work.
echo You can use the simulator for testing.
echo.
goto end

:success
echo.
echo ========================================
echo SUCCESS!
echo ========================================
echo pythonnet installed successfully!
echo.

:end
pause
