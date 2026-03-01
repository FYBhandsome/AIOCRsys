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
from typing import Optional, List
import traceback
import logging
import sys

logger = logging.getLogger(__name__)

_api_router = None
_loaded_modules: List[str] = []


def _load_all_routers() -> APIRouter:
    """加载所有路由模块"""
    global _api_router, _loaded_modules
    
    if _api_router is not None:
        return _api_router
    
    print("[Routes] 开始加载路由模块...", file=sys.stderr)
    
    _api_router = APIRouter()
    _loaded_modules = []
    
    router_modules = [
        ("certificate_routes", "证书管理"),
        ("chat_routes", "AI对话"),
        ("document_routes", "文档管理"),
        ("system_routes", "系统管理"),
        ("prompt_routes", "提示词管理"),
        ("vector_db_routes", "向量数据库"),
        ("log_routes", "日志管理"),
        ("cache_routes", "缓存管理"),
    ]
    
    for module_name, desc in router_modules:
        try:
            print(f"[Routes] 加载 {module_name}...", file=sys.stderr)
            full_module = f"app.api.{module_name}"
            module = __import__(full_module, fromlist=["router"])
            router = getattr(module, "router")
            _api_router.include_router(router)
            _loaded_modules.append(module_name)
            print(f"[Routes] [OK] {module_name} 路由已加载 ({desc})", file=sys.stderr)
        except Exception as e:
            print(f"[Routes] [FAIL] {module_name} 路由加载失败: {e}", file=sys.stderr)
            traceback.print_exc()
    
    print(f"[Routes] 路由加载完成，共 {len(_loaded_modules)} 个模块", file=sys.stderr)
    return _api_router


def get_api_router() -> APIRouter:
    """
    获取主API路由实例
    
    Returns:
        APIRouter: 配置好的主路由实例
    """
    return _load_all_routers()


def get_loaded_modules() -> List[str]:
    """获取已加载的模块列表"""
    return _loaded_modules.copy()


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
