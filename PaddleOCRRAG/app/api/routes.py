"""
统一API路由管理模块
管理和组织所有API端点，提供依赖注入支持

此模块负责:
1. 创建和配置主API路由
2. 集中注册所有子路由
3. 提供组件初始化和路由获取功能
4. 确保API路由的一致性和可维护性
"""
from fastapi import APIRouter
from typing import Optional
from app.core.logger import get_logger

logger = get_logger(__name__)

api_router = APIRouter()

try:
    from app.api.certificate_routes import router as certificate_router
    api_router.include_router(certificate_router)
    logger.info("证书路由已加载")
except Exception as e:
    logger.warning(f"证书路由加载失败: {e}")

try:
    from app.api.chat_routes import router as chat_router
    api_router.include_router(chat_router)
    logger.info("聊天路由已加载")
except Exception as e:
    logger.warning(f"聊天路由加载失败: {e}")

try:
    from app.api.document_routes import router as document_router
    api_router.include_router(document_router)
    logger.info("文档路由已加载")
except Exception as e:
    logger.warning(f"文档路由加载失败: {e}")

try:
    from app.api.system_routes import router as system_router
    api_router.include_router(system_router)
    logger.info("系统路由已加载")
except Exception as e:
    logger.warning(f"系统路由加载失败: {e}")

try:
    from app.api.prompt_routes import router as prompt_router
    api_router.include_router(prompt_router)
    logger.info("提示词路由已加载")
except Exception as e:
    logger.warning(f"提示词路由加载失败: {e}")

try:
    from app.api.vector_db_routes import router as vector_db_router
    api_router.include_router(vector_db_router)
    logger.info("向量数据库路由已加载")
except Exception as e:
    logger.warning(f"向量数据库路由加载失败: {e}")

try:
    from app.api.log_routes import router as log_router
    api_router.include_router(log_router)
    logger.info("日志路由已加载")
except Exception as e:
    logger.warning(f"日志路由加载失败: {e}")

try:
    from app.api.cache_routes import router as cache_router
    api_router.include_router(cache_router)
    logger.info("缓存路由已加载")
except Exception as e:
    logger.warning(f"缓存路由加载失败: {e}")


def init_optimized_components() -> bool:
    """
    初始化优化组件，避免在各个路由文件中重复初始化服务实例，提高代码一致性。
    
    Returns:
        bool: 初始化是否成功
    """
    try:
        logger.info("正在初始化优化组件...")
        
        try:
            from app.rag.vector_db.vector_db import get_vector_db
            vdb = get_vector_db()
            logger.info(f"向量数据库初始化成功，文档数量: {vdb.count()}")
        except Exception as vdb_error:
            logger.warning(f"向量数据库初始化失败: {str(vdb_error)}")
        
        try:
            from app.core.config_manager import config_manager
            config_manager.load_configs()
            logger.info("配置管理器初始化成功")
        except Exception as config_error:
            logger.warning(f"配置管理器初始化失败: {str(config_error)}")
        
        try:
            from app.core.document_manager import DocumentManager
            doc_manager = DocumentManager()
            logger.info("文档管理器初始化成功")
        except Exception as doc_error:
            logger.warning(f"文档管理器初始化失败: {str(doc_error)}")
            
        logger.info("优化组件初始化完成")
        return True
    except Exception as e:
        logger.error(f"优化组件初始化失败: {str(e)}", exc_info=True)
        return False


def get_api_router() -> APIRouter:
    """
    获取主API路由实例
    
    Returns:
        APIRouter: 配置好的主路由实例
    """
    return api_router
