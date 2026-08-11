@echo off
REM Cleanup script - kills all related processes

echo.
echo ======================================
echo Cleaning up Simple Start Processes
echo ======================================
echo.

REM Kill Python processes
echo Killing Python processes...
taskkill /F /IM python.exe /T 2>nul
if %ERRORLEVEL% EQU 0 (
    echo ✓ Python processes killed
) else (
    echo ○ No Python processes found
)

REM Kill Node processes
echo Killing Node processes...
taskkill /IM node.exe /F /T 2>nul
if %ERRORLEVEL% EQU 0 (
    echo ✓ Node processes killed
) else (
    echo ○ No Node processes found
)

REM Kill any process on port 5000
echo Killing process on port 5000...
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr :5000') do taskkill /PID %%a /F 2>nul
if %ERRORLEVEL% EQU 0 (
    echo ✓ Port 5000 cleared
) else (
    echo ○ Port 5000 already clear
)

REM Kill any process on port 5173
echo Killing process on port 5173...
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr :5173') do taskkill /PID %%a /F 2>nul
if %ERRORLEVEL% EQU 0 (
    echo ✓ Port 5173 cleared
) else (
    echo ○ Port 5173 already clear
)

echo.
echo ✓ Cleanup complete
echo.

pause
