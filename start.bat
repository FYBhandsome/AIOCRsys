@echo off
chcp 65001 >nul
cd /d "%~dp0"

REM Check Python availability
if exist ".conda\python.exe" (
    ".conda\python.exe" start.py %*
) else if exist "visual_model\venv\python.exe" (
    "visual_model\venv\python.exe" start.py %*
) else (
    python start.py %*
)
