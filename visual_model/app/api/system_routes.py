#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统路由模块

提供系统健康检查和状态查询接口。
"""

from fastapi import APIRouter
from datetime import datetime
import platform
import psutil

router = APIRouter(prefix="/system", tags=["系统"])


@router.get("/health")
async def system_health_check():
    """系统健康检查端点"""
    return {
        "status": "healthy",
        "service": "Visual Model Backend",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "platform": platform.system(),
        "python_version": platform.python_version()
    }


@router.get("/info")
async def get_system_info():
    """获取系统信息"""
    return {
        "service": "Visual Model Backend",
        "version": "1.0.0",
        "platform": platform.system(),
        "python_version": platform.python_version(),
        "cpu_count": psutil.cpu_count(),
        "memory_total": psutil.virtual_memory().total,
        "memory_available": psutil.virtual_memory().available,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/stats")
async def get_system_stats():
    """获取系统统计信息"""
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent if platform.system() != 'Windows' else psutil.disk_usage('C:\\').percent,
        "timestamp": datetime.now().isoformat()
    }


health_router = APIRouter(tags=["系统"])


@health_router.get("/health")
async def api_health_check():
    """API健康检查端点（/api/v1/health）"""
    return {
        "status": "healthy",
        "service": "Visual Model Backend",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "platform": platform.system(),
        "python_version": platform.python_version()
    }
