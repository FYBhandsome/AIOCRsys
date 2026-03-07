#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统路由模块

提供系统健康检查、状态查询和资源监控接口。
"""

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse
from datetime import datetime
import platform
from typing import Optional

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
    try:
        import psutil
        cpu_count = psutil.cpu_count()
        memory_total = psutil.virtual_memory().total
        memory_available = psutil.virtual_memory().available
    except ImportError:
        cpu_count = None
        memory_total = None
        memory_available = None
    
    return {
        "service": "Visual Model Backend",
        "version": "1.0.0",
        "platform": platform.system(),
        "python_version": platform.python_version(),
        "cpu_count": cpu_count,
        "memory_total": memory_total,
        "memory_available": memory_available,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/stats")
async def get_system_stats():
    """获取系统统计信息"""
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent
        if platform.system() != 'Windows':
            disk_percent = psutil.disk_usage('/').percent
        else:
            disk_percent = psutil.disk_usage('C:\\').percent
    except ImportError:
        cpu_percent = None
        memory_percent = None
        disk_percent = None
    
    return {
        "cpu_percent": cpu_percent,
        "memory_percent": memory_percent,
        "disk_percent": disk_percent,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/resources")
async def get_resources():
    """获取当前资源使用状态"""
    from app.core.resource_monitor import get_resource_monitor
    
    monitor = get_resource_monitor()
    return monitor.get_current_status()


@router.get("/resources/history")
async def get_resources_history(
    limit: int = Query(default=100, ge=1, le=500, description="返回记录数量")
):
    """获取资源使用历史记录"""
    from app.core.resource_monitor import get_resource_monitor
    
    monitor = get_resource_monitor()
    return {
        "history": monitor.get_history(limit=limit),
        "total_count": len(monitor._history)
    }


@router.get("/resources/summary")
async def get_resources_summary():
    """获取资源使用摘要"""
    from app.core.resource_monitor import get_resource_monitor
    
    monitor = get_resource_monitor()
    return monitor.get_summary()


@router.get("/resources/alerts")
async def get_resources_alerts(
    limit: int = Query(default=50, ge=1, le=200, description="返回记录数量")
):
    """获取资源告警记录"""
    from app.core.resource_monitor import get_resource_monitor
    
    monitor = get_resource_monitor()
    return {
        "alerts": monitor.get_alerts(limit=limit),
        "total_count": len(monitor._alerts)
    }


@router.get("/resources/report", response_class=HTMLResponse)
async def get_resources_report_html(
    include_history: bool = Query(default=True, description="是否包含历史数据")
):
    """生成HTML格式资源报告"""
    from app.utils.resource_report import ResourceReportGenerator
    
    generator = ResourceReportGenerator()
    return generator.generate_html_report(include_history=include_history)


@router.get("/resources/report/json")
async def get_resources_report_json(
    include_history: bool = Query(default=True, description="是否包含历史数据"),
    include_alerts: bool = Query(default=True, description="是否包含告警记录")
):
    """生成JSON格式资源报告"""
    from app.utils.resource_report import ResourceReportGenerator
    
    generator = ResourceReportGenerator()
    return generator.generate_json_report(
        include_history=include_history,
        include_alerts=include_alerts
    )


@router.get("/ocr/status")
async def get_ocr_status():
    """获取OCR服务状态"""
    from app.services.ocr_service import get_ocr_service
    from app.services.ocr_model_pool import get_ocr_model_pool
    
    ocr_service = get_ocr_service()
    model_pool = get_ocr_model_pool()
    
    return {
        "ocr_service": ocr_service.get_stats(),
        "model_pool": model_pool.get_status(),
        "health": model_pool.health_check()
    }


@router.get("/executor/status")
async def get_executor_status():
    """获取线程池执行器状态"""
    from app.core.executor_manager import get_executor_status
    
    return get_executor_status()


@router.get("/performance/stats")
async def get_performance_stats(
    function_name: Optional[str] = Query(default=None, description="函数名称")
):
    """获取性能监控统计"""
    from app.core.performance_monitor import get_performance_monitor
    
    monitor = get_performance_monitor()
    return monitor.get_stats(function_name)


@router.get("/performance/summary")
async def get_performance_summary():
    """获取性能监控摘要"""
    from app.core.performance_monitor import get_performance_monitor
    
    monitor = get_performance_monitor()
    return monitor.get_summary()


@router.post("/performance/reset")
async def reset_performance_stats():
    """重置性能监控统计"""
    from app.core.performance_monitor import get_performance_monitor
    
    monitor = get_performance_monitor()
    monitor.reset()
    return {"success": True, "message": "性能监控统计已重置"}


@router.get("/cache/stats")
async def get_cache_stats():
    """获取缓存统计信息"""
    from app.core.cache_service import get_cache_service
    
    cache_service = get_cache_service()
    return cache_service.get_all_stats()


@router.post("/cache/clear")
async def clear_cache(
    cache_name: Optional[str] = Query(default=None, description="缓存名称，不指定则清空所有")
):
    """清空缓存"""
    from app.core.cache_service import get_cache_service
    
    cache_service = get_cache_service()
    
    if cache_name:
        cache = cache_service.get_cache(cache_name)
        cache.clear()
        return {"success": True, "message": f"缓存 {cache_name} 已清空"}
    else:
        cache_service.clear_all()
        return {"success": True, "message": "所有缓存已清空"}


@router.post("/cache/invalidate/student/{student_id}")
async def invalidate_student_cache(student_id: str):
    """使学生缓存失效"""
    from app.core.cache_service import get_cache_service
    
    cache_service = get_cache_service()
    cache_service.invalidate_student(student_id)
    return {"success": True, "message": f"学生 {student_id} 的缓存已失效"}


@router.post("/cache/invalidate/class/{class_id}")
async def invalidate_class_cache(class_id: str):
    """使班级缓存失效"""
    from app.core.cache_service import get_cache_service
    
    cache_service = get_cache_service()
    cache_service.invalidate_class(class_id)
    return {"success": True, "message": f"班级 {class_id} 的缓存已失效"}


@router.get("/comprehensive-score/stats")
async def get_comprehensive_score_stats():
    """获取综测成绩计算统计"""
    from app.services.comprehensive_score_service import get_comprehensive_score_service
    
    service = get_comprehensive_score_service()
    return {
        "stats": service._stats,
        "cache_stats": service._cache.get_all_stats()
    }


@router.get("/ocr-processing/stats")
async def get_ocr_processing_stats():
    """获取OCR处理统计"""
    from app.services.certificate_ocr_processing_service import get_certificate_ocr_processing_service
    
    service = get_certificate_ocr_processing_service()
    return service.get_stats()


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
