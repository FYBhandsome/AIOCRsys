"""
RAG模块
包含检索增强生成相关的功能组件
"""

from app.core.llm_manager import llm_manager
from app.core.prompt_manager import prompt_manager

from .loaders.loader import RuleDocumentLoader
from .loaders.enhanced_loader import EnhancedRuleLoader, get_enhanced_loader

from .preprocessors import (
    get_competition_mapper,
    get_intent_recognizer,
    get_query_enhancer
)

from .utils import CATEGORY_KEYWORDS, SCORE_LIMITS

def get_vector_db(collection_name: str = "zongce_rules"):
    """延迟导入向量数据库"""
    from .vector_db import get_vector_db as _get_vector_db
    return _get_vector_db(collection_name)

def get_category_reranker():
    """延迟导入重排器"""
    from .vector_db.reranker import get_category_reranker as _get_category_reranker
    return _get_category_reranker()

__all__ = [
    "llm_manager",
    "prompt_manager",
    
    "get_vector_db",
    "get_category_reranker",
    
    "RuleDocumentLoader",
    "EnhancedRuleLoader",
    "get_enhanced_loader",
    
    "get_competition_mapper",
    "get_intent_recognizer",
    "get_query_enhancer",
    
    "CATEGORY_KEYWORDS",
    "SCORE_LIMITS"
]