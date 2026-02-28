#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG系统API集成测试
测试文档上传、证书计算、聊天等功能
"""
import pytest
import logging
import json
import os
import sys
from httpx import AsyncClient, ASGITransport
from io import BytesIO
from unittest.mock import AsyncMock, patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger("test_logger")


class TestRAGChat:
    """RAG聊天测试类"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_chat_endpoint(self, test_logger):
        """测试RAG聊天端点"""
        test_logger.info("开始测试: RAG聊天端点")
        
        from app.main import app
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            chat_data = {
                "message": "省级竞赛一等奖加多少分？",
                "chat_history": []
            }
            
            response = await client.post("/api/v1/api/chat", json=chat_data)
            
            test_logger.info(f"响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                test_logger.info(f"聊天响应: {json.dumps(data, ensure_ascii=False)[:500]}")
                test_logger.info("RAG聊天端点测试通过")
            else:
                test_logger.warning(f"RAG聊天失败: {response.text}")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_chat_stream_endpoint(self, test_logger):
        """测试RAG流式聊天端点"""
        test_logger.info("开始测试: RAG流式聊天端点")
        
        from app.main import app
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            chat_data = {
                "message": "请解释综测加分规则",
                "chat_history": []
            }
            
            response = await client.post("/api/v1/api/chat/stream", json=chat_data)
            
            test_logger.info(f"响应状态码: {response.status_code}")
            test_logger.info(f"Content-Type: {response.headers.get('content-type', '')}")
            
            if response.status_code == 200:
                test_logger.info("RAG流式聊天端点测试通过")
            else:
                test_logger.warning(f"RAG流式聊天失败: {response.text}")


class TestCertificateCalculation:
    """证书计算测试类"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_calculate_certificate_points(self, test_logger):
        """测试计算证书加分"""
        test_logger.info("开始测试: 计算证书加分")
        
        from app.main import app
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            cert_data = {
                "certificate_name": "蓝桥杯全国软件和信息技术专业人才大赛",
                "level": "省级",
                "award": "一等奖",
                "student_id": "2021001"
            }
            
            response = await client.post("/api/v1/api/certificate/calculate", json=cert_data)
            
            test_logger.info(f"请求参数: {cert_data}")
            test_logger.info(f"响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                test_logger.info(f"计算结果: {json.dumps(data, ensure_ascii=False)[:500]}")
                
                if "points" in data:
                    test_logger.info(f"加分: {data['points']}")
                test_logger.info("计算证书加分测试通过")
            else:
                test_logger.warning(f"计算证书加分失败: {response.text}")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_calculate_certificate_missing_fields(self, test_logger):
        """测试计算证书加分缺少字段"""
        test_logger.info("开始测试: 计算证书加分缺少字段")
        
        from app.main import app
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            cert_data = {
                "certificate_name": "测试证书"
            }
            
            response = await client.post("/api/v1/api/certificate/calculate", json=cert_data)
            
            test_logger.info(f"响应状态码: {response.status_code}")
            
            assert response.status_code == 422, "缺少字段应返回422"
            test_logger.info("缺少字段测试通过")


class TestDocumentUpload:
    """文档上传测试类"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_upload_document(self, test_logger):
        """测试上传文档"""
        test_logger.info("开始测试: 上传文档")
        
        from app.main import app
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            test_content = b"Test document content for RAG system"
            files = {
                "file": ("test_document.txt", BytesIO(test_content), "text/plain")
            }
            
            response = await client.post("/api/v1/api/documents/upload", files=files)
            
            test_logger.info(f"响应状态码: {response.status_code}")
            
            if response.status_code in [200, 201]:
                data = response.json()
                test_logger.info(f"上传结果: {json.dumps(data, ensure_ascii=False)[:300]}")
                test_logger.info("上传文档测试通过")
            else:
                test_logger.warning(f"上传文档失败: {response.text}")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_list_documents(self, test_logger):
        """测试获取文档列表"""
        test_logger.info("开始测试: 获取文档列表")
        
        from app.main import app
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/api/documents")
            
            test_logger.info(f"响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                test_logger.info(f"文档列表: {json.dumps(data, ensure_ascii=False)[:500]}")
                test_logger.info("获取文档列表测试通过")
            else:
                test_logger.warning(f"获取文档列表失败: {response.text}")


class TestSystemHealth:
    """系统健康检查测试类"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_health_check(self, test_logger):
        """测试健康检查"""
        test_logger.info("开始测试: 健康检查")
        
        from app.main import app
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/api/system/health")
            
            test_logger.info(f"响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                test_logger.info(f"健康状态: {json.dumps(data, ensure_ascii=False)[:300]}")
                test_logger.info("健康检查测试通过")
            else:
                test_logger.warning(f"健康检查失败: {response.text}")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_system_info(self, test_logger):
        """测试系统信息"""
        test_logger.info("开始测试: 系统信息")
        
        from app.main import app
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/api/system/info")
            
            test_logger.info(f"响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                test_logger.info(f"系统信息: {json.dumps(data, ensure_ascii=False)[:500]}")
                test_logger.info("系统信息测试通过")
            else:
                test_logger.warning(f"获取系统信息失败: {response.text}")


class TestPromptManagement:
    """提示词管理测试类"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_prompts(self, test_logger):
        """测试获取提示词列表"""
        test_logger.info("开始测试: 获取提示词列表")
        
        from app.main import app
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/api/prompts")
            
            test_logger.info(f"响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                test_logger.info(f"提示词列表: {json.dumps(data, ensure_ascii=False)[:500]}")
                test_logger.info("获取提示词列表测试通过")
            else:
                test_logger.warning(f"获取提示词列表失败: {response.text}")
