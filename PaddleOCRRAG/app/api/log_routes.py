"""
日志查询与分析API路由
提供日志搜索、性能监控、错误统计等功能
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query
from app.models import ApiResponse
from app.core.logger import (
    get_logger, 
    log_analyzer, 
    performance_monitor,
    LogLevel
)

logger = get_logger(__name__)
router = APIRouter(prefix="/logs", tags=["日志管理"])


@router.get("/search")
async def search_logs(
    keyword: str = Query(None, description="搜索关键词"),
    level: str = Query(None, description="日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)"),
    request_id: str = Query(None, description="请求ID"),
    hours: int = Query(24, description="最近N小时"),
    limit: int = Query(100, description="返回数量限制")
):
    """搜索日志
    
    Args:
        keyword: 搜索关键词
        level: 日志级别
        request_id: 请求ID
        hours: 最近N小时
        limit: 返回数量限制
        
    Returns:
        匹配的日志列表
    """
    logger.info(f"搜索日志: keyword={keyword}, level={level}, request_id={request_id}")
    
    try:
        start_time = datetime.now() - timedelta(hours=hours)
        
        results = log_analyzer.search_logs(
            keyword=keyword,
            level=level,
            start_time=start_time,
            request_id=request_id,
            limit=limit
        )
        
        return ApiResponse(
            success=True,
            data={
                "logs": results,
                "count": len(results),
                "query": {
                    "keyword": keyword,
                    "level": level,
                    "request_id": request_id,
                    "hours": hours
                }
            },
            message=f"找到 {len(results)} 条日志"
        )
    except Exception as e:
        logger.error(f"搜索日志失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"搜索日志失败: {str(e)}")


@router.get("/errors/summary")
async def get_error_summary(
    hours: int = Query(24, description="最近N小时")
):
    """获取错误摘要
    
    Args:
        hours: 最近N小时
        
    Returns:
        错误统计摘要
    """
    logger.info(f"获取错误摘要: hours={hours}")
    
    try:
        summary = log_analyzer.get_error_summary(hours=hours)
        
        return ApiResponse(
            success=True,
            data=summary,
            message="获取错误摘要成功"
        )
    except Exception as e:
        logger.error(f"获取错误摘要失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取错误摘要失败: {str(e)}")


@router.get("/request/{request_id}")
async def get_request_trace(request_id: str):
    """获取请求追踪日志
    
    Args:
        request_id: 请求ID
        
    Returns:
        该请求的所有日志
    """
    logger.info(f"获取请求追踪: request_id={request_id}")
    
    try:
        traces = log_analyzer.get_request_trace(request_id)
        
        if not traces:
            return ApiResponse(
                success=False,
                data={"request_id": request_id, "traces": []},
                message=f"未找到请求 {request_id} 的日志"
            )
        
        return ApiResponse(
            success=True,
            data={
                "request_id": request_id,
                "traces": traces,
                "count": len(traces)
            },
            message=f"找到 {len(traces)} 条日志"
        )
    except Exception as e:
        logger.error(f"获取请求追踪失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取请求追踪失败: {str(e)}")


@router.get("/performance/stats")
async def get_performance_stats(
    operation: str = Query(None, description="操作名称"),
    last_n: int = Query(100, description="最近N条记录")
):
    """获取性能统计
    
    Args:
        operation: 操作名称（可选）
        last_n: 最近N条记录
        
    Returns:
        性能统计数据
    """
    logger.debug(f"获取性能统计: operation={operation}, last_n={last_n}")
    
    try:
        stats = performance_monitor.get_stats(operation=operation, last_n=last_n)
        
        return ApiResponse(
            success=True,
            data=stats,
            message="获取性能统计成功"
        )
    except Exception as e:
        logger.error(f"获取性能统计失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取性能统计失败: {str(e)}")


@router.get("/performance/slow")
async def get_slow_operations(
    threshold_ms: int = Query(1000, description="慢操作阈值（毫秒）"),
    last_n: int = Query(50, description="最近N条记录")
):
    """获取慢操作列表
    
    Args:
        threshold_ms: 慢操作阈值（毫秒）
        last_n: 最近N条记录
        
    Returns:
        慢操作列表
    """
    logger.info(f"获取慢操作: threshold_ms={threshold_ms}, last_n={last_n}")
    
    try:
        slow_ops = performance_monitor.get_slow_operations(
            threshold_ms=threshold_ms, 
            last_n=last_n
        )
        
        return ApiResponse(
            success=True,
            data={
                "slow_operations": slow_ops,
                "count": len(slow_ops),
                "threshold_ms": threshold_ms
            },
            message=f"找到 {len(slow_ops)} 个慢操作"
        )
    except Exception as e:
        logger.error(f"获取慢操作失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取慢操作失败: {str(e)}")


@router.get("/performance/summary")
async def get_operations_summary():
    """获取所有操作的摘要
    
    Returns:
        操作摘要字典
    """
    logger.debug("获取操作摘要")
    
    try:
        summary = performance_monitor.get_operations_summary()
        
        return ApiResponse(
            success=True,
            data=summary,
            message="获取操作摘要成功"
        )
    except Exception as e:
        logger.error(f"获取操作摘要失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取操作摘要失败: {str(e)}")


@router.delete("/performance/clear")
async def clear_performance_metrics():
    """清空性能指标"""
    logger.info("清空性能指标")
    
    try:
        performance_monitor.clear()
        
        return ApiResponse(
            success=True,
            data={"cleared_at": datetime.now().isoformat()},
            message="性能指标已清空"
        )
    except Exception as e:
        logger.error(f"清空性能指标失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"清空性能指标失败: {str(e)}")


@router.get("/levels")
async def get_log_levels():
    """获取支持的日志级别
    
    Returns:
        日志级别列表
    """
    levels = [{"name": level.name, "value": level.value} for level in LogLevel]
    
    return ApiResponse(
        success=True,
        data={"levels": levels},
        message="获取日志级别成功"
    )
