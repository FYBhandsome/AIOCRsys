#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI助手API测试模块
测试AI对话、建议问题等功能
"""
import pytest
from httpx import AsyncClient

from conftest_new import API_PREFIX


@pytest.mark.asyncio
@pytest.mark.ai
class TestAIChatAPI:
    """AI对话API测试类"""
    
    async def test_ai_chat(self, client: AsyncClient, student_token: str, test_result):
        """测试AI对话"""
        test_result.start()
        
        headers = {"Authorization": f"Bearer {student_token}"}
        chat_data = {
            "message": "省级竞赛可以加多少分？",
            "use_rag": True
        }
        
        response = await client.post(
            f"{API_PREFIX}/ai/chat",
            headers=headers,
            json=chat_data
        )
        
        assert response.status_code in [200, 503], f"AI对话响应异常: {response.text}"
        data = response.json()
        assert "reply" in data or "response" in data, "响应中缺少回复内容"
        
        test_result.add_result("test_ai_chat", True, "AI对话接口正常")
        test_result.end()
    
    async def test_ai_chat_with_history(self, client: AsyncClient, student_token: str, test_result):
        """测试带历史记录的AI对话"""
        test_result.start()
        
        headers = {"Authorization": f"Bearer {student_token}"}
        chat_data = {
            "message": "那国家级呢？",
            "chat_history": [
                {"role": "user", "content": "省级竞赛可以加多少分？"},
                {"role": "assistant", "content": "省级竞赛一般可以加8分。"}
            ],
            "use_rag": True
        }
        
        response = await client.post(
            f"{API_PREFIX}/ai/chat",
            headers=headers,
            json=chat_data
        )
        
        assert response.status_code in [200, 503], f"AI对话响应异常: {response.text}"
        
        test_result.add_result("test_ai_chat_with_history", True, "带历史记录的AI对话正常")
        test_result.end()
    
    async def test_ai_chat_without_rag(self, client: AsyncClient, student_token: str, test_result):
        """测试不使用RAG的AI对话"""
        test_result.start()
        
        headers = {"Authorization": f"Bearer {student_token}"}
        chat_data = {
            "message": "你好",
            "use_rag": False
        }
        
        response = await client.post(
            f"{API_PREFIX}/ai/chat",
            headers=headers,
            json=chat_data
        )
        
        assert response.status_code in [200, 503], f"AI对话响应异常: {response.text}"
        
        test_result.add_result("test_ai_chat_without_rag", True, "不使用RAG的AI对话正常")
        test_result.end()
    
    async def test_ai_chat_unauthorized(self, client: AsyncClient, test_result):
        """测试未授权的AI对话"""
        test_result.start()
        
        chat_data = {
            "message": "测试消息",
            "use_rag": True
        }
        
        response = await client.post(
            f"{API_PREFIX}/ai/chat",
            json=chat_data
        )
        
        assert response.status_code == 401, "未授权应该返回401"
        
        test_result.add_result("test_ai_chat_unauthorized", True, "未授权正确返回401")
        test_result.end()


@pytest.mark.asyncio
@pytest.mark.ai
class TestAIAssistantAPI:
    """AI助手API测试类"""
    
    async def test_assistant_message(self, client: AsyncClient, student_token: str, test_result):
        """测试AI助手消息"""
        test_result.start()
        
        headers = {"Authorization": f"Bearer {student_token}"}
        message_data = {
            "question": "如何上传证书？"
        }
        
        response = await client.post(
            f"{API_PREFIX}/ai/assistant/message",
            headers=headers,
            json=message_data
        )
        
        assert response.status_code in [200, 503], f"AI助手消息响应异常: {response.text}"
        data = response.json()
        assert "response" in data or "reply" in data, "响应中缺少回复内容"
        
        test_result.add_result("test_assistant_message", True, "AI助手消息接口正常")
        test_result.end()
    
    async def test_get_suggestions(self, client: AsyncClient, student_token: str, test_result):
        """测试获取推荐问题"""
        test_result.start()
        
        headers = {"Authorization": f"Bearer {student_token}"}
        response = await client.get(
            f"{API_PREFIX}/ai/suggestions",
            headers=headers
        )
        
        assert response.status_code == 200, f"获取建议问题失败: {response.text}"
        data = response.json()
        assert "suggestions" in data, "响应中缺少suggestions字段"
        
        test_result.add_result("test_get_suggestions", True, f"获取到{len(data.get('suggestions', []))}个建议问题")
        test_result.end()
    
    async def test_get_chat_history(self, client: AsyncClient, student_token: str, test_result):
        """测试获取对话历史"""
        test_result.start()
        
        headers = {"Authorization": f"Bearer {student_token}"}
        response = await client.get(
            f"{API_PREFIX}/ai/history",
            headers=headers,
            params={"limit": 10}
        )
        
        assert response.status_code == 200, f"获取对话历史失败: {response.text}"
        
        test_result.add_result("test_get_chat_history", True, "获取对话历史接口正常")
        test_result.end()
    
    async def test_clear_chat_history(self, client: AsyncClient, student_token: str, test_result):
        """测试清空对话历史"""
        test_result.start()
        
        headers = {"Authorization": f"Bearer {student_token}"}
        response = await client.delete(
            f"{API_PREFIX}/ai/history",
            headers=headers
        )
        
        assert response.status_code == 200, f"清空对话历史失败: {response.text}"
        
        test_result.add_result("test_clear_chat_history", True, "清空对话历史接口正常")
        test_result.end()
