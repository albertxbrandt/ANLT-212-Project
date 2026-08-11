@echo off
REM Start both backend and frontend together

setlocal enabledelayedexpansion

echo.
echo ======================================
echo Starting Simple Start (Backend + Frontend)
echo ======================================
echo.
echo This will open two terminal windows:
echo - Backend (Flask) on http://localhost:5000
echo - Frontend (React) on http://localhost:5173 (or next available port)
echo.

REM Get the directory where this script is located
cd /d "%~dp0"

REM Kill any existing processes on the ports
echo Cleaning up existing processes...
taskkill /F /IM python.exe /T 2>nul
taskkill /IM node.exe /F /T 2>nul

timeout /t 1 /nobreak

echo ✓ Cleanup complete
echo.

REM Start backend in new window
echo Starting backend...
start "Simple Start - Backend" cmd /k "cd /d "%~dp0backend" && python -m pip install -r requirements.txt >nul 2>&1 && python -u src/app.py"

timeout /t 2 /nobreak

REM Start frontend in new window
echo Starting frontend...
start "Simple Start - Frontend" cmd /k "cd /d "%~dp0frontend" && npm install --legacy-peer-deps >nul 2>&1 && npm run dev"

echo.
echo ✓ Both services starting in separate windows
echo.
echo Backend: http://localhost:5000
echo Frontend: http://localhost:5173 (or next available port)
echo.
echo Close the terminal windows to stop the services.
echo.
pause

pause
