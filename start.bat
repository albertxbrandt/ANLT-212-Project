@echo off
REM Launch the PantryPal API and the React app in two windows.

setlocal
cd /d "%~dp0"

echo.
echo ======================================
echo Starting PantryPal
echo ======================================
echo.
echo Backend:  http://localhost:5000
echo Frontend: http://localhost:5173
echo.

call :clearport 5000
call :clearport 5173

echo Starting backend...
start "PantryPal Backend" cmd /k "cd /d "%~dp0backend" && python -m pip install -r requirements.txt && python -u src/app.py"

timeout /t 2 /nobreak >nul

echo Starting frontend...
start "PantryPal Frontend" cmd /k "cd /d "%~dp0frontend" && npm install && npm run dev"

echo.
echo Close each window to stop that process.
echo.
pause
exit /b 0

:clearport
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%1 ^| findstr LISTENING') do taskkill /PID %%a /F >nul 2>&1
exit /b 0
