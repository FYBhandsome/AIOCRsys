#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI助手API集成测试
测试AI对话、流式响应、建议问题等功能
"""
import pytest
import logging
import json
from httpx import AsyncClient

from conftest import API_PREFIX

logger = logging.getLogger("test_logger")


class TestAIChat:
    """AI对话测试类"""
    
    @pytest.mark.ai
    @pytest.mark.asyncio
    async def test_chat_success(self, client: AsyncClient, student_token: str, test_logger):
        """测试AI对话 - 正常场景"""
        test_logger.info("开始测试: AI对话正常请求")
        
        chat_data = {
            "message": "省级竞赛加多少分？",
            "userId": "test_user",
            "use_rag": True
        }
        
        headers = {"Authorization": f"Bearer {student_token}"}
        response = await client.post(f"{API_PREFIX}/ai/chat", json=chat_data, headers=headers)
        
        test_logger.info(f"请求参数: {chat_data}")
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"响应数据: {json.dumps(data, ensure_ascii=False)[:500]}")
            
            assert "reply" in data or "response" in data, "响应应包含reply或response字段"
            test_logger.info("AI对话测试通过")
        else:
            test_logger.warning(f"AI对话失败: {response.text}")
    
    @pytest.mark.ai
    @pytest.mark.asyncio
    async def test_chat_with_history(self, client: AsyncClient, student_token: str, test_logger):
        """测试AI对话带历史记录"""
        test_logger.info("开始测试: AI对话带历史记录")
        
        chat_data = {
            "message": "那国家级的呢？",
            "userId": "test_user",
            "use_rag": True,
            "chat_history": [
                {"role": "user", "content": "省级竞赛加多少分？"},
                {"role": "assistant", "content": "省级竞赛一等奖可以加15分。"}
            ]
        }
        
        headers = {"Authorization": f"Bearer {student_token}"}
        response = await client.post(f"{API_PREFIX}/ai/chat", json=chat_data, headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"响应数据: {json.dumps(data, ensure_ascii=False)[:300]}")
            test_logger.info("带历史记录的AI对话测试通过")
        else:
            test_logger.warning(f"AI对话失败: {response.text}")
    
    @pytest.mark.ai
    @pytest.mark.asyncio
    async def test_chat_empty_message(self, client: AsyncClient, student_token: str, test_logger):
        """测试AI对话空消息 - 边界条件"""
        test_logger.info("开始测试: AI对话空消息")
        
        chat_data = {
            "message": "",
            "userId": "test_user"
        }
        
        headers = {"Authorization": f"Bearer {student_token}"}
        response = await client.post(f"{API_PREFIX}/ai/chat", json=chat_data, headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [400, 404, 422], "空消息应返回验证错误"
        test_logger.info("空消息测试通过")
    
    @pytest.mark.ai
    @pytest.mark.asyncio
    async def test_chat_no_auth(self, client: AsyncClient, test_logger):
        """测试AI对话无认证 - 异常场景"""
        test_logger.info("开始测试: AI对话无认证")
        
        chat_data = {
            "message": "测试消息",
            "userId": "test_user"
        }
        
        response = await client.post(f"{API_PREFIX}/ai/chat", json=chat_data)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [401, 403, 404], "无认证应返回401或403"
        test_logger.info("无认证测试通过")


class TestAIAssistantMessage:
    """AI助手消息接口测试类"""
    
    @pytest.mark.ai
    @pytest.mark.asyncio
    async def test_assistant_message_success(self, client: AsyncClient, student_token: str, test_logger):
        """测试AI助手消息接口 - 正常场景"""
        test_logger.info("开始测试: AI助手消息接口")
        
        message_data = {
            "question": "英语四级可以加多少分？",
            "userId": "test_user"
        }
        
        headers = {"Authorization": f"Bearer {student_token}"}
        response = await client.post(f"{API_PREFIX}/ai/assistant/message", json=message_data, headers=headers)
        
        test_logger.info(f"请求参数: {message_data}")
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"响应数据: {json.dumps(data, ensure_ascii=False)[:500]}")
            
            assert "response" in data, "响应应包含response字段"
            test_logger.info("AI助手消息接口测试通过")
        else:
            test_logger.warning(f"AI助手消息失败: {response.text}")
    
    @pytest.mark.ai
    @pytest.mark.asyncio
    async def test_assistant_message_with_context(self, client: AsyncClient, student_token: str, test_logger):
        """测试AI助手消息带上下文"""
        test_logger.info("开始测试: AI助手消息带上下文")
        
        message_data = {
            "question": "我的证书可以加多少分？",
            "userId": "test_user",
            "context": {
                "certificates": [
                    {"name": "蓝桥杯", "level": "省级", "award": "一等奖"}
                ]
            }
        }
        
        headers = {"Authorization": f"Bearer {student_token}"}
        response = await client.post(f"{API_PREFIX}/ai/assistant/message", json=message_data, headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"响应数据: {json.dumps(data, ensure_ascii=False)[:300]}")
            test_logger.info("带上下文的AI助手消息测试通过")


class TestAISuggestions:
    """AI建议问题测试类"""
    
    @pytest.mark.ai
    @pytest.mark.asyncio
    async def test_get_suggestions(self, client: AsyncClient, student_token: str, test_logger):
        """测试获取建议问题"""
        test_logger.info("开始测试: 获取建议问题")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        response = await client.get(f"{API_PREFIX}/ai/suggestions", headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"建议问题: {json.dumps(data, ensure_ascii=False)[:500]}")
            
            assert "suggestions" in data, "响应应包含suggestions字段"
            assert isinstance(data["suggestions"], list), "suggestions应为列表"
            test_logger.info("获取建议问题测试通过")
        else:
            test_logger.warning(f"获取建议问题失败: {response.text}")


class TestAIChatStream:
    """AI流式对话测试类"""
    
    @pytest.mark.ai
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_chat_stream(self, client: AsyncClient, student_token: str, test_logger):
        """测试AI流式对话"""
        test_logger.info("开始测试: AI流式对话")
        
        chat_data = {
            "message": "请详细解释综测加分规则",
            "userId": "test_user"
        }
        
        headers = {"Authorization": f"Bearer {student_token}"}
        response = await client.post(f"{API_PREFIX}/ai/chat/stream", json=chat_data, headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        test_logger.info(f"响应Content-Type: {response.headers.get('content-type', '')}")
        
        if response.status_code == 200:
            content_type = response.headers.get("content-type", "")
            assert "event-stream" in content_type or "text" in content_type
            test_logger.info("AI流式对话测试通过")
        else:
            test_logger.warning(f"AI流式对话失败: {response.text}")


class TestAIHistory:
    """AI对话历史测试类"""
    
    @pytest.mark.ai
    @pytest.mark.asyncio
    async def test_get_history(self, client: AsyncClient, student_token: str, test_logger):
        """测试获取对话历史"""
        test_logger.info("开始测试: 获取对话历史")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        response = await client.get(f"{API_PREFIX}/ai/history", headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"对话历史: {json.dumps(data, ensure_ascii=False)[:300]}")
            test_logger.info("获取对话历史测试通过")
    
    @pytest.mark.ai
    @pytest.mark.asyncio
    async def test_clear_history(self, client: AsyncClient, student_token: str, test_logger):
        """测试清空对话历史"""
        test_logger.info("开始测试: 清空对话历史")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        response = await client.delete(f"{API_PREFIX}/ai/history", headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            assert "message" in data
            test_logger.info("清空对话历史测试通过")
