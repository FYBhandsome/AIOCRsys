"""
缓存管理相关API路由
提供缓存统计、清理、配置等功能
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from app.models import ApiResponse
from app.core.cache import cache_manager
from app.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/cache", tags=["缓存管理"])


@router.get("/stats")
async def get_cache_stats():
    """获取所有缓存统计信息
    
    Returns:
        所有命名缓存的统计信息
    """
    logger.info("获取缓存统计信息")
    
    try:
        stats = cache_manager.get_all_stats()
        
        return ApiResponse(
            success=True,
            data={
                "caches": stats,
                "timestamp": datetime.now().isoformat()
            },
            message="获取缓存统计成功"
        )
    except Exception as e:
        logger.error(f"获取缓存统计失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取缓存统计失败: {str(e)}")


@router.get("/stats/{cache_name}")
async def get_named_cache_stats(cache_name: str):
    """获取指定缓存的统计信息
    
    Args:
        cache_name: 缓存名称
        
    Returns:
        指定缓存的统计信息
    """
    logger.info(f"获取缓存统计: {cache_name}")
    
    try:
        cache = cache_manager.get_cache(cache_name)
        stats = cache.get_stats()
        
        return ApiResponse(
            success=True,
            data={
                "cache_name": cache_name,
                "stats": stats,
                "timestamp": datetime.now().isoformat()
            },
            message=f"获取缓存 {cache_name} 统计成功"
        )
    except Exception as e:
        logger.error(f"获取缓存统计失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取缓存统计失败: {str(e)}")


@router.delete("/clear")
async def clear_cache(cache_name: Optional[str] = Query(None, description="缓存名称，不指定则清空所有")):
    """清空缓存
    
    Args:
        cache_name: 缓存名称，不指定则清空所有缓存
        
    Returns:
        清空结果
    """
    logger.info(f"清空缓存: {cache_name or '所有'}")
    
    try:
        if cache_name:
            cache_manager.clear(cache_name)
            message = f"缓存 {cache_name} 已清空"
        else:
            cache_manager.clear_all()
            message = "所有缓存已清空"
        
        return ApiResponse(
            success=True,
            data={
                "cache_name": cache_name,
                "cleared_at": datetime.now().isoformat()
            },
            message=message
        )
    except Exception as e:
        logger.error(f"清空缓存失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"清空缓存失败: {str(e)}")


@router.delete("/clear/{cache_name}")
async def clear_named_cache(cache_name: str):
    """清空指定缓存
    
    Args:
        cache_name: 缓存名称
        
    Returns:
        清空结果
    """
    logger.info(f"清空缓存: {cache_name}")
    
    try:
        cache_manager.clear(cache_name)
        
        return ApiResponse(
            success=True,
            data={
                "cache_name": cache_name,
                "cleared_at": datetime.now().isoformat()
            },
            message=f"缓存 {cache_name} 已清空"
        )
    except Exception as e:
        logger.error(f"清空缓存失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"清空缓存失败: {str(e)}")


@router.get("/health")
async def cache_health_check():
    """缓存健康检查
    
    Returns:
        缓存系统健康状态
    """
    logger.debug("缓存健康检查")
    
    try:
        stats = cache_manager.get_all_stats()
        
        total_hits = sum(s.get("hits", 0) for s in stats.values())
        total_misses = sum(s.get("misses", 0) for s in stats.values())
        total_requests = total_hits + total_misses
        
        hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "healthy": True,
            "total_caches": len(stats),
            "total_hits": total_hits,
            "total_misses": total_misses,
            "hit_rate": f"{hit_rate:.2f}%",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"缓存健康检查失败: {str(e)}", exc_info=True)
        return {
            "healthy": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
