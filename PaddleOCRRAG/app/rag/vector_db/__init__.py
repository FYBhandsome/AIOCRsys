"""
向量数据库模块

本模块提供向量数据库相关的功能，包括基础向量数据库类和规则向量数据库。
"""

def __getattr__(name):
    """延迟导入，避免在导入时加载chromadb"""
    if name == 'BaseVectorDB':
        from .base_vector_db import BaseVectorDB
        return BaseVectorDB
    elif name == 'RuleVectorDB':
        from .vector_db import RuleVectorDB
        return RuleVectorDB
    elif name == 'get_vector_db':
        from .vector_db import get_vector_db
        return get_vector_db
    elif name == 'CategoryReranker':
        from .reranker import CategoryReranker
        return CategoryReranker
    elif name == 'RerankedResult':
        from .reranker import RerankedResult
        return RerankedResult
    elif name == 'get_category_reranker':
        from .reranker import get_category_reranker
        return get_category_reranker
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    'BaseVectorDB',
    'RuleVectorDB',
    'get_vector_db',
    'CategoryReranker',
    'RerankedResult',
    'get_category_reranker'
]