@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

title 综测计算助手 - 服务管理控制台

echo ========================================
echo    综测计算助手 - 一键启动脚本 v3.0
echo ========================================
echo.

REM 设置项目路径
set "PROJECT_ROOT=%~dp0"
set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"
set "VISUAL_MODEL_DIR=%PROJECT_ROOT%\visual_model"
set "RAG_DIR=%PROJECT_ROOT%\PaddleOCRRAG"
set "FRONTEND_DIR=%PROJECT_ROOT%\fronted\front"

REM 设置虚拟环境路径
set "VENV_PYTHON=%VISUAL_MODEL_DIR%\venv\python.exe"
set "CONDA_PYTHON=%PROJECT_ROOT%\.conda\python.exe"

REM 设置日志目录
set "LOG_DIR=%PROJECT_ROOT%\logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM 设置日志文件
set "VISUAL_LOG=%LOG_DIR%\visual_model.log"
set "RAG_LOG=%LOG_DIR%\rag.log"
set "FRONTEND_LOG=%LOG_DIR%\frontend.log"
set "ERROR_LOG=%LOG_DIR%\errors.log"

REM 清理旧日志
if exist "%VISUAL_LOG%" del "%VISUAL_LOG%" 2>nul
if exist "%RAG_LOG%" del "%RAG_LOG%" 2>nul
if exist "%FRONTEND_LOG%" del "%FRONTEND_LOG%" 2>nul
if exist "%ERROR_LOG%" del "%ERROR_LOG%" 2>nul

REM 初始化错误标志
set "VISUAL_ERROR=0"
set "RAG_ERROR=0"
set "FRONTEND_ERROR=0"
set "RAG_ENABLED=1"

echo [1/5] 检查虚拟环境...
if not exist "%VENV_PYTHON%" (
    echo [错误] Visual Model虚拟环境不存在: %VENV_PYTHON%
    echo 请先运行: python manage.py venv
    pause
    exit /b 1
)

if not exist "%CONDA_PYTHON%" (
    echo [警告] RAG虚拟环境不存在: %CONDA_PYTHON%
    echo RAG服务将跳过启动
    set "RAG_ENABLED=0"
)

echo.
echo [2/5] 启动 Visual Model 后端服务 (端口 8001)...
cd /d "%VISUAL_MODEL_DIR%"
start /b "" cmd /c "("%VENV_PYTHON%" main.py >> "%VISUAL_LOG%" 2>&1) || echo [ERROR] Visual Model启动失败 >> "%ERROR_LOG%""
timeout /t 3 /nobreak >nul

echo [3/5] 启动 RAG 后端服务 (端口 8000)...
if "%RAG_ENABLED%"=="1" (
    cd /d "%RAG_DIR%"
    start /b "" cmd /c "("%CONDA_PYTHON%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 >> "%RAG_LOG%" 2>&1) || echo [ERROR] RAG服务启动失败 >> "%ERROR_LOG%""
    timeout /t 3 /nobreak >nul
) else (
    echo [跳过] RAG服务 (虚拟环境不存在)
)

echo [4/5] 启动前端服务 (端口 5173)...
cd /d "%FRONTEND_DIR%"
if exist "node_modules" (
    start /b "" cmd /c "(npm run dev >> "%FRONTEND_LOG%" 2>&1) || echo [ERROR] 前端服务启动失败 >> "%ERROR_LOG%""
) else (
    echo [警告] 前端依赖未安装，正在安装...
    call npm install >> "%FRONTEND_LOG%" 2>&1
    start /b "" cmd /c "(npm run dev >> "%FRONTEND_LOG%" 2>&1) || echo [ERROR] 前端服务启动失败 >> "%ERROR_LOG%""
)
timeout /t 3 /nobreak >nul

echo [5/5] 等待服务初始化...
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo    服务启动完成 - 实时日志监控中
echo ========================================
echo.
echo 服务地址:
echo   - 前端应用:     http://localhost:5173
echo   - Visual Model: http://localhost:8001/docs
echo   - RAG服务:      http://localhost:8000/docs
echo.
echo 测试账号:
echo   - 管理员: dev_admin / dev123456
echo   - 教师:   dev_teacher / dev123456
echo   - 学生:   dev_student / dev123456
echo.
echo 日志文件位置: %LOG_DIR%
echo.
echo 按 Ctrl+C 停止所有服务并退出
echo ========================================
echo.

:log_monitor
cls
echo ========================================
echo    综测计算助手 - 实时日志监控
echo ========================================
echo [时间: %date% %time%]
echo.

echo ---------- Visual Model (端口 8001) ----------
if exist "%VISUAL_LOG%" (
    powershell -Command "Get-Content '%VISUAL_LOG%' -Tail 8"
) else (
    echo [等待日志生成...]
)
echo.

if "%RAG_ENABLED%"=="1" (
    echo ---------- RAG服务 (端口 8000) ----------
    if exist "%RAG_LOG%" (
        powershell -Command "Get-Content '%RAG_LOG%' -Tail 8"
    ) else (
        echo [等待日志生成...]
    )
    echo.
)

echo ---------- 前端服务 (端口 5173) ----------
if exist "%FRONTEND_LOG%" (
    powershell -Command "Get-Content '%FRONTEND_LOG%' -Tail 8"
) else (
    echo [等待日志生成...]
)
echo.

if exist "%ERROR_LOG%" (
    echo ---------- 错误信息 ----------
    type "%ERROR_LOG%"
    echo.
)

echo ========================================
echo 按 Ctrl+C 停止所有服务并退出
echo ========================================

REM 等待3秒后刷新
timeout /t 3 /nobreak >nul
goto log_monitor

:end
echo.
echo 正在停止所有服务...

REM 停止所有Python进程
taskkill /F /FI "WINDOWTITLE eq Visual Model*" 2>nul
taskkill /F /FI "WINDOWTITLE eq RAG*" 2>nul
taskkill /F /FI "WINDOWTITLE eq Frontend*" 2>nul

REM 通过端口停止服务
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8001" ^| findstr "LISTENING"') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173" ^| findstr "LISTENING"') do taskkill /F /PID %%a 2>nul

echo 所有服务已停止
exit /b 0
