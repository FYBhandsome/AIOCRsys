#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG系统API测试模块
测试向量数据库、文档管理、聊天等功能
"""
import pytest
from httpx import AsyncClient


RAG_API_PREFIX = "/api/v1"


@pytest.mark.asyncio
@pytest.mark.rag
class TestRAGChatAPI:
    """RAG聊天API测试类"""
    
    async def test_rag_chat(self, client: AsyncClient, test_result):
        """测试RAG聊天"""
        test_result.start()
        
        chat_data = {
            "message": "省级竞赛可以加多少分？",
            "chat_history": [],
            "use_rag": True
        }
        
        response = await client.post(
            f"{RAG_API_PREFIX}/chat",
            json=chat_data
        )
        
        assert response.status_code in [200, 503], f"RAG聊天响应异常: {response.text}"
        data = response.json()
        assert "answer" in data or "response" in data or "reply" in data, "响应中缺少回复内容"
        
        test_result.add_result("test_rag_chat", True, "RAG聊天接口正常")
        test_result.end()
    
    async def test_rag_chat_with_history(self, client: AsyncClient, test_result):
        """测试带历史记录的RAG聊天"""
        test_result.start()
        
        chat_data = {
            "message": "那国家级呢？",
            "chat_history": [
                {"role": "user", "content": "省级竞赛可以加多少分？"},
                {"role": "assistant", "content": "省级竞赛一般可以加8分。"}
            ],
            "use_rag": True
        }
        
        response = await client.post(
            f"{RAG_API_PREFIX}/chat",
            json=chat_data
        )
        
        assert response.status_code in [200, 503], f"RAG聊天响应异常: {response.text}"
        
        test_result.add_result("test_rag_chat_with_history", True, "带历史记录的RAG聊天正常")
        test_result.end()


@pytest.mark.asyncio
@pytest.mark.rag
class TestRAGSystemAPI:
    """RAG系统API测试类"""
    
    async def test_get_system_info(self, client: AsyncClient, test_result):
        """测试获取系统信息"""
        test_result.start()
        
        response = await client.get(f"{RAG_API_PREFIX}/system/info")
        
        assert response.status_code == 200, f"获取系统信息失败: {response.text}"
        data = response.json()
        
        test_result.add_result("test_get_system_info", True, "获取系统信息成功")
        test_result.end()
    
    async def test_get_system_health(self, client: AsyncClient, test_result):
        """测试系统健康检查"""
        test_result.start()
        
        response = await client.get(f"{RAG_API_PREFIX}/system/health")
        
        assert response.status_code == 200, f"健康检查失败: {response.text}"
        data = response.json()
        assert "status" in data, "响应中缺少status字段"
        
        test_result.add_result("test_get_system_health", True, f"系统状态: {data.get('status', 'unknown')}")
        test_result.end()
    
    async def test_get_vector_db_stats(self, client: AsyncClient, test_result):
        """测试获取向量数据库统计"""
        test_result.start()
        
        response = await client.get(f"{RAG_API_PREFIX}/system/vector_db/stats")
        
        assert response.status_code in [200, 503], f"获取向量数据库统计失败: {response.text}"
        
        test_result.add_result("test_get_vector_db_stats", True, "获取向量数据库统计成功")
        test_result.end()


@pytest.mark.asyncio
@pytest.mark.rag
class TestRAGDocumentAPI:
    """RAG文档API测试类"""
    
    async def test_get_documents(self, client: AsyncClient, test_result):
        """测试获取文档列表"""
        test_result.start()
        
        response = await client.get(f"{RAG_API_PREFIX}/documents")
        
        assert response.status_code in [200, 503], f"获取文档列表失败: {response.text}"
        
        test_result.add_result("test_get_documents", True, "获取文档列表成功")
        test_result.end()
    
    async def test_get_documents_with_category(self, client: AsyncClient, test_result):
        """测试按类别获取文档列表"""
        test_result.start()
        
        response = await client.get(
            f"{RAG_API_PREFIX}/documents",
            params={"category": "综测规则"}
        )
        
        assert response.status_code in [200, 503], f"按类别获取文档列表失败: {response.text}"
        
        test_result.add_result("test_get_documents_with_category", True, "按类别获取文档列表成功")
        test_result.end()


@pytest.mark.asyncio
@pytest.mark.rag
class TestRAGLLMAPI:
    """RAG LLM配置API测试类"""
    
    async def test_get_llm_config(self, client: AsyncClient, test_result):
        """测试获取LLM配置"""
        test_result.start()
        
        response = await client.get(f"{RAG_API_PREFIX}/system/llm/config")
        
        assert response.status_code in [200, 503], f"获取LLM配置失败: {response.text}"
        
        test_result.add_result("test_get_llm_config", True, "获取LLM配置成功")
        test_result.end()
    
    async def test_test_llm_connection(self, client: AsyncClient, test_result):
        """测试LLM连接测试"""
        test_result.start()
        
        response = await client.post(f"{RAG_API_PREFIX}/system/llm/test")
        
        assert response.status_code in [200, 503], f"LLM连接测试失败: {response.text}"
        
        test_result.add_result("test_test_llm_connection", True, "LLM连接测试接口正常")
        test_result.end()


@pytest.mark.asyncio
@pytest.mark.rag
class TestRAGPromptAPI:
    """RAG提示词API测试类"""
    
    async def test_get_prompts(self, client: AsyncClient, test_result):
        """测试获取提示词配置"""
        test_result.start()
        
        response = await client.get(f"{RAG_API_PREFIX}/prompts")
        
        assert response.status_code in [200, 503], f"获取提示词配置失败: {response.text}"
        
        test_result.add_result("test_get_prompts", True, "获取提示词配置成功")
        test_result.end()
