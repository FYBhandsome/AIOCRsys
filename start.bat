@echo off
chcp 65001 >nul
title 综测计算助手 - 一键启动

echo ========================================
echo    综测计算助手 - 一键启动脚本 v2.0
echo ========================================
echo.

REM 设置项目路径
set PROJECT_ROOT=%~dp0
set VISUAL_MODEL_DIR=%PROJECT_ROOT%visual_model
set RAG_DIR=%PROJECT_ROOT%PaddleOCRRAG
set FRONTEND_DIR=%PROJECT_ROOT%fronted\front

REM 设置虚拟环境路径
set VENV_PYTHON=%VISUAL_MODEL_DIR%\venv\python.exe
set CONDA_PYTHON=%PROJECT_ROOT%.conda\python.exe

echo [1/4] 检查虚拟环境...
if not exist "%VENV_PYTHON%" (
    echo [错误] Visual Model虚拟环境不存在: %VENV_PYTHON%
    echo 请先运行: python manage.py venv
    pause
    exit /b 1
)

if not exist "%CONDA_PYTHON%" (
    echo [警告] RAG虚拟环境不存在: %CONDA_PYTHON%
    echo RAG服务将跳过启动
    set RAG_ENABLED=0
) else (
    set RAG_ENABLED=1
)

echo.
echo [2/4] 启动 Visual Model 后端服务 (端口 8001)...
start "Visual Model Backend" cmd /k "cd /d %VISUAL_MODEL_DIR% && %VENV_PYTHON% main.py"
timeout /t 5 /nobreak >nul

if "%RAG_ENABLED%"=="1" (
    echo [3/4] 启动 RAG 后端服务 (端口 8000)...
    start "RAG Backend" cmd /k "cd /d %RAG_DIR% && %CONDA_PYTHON% -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
    timeout /t 5 /nobreak >nul
) else (
    echo [3/4] RAG 服务跳过 (虚拟环境不存在)
)

echo [4/4] 启动前端服务 (端口 5173)...
cd /d %FRONTEND_DIR%
if exist "node_modules" (
    start "Frontend" cmd /k "cd /d %FRONTEND_DIR% && npm run dev"
) else (
    echo [警告] 前端依赖未安装，正在安装...
    call npm install
    start "Frontend" cmd /k "cd /d %FRONTEND_DIR% && npm run dev"
)

echo.
echo ========================================
echo    服务启动完成
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
echo 按任意键退出此窗口 (服务将继续运行)
echo ========================================
pause >nul
