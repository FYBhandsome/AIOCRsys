@echo off
chcp 65001 >nul
title 综测计算助手 - 停止所有服务

echo ========================================
echo    综测计算助手 - 停止所有服务
echo ========================================
echo.

echo 正在停止所有 Python 服务...
taskkill /F /IM python.exe 2>nul

echo 正在停止所有 Node 服务...
taskkill /F /IM node.exe 2>nul

echo.
echo ========================================
echo    所有服务已停止
echo ========================================
echo.
pause
