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

# 创建主路由
api_router = APIRouter()

# 导入各模块的路由
from app.api.certificate_routes import router as certificate_router
from app.api.chat_routes import router as chat_router
from app.api.document_routes import router as document_router
from app.api.system_routes import router as system_router
from app.api.prompt_routes import router as prompt_router

# 注册各个功能模块的路由
api_router.include_router(certificate_router)
api_router.include_router(chat_router)
api_router.include_router(document_router)
api_router.include_router(system_router)
api_router.include_router(prompt_router)

# 初始化函数

def init_optimized_components() -> bool:
    """
    初始化优化后的组件
    
    此函数负责初始化所有需要的核心组件，确保它们在API服务启动时被正确加载。
    统一管理组件初始化，避免在各个路由文件中重复初始化服务实例，提高代码一致性。
    
    Returns:
        bool: 初始化是否成功
    """
    try:
        print("正在初始化优化组件...")
        
        # 初始化向量数据库
        try:
            from app.rag.vector_db import get_vector_db
            vector_db = get_vector_db()
            print(f"向量数据库初始化成功: {vector_db.collection_name}")
        except Exception as vdb_error:
            print(f"向量数据库初始化失败: {str(vdb_error)}")
            raise
        
        # 初始化配置管理器
        try:
            from app.core.config_manager import config_manager
            config = config_manager.get_config()
            print("配置管理器初始化成功")
        except Exception as config_error:
            print(f"配置管理器初始化失败: {str(config_error)}")
            raise
            
        # 初始化文档管理器
        try:
            from app.core.document_manager import DocumentManager
            doc_manager = DocumentManager()
            print("文档管理器初始化成功")
        except Exception as doc_error:
            print(f"文档管理器初始化失败: {str(doc_error)}")
            raise
            
        print("优化组件初始化完成")
        return True
    except Exception as e:
        print(f"优化组件初始化失败: {str(e)}")
        return False


def get_api_router() -> APIRouter:
    """
    获取主API路由实例
    
    Returns:
        APIRouter: 配置好的主路由实例
    """
    return api_router
