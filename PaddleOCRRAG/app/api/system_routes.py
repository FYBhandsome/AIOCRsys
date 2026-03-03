"""
系统管理相关API路由
"""
import logging
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from app.models import ApiResponse, LLMConfigUpdateRequest
from app.core.dependencies import DependencyContainer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/system", tags=["系统管理"])

# 创建依赖注入容器实例
container = DependencyContainer()


@router.get("/info")
async def get_system_info():
    """获取系统信息"""
    try:
        system_service = container.get_system_service()
        result = system_service.get_system_info()
        
        return ApiResponse(
            success=True,
            data=result,
            message="获取系统信息成功"
        )
    except Exception as e:
        logger.error(f"获取系统信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取系统信息失败: {str(e)}")


@router.get("/health")
async def health_check():
    """健康检查"""
    try:
        system_service = container.get_system_service()
        result = system_service.health_check()
        healthy = result["healthy"]
        
        return JSONResponse(
            status_code=200 if healthy else 503,
            content={
                "success": healthy,
                "data": result,
                "message": "系统健康" if healthy else "系统部分组件异常"
            }
        )
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")


@router.post("/llm/test")
async def test_llm_connection():
    """测试LLM连接"""
    try:
        system_service = container.get_system_service()
        result = system_service.test_llm_connection()
        
        return ApiResponse(
            success=True,
            data=result,
            message="LLM连接测试成功"
        )
    except Exception as e:
        logger.error(f"LLM连接测试失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "message": "LLM连接测试失败"
            }
        )


@router.get("/vector_db/stats")
async def get_vector_db_stats():
    """获取向量数据库统计信息"""
    try:
        system_service = container.get_system_service()
        result = system_service.get_vector_db_stats()
        
        return ApiResponse(
            success=True,
            data=result,
            message="获取向量数据库统计信息成功"
        )
    except Exception as e:
        logger.error(f"获取向量数据库统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取向量数据库统计信息失败: {str(e)}")


@router.post("/vector_db/rebuild")
async def rebuild_vector_db():
    """重建向量数据库"""
    try:
        system_service = container.get_system_service()
        result = system_service.rebuild_vector_db()
        
        return ApiResponse(
            success=True,
            data=result,
            message="向量数据库重建成功"
        )
    except Exception as e:
        logger.error(f"向量数据库重建失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"向量数据库重建失败: {str(e)}")


@router.get("/config")
async def get_system_config():
    """获取系统配置"""
    try:
        system_service = container.get_system_service()
        result = system_service.get_system_config()
        
        return ApiResponse(
            success=True,
            data=result,
            message="获取系统配置成功"
        )
    except Exception as e:
        logger.error(f"获取系统配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取系统配置失败: {str(e)}")


@router.put("/config")
async def update_system_config(config_data: Dict[str, Any]):
    """更新系统配置"""
    try:
        system_service = container.get_system_service()
        result = system_service.update_system_config(config_data)
        
        return ApiResponse(
            success=True,
            data=result,
            message="系统配置更新成功"
        )
    except Exception as e:
        logger.error(f"系统配置更新失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"系统配置更新失败: {str(e)}")


@router.get("/llm/config")
async def get_llm_config():
    """获取LLM配置"""
    try:
        system_service = container.get_system_service()
        result = system_service.config_manager.get_llm_config()
        
        return ApiResponse(
            success=True,
            data=result,
            message="获取LLM配置成功"
        )
    except Exception as e:
        logger.error(f"获取LLM配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取LLM配置失败: {str(e)}")


@router.get("/model-info")
async def get_model_info():
    """获取当前使用的模型信息"""
    try:
        from app.core.config_manager import settings
        
        return {
            "model_name": settings.XUNFEI_MODEL_ID or "xop3qwen1b7",
            "provider": "xunfei",
            "api_base_url": settings.XUNFEI_API_URL or "",
            "temperature": settings.XUNFEI_TEMPERATURE or 0.1,
            "max_tokens": settings.XUNFEI_MAX_TOKENS or 1024
        }
    except Exception as e:
        logger.error(f"获取模型信息失败: {str(e)}")
        return {
            "model_name": "未知",
            "provider": "未知",
            "error": str(e)
        }


@router.put("/llm/config")
async def update_llm_config(request: LLMConfigUpdateRequest):
    """更新LLM配置"""
    try:
        system_service = container.get_system_service()
        result = system_service.config_manager.update_llm_config(
            provider=request.provider,
            api_key=request.api_key,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        return ApiResponse(
            success=True,
            data={
                **result,
                "updated_at": datetime.now().isoformat()
            },
            message="LLM配置更新成功"
        )
    except Exception as e:
        logger.error(f"LLM配置更新失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"LLM配置更新失败: {str(e)}")


@router.post("/llm/config/reset")
async def reset_llm_config():
    """重置LLM配置为默认值"""
    try:
        system_service = container.get_system_service()
        result = system_service.config_manager.reset_llm_config()
        
        return ApiResponse(
            success=True,
            data=result,
            message="LLM配置已重置为默认值"
        )
    except Exception as e:
        logger.error(f"重置LLM配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"重置LLM配置失败: {str(e)}")


@router.get("/llm/config/validate")
async def validate_llm_config():
    """验证LLM配置"""
    try:
        system_service = container.get_system_service()
        result = system_service.config_manager.validate_llm_config()
        
        return ApiResponse(
            success=True,
            data=result,
            message="LLM配置验证成功"
        )
    except Exception as e:
        logger.error(f"验证LLM配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"验证LLM配置失败: {str(e)}")
