@echo off
chcp 65001 >nul
echo ========================================
echo 综测加分规则RAG系统
echo ========================================
echo.

REM 检查Python版本
python --version
echo.

echo 正在启动服务...
echo 访问 http://localhost:8010/docs 查看API文档
echo 按 Ctrl+C 停止服务
echo.

uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload

