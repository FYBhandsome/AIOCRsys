@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

title 综测计算助手 - 停止所有服务

echo ========================================
echo    综测计算助手 - 停止所有服务 v3.0
echo ========================================
echo.

set "STOPPED_ANY=0"

echo [1/4] 检查并停止端口 8001 (Visual Model)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8001" ^| findstr "LISTENING" 2^>nul') do (
    echo 正在停止进程 PID: %%a
    taskkill /F /PID %%a 2>nul
    set "STOPPED_ANY=1"
)
if "!STOPPED_ANY!"=="0" echo [信息] 端口 8001 无运行中的服务

echo.
echo [2/4] 检查并停止端口 8000 (RAG服务)...
set "STOPPED_ANY=0"
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING" 2^>nul') do (
    echo 正在停止进程 PID: %%a
    taskkill /F /PID %%a 2>nul
    set "STOPPED_ANY=1"
)
if "!STOPPED_ANY!"=="0" echo [信息] 端口 8000 无运行中的服务

echo.
echo [3/4] 检查并停止端口 5173 (前端服务)...
set "STOPPED_ANY=0"
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173" ^| findstr "LISTENING" 2^>nul') do (
    echo 正在停止进程 PID: %%a
    taskkill /F /PID %%a 2>nul
    set "STOPPED_ANY=1"
)
if "!STOPPED_ANY!"=="0" echo [信息] 端口 5173 无运行中的服务

echo.
echo [4/4] 清理残留进程...
REM 停止所有相关的Python进程（仅限本项目相关）
wmic process where "commandline like '%%visual_model%%main.py%%'" delete 2>nul
wmic process where "commandline like '%%PaddleOCRRAG%%uvicorn%%'" delete 2>nul

REM 停止所有相关的Node进程（仅限本项目相关）
wmic process where "commandline like '%%fronted\\front%%npm%%'" delete 2>nul
wmic process where "commandline like '%%fronted\\front%%vite%%'" delete 2>nul

echo.
echo ========================================
echo    所有服务已停止
echo ========================================
echo.
echo 如需重新启动服务，请运行 start.bat
echo.
pause
