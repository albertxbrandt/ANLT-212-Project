@echo off
REM Start backend with process cleanup
REM This script will kill any running processes on port 5000 and start Flask

echo.
echo ======================================
echo Starting Backend (Flask on port 5000)
echo ======================================
echo.

REM Kill any existing Python processes
echo Cleaning up existing processes...
taskkill /F /IM python.exe /T 2>nul
if %ERRORLEVEL% EQU 0 (
    echo ✓ Killed existing Python processes
) else (
    echo ○ No existing Python processes found
)

REM Kill any process using port 5000
netstat -ano | findstr :5000 > nul
if %ERRORLEVEL% EQU 0 (
    echo Killing process on port 5000...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000') do taskkill /PID %%a /F 2>nul
    if %ERRORLEVEL% EQU 0 (
        echo ✓ Killed process on port 5000
    )
)

REM Change to backend directory
cd backend

REM Check if virtual environment exists, if not create it
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo Installing dependencies...
    pip install -r requirements.txt
) else (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

echo.
echo ✓ Backend starting on http://localhost:5000
echo Press Ctrl+C to stop
echo.

REM Start Flask in debug mode
python -m flask run --debug

pause
