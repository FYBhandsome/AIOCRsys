@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo    Stop All Services
echo ========================================
echo.

echo [1/3] Stopping services by port...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8001" ^| findstr "LISTENING" 2^>nul') do (
    echo Stopping PID: %%a (Port 8001)
    taskkill /F /PID %%a 2>nul
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING" 2^>nul') do (
    echo Stopping PID: %%a (Port 8000)
    taskkill /F /PID %%a 2>nul
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173" ^| findstr "LISTENING" 2^>nul') do (
    echo Stopping PID: %%a (Port 5173)
    taskkill /F /PID %%a 2>nul
)

echo.
echo [2/3] Cleaning up residual processes...
wmic process where "commandline like '%%visual_model%%main.py%%'" delete 2>nul
wmic process where "commandline like '%%PaddleOCRRAG%%uvicorn%%'" delete 2>nul
wmic process where "commandline like '%%fronted\\front%%vite%%'" delete 2>nul

echo.
echo [3/3] Done.
echo ========================================
echo    All Services Stopped
echo ========================================
echo.
pause
