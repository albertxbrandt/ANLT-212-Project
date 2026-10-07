@echo off
REM Run backend and frontend unit tests, then build the frontend.

setlocal
cd /d "%~dp0"

echo.
echo ======================================
echo Testing PantryPal
echo ======================================
echo.

python -m pip install -r backend\requirements.txt -r backend\requirements-dev.txt
if errorlevel 1 exit /b 1

python -m pytest tests -q
if errorlevel 1 exit /b 1

cd frontend
call npm install
if errorlevel 1 exit /b 1

call npm test
if errorlevel 1 exit /b 1

call npm run build
if errorlevel 1 exit /b 1

echo.
echo Tests and frontend build passed.
echo.
pause
exit /b 0
