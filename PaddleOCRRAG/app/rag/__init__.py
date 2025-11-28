"""
RAG模块
包含检索增强生成相关的功能组件
"""

# 导入核心组件
from app.core.llm_manager import llm_manager
from app.core.prompt_manager import prompt_manager

# 导入向量数据库组件
from .vector_db import get_vector_db

# 导入文档加载器
from .loaders.loader import RuleDocumentLoader

# 注意：链式处理、竞赛相关功能和工具函数已移除，如需要可重新实现

__all__ = [
    # 核心组件
    "llm_manager",
    "prompt_manager",
    
    # 向量数据库
    "get_vector_db",
    
    # 文档加载器
    "RuleDocumentLoader"
]