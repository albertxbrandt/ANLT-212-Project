@echo off
REM Start frontend with process cleanup
REM This script will kill any running Node processes and start React dev server

echo.
echo ======================================
echo Starting Frontend (React on port 5173)
echo ======================================
echo.

REM Kill any process using port 5173
netstat -ano | findstr :5173 > nul
if %ERRORLEVEL% EQU 0 (
    echo Killing process on port 5173...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173') do taskkill /PID %%a /F 2>nul
    if %ERRORLEVEL% EQU 0 (
        echo ✓ Killed process on port 5173
    )
)

REM Kill any remaining node processes
taskkill /IM node.exe /F /T 2>nul
if %ERRORLEVEL% EQU 0 (
    echo ✓ Killed existing Node processes
) else (
    echo ○ No existing Node processes found
)

REM Change to frontend directory
cd frontend

REM Check if node_modules exists, if not install dependencies
if not exist "node_modules" (
    echo Installing dependencies...
    call npm install
)

echo.
echo ✓ Frontend starting on http://localhost:5173
echo Press Ctrl+C to stop
echo.

REM Start React dev server
call npm run dev

pause
