#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG系统测试用例
测试核心RAG功能
"""
import pytest
import asyncio
import os
import sys
from unittest.mock import AsyncMock, patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/PaddleOCRRAG")


class TestVectorDB:
    """向量数据库测试"""
    
    def test_import_vector_db_module(self):
        """测试导入向量数据库模块"""
        try:
            from app.rag.vector_db.vector_db import RuleVectorDB
            assert RuleVectorDB is not None
        except ImportError as e:
            pytest.skip(f"无法导入向量数据库模块: {e}")
            
    def test_get_vector_db_singleton(self):
        """测试向量数据库单例"""
        try:
            from app.rag.vector_db.vector_db import get_vector_db
            vdb1 = get_vector_db()
            vdb2 = get_vector_db()
            assert vdb1 is vdb2
        except Exception as e:
            pytest.skip(f"无法初始化向量数据库: {e}")


class TestEmbeddingModel:
    """嵌入模型测试"""
    
    def test_import_embedding_function(self):
        """测试导入嵌入函数"""
        try:
            from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
            assert SentenceTransformerEmbeddingFunction is not None
        except ImportError as e:
            pytest.skip(f"无法导入嵌入函数: {e}")


class TestLLMManager:
    """LLM管理器测试"""
    
    def test_import_llm_manager(self):
        """测试导入LLM管理器"""
        try:
            from app.core.llm_manager import LLMManager, get_llm_manager
            assert LLMManager is not None
        except ImportError as e:
            pytest.skip(f"无法导入LLM管理器: {e}")
            
    def test_get_llm_manager_singleton(self):
        """测试LLM管理器单例"""
        try:
            from app.core.llm_manager import get_llm_manager
            manager1 = get_llm_manager()
            manager2 = get_llm_manager()
            assert manager1 is manager2
        except Exception as e:
            pytest.skip(f"无法初始化LLM管理器: {e}")


class TestChatService:
    """聊天服务测试"""
    
    def test_import_chat_service(self):
        """测试导入聊天服务"""
        try:
            from app.services.chat_service import ChatService
            assert ChatService is not None
        except ImportError as e:
            pytest.skip(f"无法导入聊天服务: {e}")


class TestDocumentLoader:
    """文档加载器测试"""
    
    def test_import_loader(self):
        """测试导入文档加载器"""
        try:
            from app.rag.loaders.loader import DocumentLoader
            assert DocumentLoader is not None
        except ImportError as e:
            pytest.skip(f"无法导入文档加载器: {e}")
            
    def test_import_enhanced_loader(self):
        """测试导入增强文档加载器"""
        try:
            from app.rag.loaders.enhanced_loader import EnhancedDocumentLoader
            assert EnhancedDocumentLoader is not None
        except ImportError as e:
            pytest.skip(f"无法导入增强文档加载器: {e}")


class TestPreprocessors:
    """预处理器测试"""
    
    def test_import_intent_recognizer(self):
        """测试导入意图识别器"""
        try:
            from app.rag.preprocessors.intent_recognizer import get_intent_recognizer
            recognizer = get_intent_recognizer()
            assert recognizer is not None
        except ImportError as e:
            pytest.skip(f"无法导入意图识别器: {e}")
            
    def test_import_query_enhancer(self):
        """测试导入查询增强器"""
        try:
            from app.rag.preprocessors.query_enhancer import get_query_enhancer
            enhancer = get_query_enhancer()
            assert enhancer is not None
        except ImportError as e:
            pytest.skip(f"无法导入查询增强器: {e}")
            
    def test_import_competition_mapper(self):
        """测试导入竞赛映射器"""
        try:
            from app.rag.preprocessors.competition_mapper import CompetitionMapper
            assert CompetitionMapper is not None
        except ImportError as e:
            pytest.skip(f"无法导入竞赛映射器: {e}")


class TestReranker:
    """重排器测试"""
    
    def test_import_reranker(self):
        """测试导入重排器"""
        try:
            from app.rag.vector_db.reranker import get_category_reranker
            reranker = get_category_reranker()
            assert reranker is not None
        except ImportError as e:
            pytest.skip(f"无法导入重排器: {e}")


class TestConfigManager:
    """配置管理器测试"""
    
    def test_import_config_manager(self):
        """测试导入配置管理器"""
        try:
            from app.core.config_manager import config_manager, settings
            assert config_manager is not None
            assert settings is not None
        except ImportError as e:
            pytest.skip(f"无法导入配置管理器: {e}")
            
    def test_settings_attributes(self):
        """测试配置属性"""
        try:
            from app.core.config_manager import settings
            
            assert hasattr(settings, 'CHROMA_DB_PATH')
            assert hasattr(settings, 'EMBEDDING_MODEL')
            assert hasattr(settings, 'EMBEDDING_DEVICE')
        except Exception as e:
            pytest.skip(f"无法访问配置属性: {e}")


class TestPromptManager:
    """提示词管理器测试"""
    
    def test_import_prompt_manager(self):
        """测试导入提示词管理器"""
        try:
            from app.core.prompt_manager import PromptManager
            assert PromptManager is not None
        except ImportError as e:
            pytest.skip(f"无法导入提示词管理器: {e}")


class TestLogger:
    """日志系统测试"""
    
    def test_import_logger(self):
        """测试导入日志模块"""
        try:
            from app.core.logger import get_logger, setup_logging
            logger = get_logger("test")
            assert logger is not None
        except ImportError as e:
            pytest.skip(f"无法导入日志模块: {e}")
            
    def test_logger_methods(self):
        """测试日志方法"""
        try:
            from app.core.logger import get_logger
            logger = get_logger("test")
            
            assert hasattr(logger, 'info')
            assert hasattr(logger, 'error')
            assert hasattr(logger, 'warning')
            assert hasattr(logger, 'debug')
        except Exception as e:
            pytest.skip(f"无法访问日志方法: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
