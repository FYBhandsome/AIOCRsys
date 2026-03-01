"""
API模块

此模块提供API路由的统一入口点。
路由模块通过routes.py按需加载，避免循环导入问题。
"""

__all__ = [
    "certificate_router",
    "chat_router", 
    "document_router",
    "system_router",
    "prompt_router",
    "vector_db_router",
    "log_router",
    "cache_router"
]
