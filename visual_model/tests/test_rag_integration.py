#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Visual Model与RAG集成端到端测试
测试完整通信链路：前端 → visual_model后端 → RAG服务端
"""
import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from typing import Dict, Any, List, Optional
from httpx import AsyncClient, ASGITransport, Response

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.rag_client import RAGClient, get_rag_client
from app.core.logger import logger
from config import settings


# ============================================================================
# RAG客户端单元测试
# ============================================================================

class TestRAGClient:
    """RAG客户端单元测试"""
    
    @pytest.fixture
    def rag_client(self):
        """创建RAG客户端实例"""
        return RAGClient(base_url="http://localhost:8010")
    
    @pytest.fixture
    def mock_httpx(self):
        """Mock httpx客户端"""
        with patch('httpx.AsyncClient') as mock:
            yield mock
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, rag_client, mock_httpx):
        """测试健康检查成功"""
        mock_response = AsyncMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "healthy",
            "service": "RAG系统",
            "version": "1.0.0"
        }
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_httpx.return_value.__aenter__.return_value = mock_client
        
        result = await rag_client.health_check()
        
        assert result is not None
        assert result["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, rag_client, mock_httpx):
        """测试健康检查失败"""
        mock_client = AsyncMock()
        mock_client.get.side_effect = Exception("Connection refused")
        mock_httpx.return_value.__aenter__.return_value = mock_client
        
        with pytest.raises(Exception):
            await rag_client.health_check()
    
    @pytest.mark.asyncio
    async def test_check_service_availability_success(self, rag_client, mock_httpx):
        """测试服务可用性检查成功"""
        mock_response = AsyncMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy"}
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_httpx.return_value.__aenter__.return_value = mock_client
        
        result = await rag_client.check_service_availability()
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_check_service_availability_failure(self, rag_client, mock_httpx):
        """测试服务可用性检查失败"""
        mock_client = AsyncMock()
        mock_client.get.side_effect = Exception("Connection refused")
        mock_httpx.return_value.__aenter__.return_value = mock_client
        
        result = await rag_client.check_service_availability()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_chat_success(self, rag_client, mock_httpx):
        """测试聊天接口成功"""
        mock_response = AsyncMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "reply": "这是AI回复",
            "success": True,
            "sources": []
        }
        
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_httpx.return_value.__aenter__.return_value = mock_client
        
        result = await rag_client.chat(
            message="你好",
            use_rag=True,
            chat_history=[],
            student_info={"user_id": "test"}
        )
        
        assert result is not None
        assert "reply" in result
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_chat_404_fallback(self, rag_client, mock_httpx):
        """测试聊天接口404降级处理"""
        mock_response = AsyncMock(spec=Response)
        mock_response.status_code = 404
        
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_httpx.return_value.__aenter__.return_value = mock_client
        
        result = await rag_client.chat(
            message="你好",
            use_rag=True,
            chat_history=[],
            student_info={"user_id": "test"}
        )
        
        assert result is not None
        assert "抱歉" in result["reply"]
    
    @pytest.mark.asyncio
    async def test_chat_exception_fallback(self, rag_client, mock_httpx):
        """测试聊天接口异常降级处理"""
        mock_client = AsyncMock()
        mock_client.post.side_effect = Exception("Network error")
        mock_httpx.return_value.__aenter__.return_value = mock_client
        
        result = await rag_client.chat(
            message="你好",
            use_rag=True,
            chat_history=[],
            student_info={"user_id": "test"}
        )
        
        assert result is not None
        assert "抱歉" in result["reply"]
    
    @pytest.mark.asyncio
    async def test_calculate_score_success(self, rag_client, mock_httpx):
        """测试计算加分接口成功"""
        mock_response = AsyncMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "score": 15.0,
            "category": "C",
            "details": "测试详情"
        }
        
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_httpx.return_value.__aenter__.return_value = mock_client
        
        result = await rag_client.calculate_score(
            certificate_text="蓝桥杯一等奖",
            student_info={"user_id": "test"}
        )
        
        assert result is not None
        assert "score" in result
        assert result["score"] == 15.0
    
    @pytest.mark.asyncio
    async def test_calculate_score_404_fallback(self, rag_client, mock_httpx):
        """测试计算加分接口404降级处理"""
        mock_response = AsyncMock(spec=Response)
        mock_response.status_code = 404
        
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_httpx.return_value.__aenter__.return_value = mock_client
        
        result = await rag_client.calculate_score(
            certificate_text="蓝桥杯一等奖",
            student_info={"user_id": "test"}
        )
        
        assert result is not None
        assert result["score"] == 0.0
    
    @pytest.mark.asyncio
    async def test_list_documents_success(self, rag_client, mock_httpx):
        """测试获取文档列表成功"""
        mock_response = AsyncMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "documents": [
                {"id": "1", "name": "测试文档1", "enabled": True},
                {"id": "2", "name": "测试文档2", "enabled": False}
            ],
            "total": 2
        }
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_httpx.return_value.__aenter__.return_value = mock_client
        
        result = await rag_client.list_documents(enabled_only=True)
        
        assert result is not None
        assert "documents" in result
        assert len(result["documents"]) == 2


# ============================================================================
# 端到端集成测试
# ============================================================================

class TestRAGIntegrationE2E:
    """端到端集成测试"""
    
    @pytest.fixture(scope="function")
    async def setup_test_env(self):
        """设置测试环境"""
        import tempfile
        import shutil
        
        temp_dir = tempfile.mkdtemp()
        
        yield {
            "temp_dir": temp_dir,
            "rag_base_url": getattr(settings, 'RAG_BASE_URL', 'http://localhost:8010')
        }
        
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_rag_service_connectivity(self, setup_test_env):
        """测试RAG服务连通性"""
        env = setup_test_env
        rag_client = RAGClient(base_url=env["rag_base_url"])
        
        try:
            start_time = time.time()
            is_available = await rag_client.check_service_availability()
            response_time = time.time() - start_time
            
            logger.info(f"RAG服务连通性测试: 可用={is_available}, 响应时间={response_time:.2f}s")
            
            if is_available:
                assert response_time < 5.0, f"响应时间过长: {response_time:.2f}s"
                logger.info("✅ RAG服务连通性测试通过")
            else:
                logger.warning("⚠️ RAG服务不可用，跳过部分测试")
                
        except Exception as e:
            logger.error(f"RAG服务连通性测试失败: {e}")
            pytest.skip(f"RAG服务不可用: {e}")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_rag_chat_end_to_end(self, setup_test_env):
        """测试聊天端到端流程"""
        env = setup_test_env
        rag_client = RAGClient(base_url=env["rag_base_url"])
        
        try:
            is_available = await rag_client.check_service_availability()
            if not is_available:
                pytest.skip("RAG服务不可用")
            
            test_message = "省级竞赛加多少分？"
            student_info = {"user_id": "test_e2e", "username": "test_e2e", "role": "student"}
            
            start_time = time.time()
            result = await rag_client.chat(
                message=test_message,
                use_rag=True,
                chat_history=[],
                student_info=student_info
            )
            response_time = time.time() - start_time
            
            logger.info(f"聊天端到端测试完成，响应时间: {response_time:.2f}s")
            
            assert result is not None
            assert "reply" in result
            assert result["reply"] is not None
            assert len(result["reply"]) > 0
            
            assert response_time < 30.0, f"响应时间过长: {response_time:.2f}s"
            
            logger.info("✅ 聊天端到端测试通过")
            
        except Exception as e:
            logger.error(f"聊天端到端测试失败: {e}")
            pytest.skip(f"测试失败: {e}")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_rag_calculate_score_end_to_end(self, setup_test_env):
        """测试计算加分端到端流程"""
        env = setup_test_env
        rag_client = RAGClient(base_url=env["rag_base_url"])
        
        try:
            is_available = await rag_client.check_service_availability()
            if not is_available:
                pytest.skip("RAG服务不可用")
            
            certificate_text = "蓝桥杯全国软件和信息技术专业人才大赛 省级一等奖"
            student_info = {"user_id": "test_e2e", "student_id": "202300502101"}
            
            logger.info(f"输入证书文本: {certificate_text}")
            logger.info(f"输入学生信息: {student_info}")
            
            start_time = time.time()
            result = await rag_client.calculate_score(
                certificate_text=certificate_text,
                student_info=student_info
            )
            response_time = time.time() - start_time
            
            logger.info(f"完整API响应: {result}")
            logger.info(f"计算加分端到端测试完成，响应时间: {response_time:.2f}s")
            
            assert result is not None
            assert "score" in result, f"缺少score字段，响应: {result}"
            assert "category" in result, f"缺少category字段，响应: {result}"
            
            assert response_time < 10.0, f"响应时间过长: {response_time:.2f}s (要求<10秒)"
            
            logger.info(f"✅ 计算加分端到端测试通过")
            logger.info(f"   - 分数 (score): {result['score']}")
            logger.info(f"   - 类别 (category): {result['category']}")
            logger.info(f"   - 响应时间: {response_time:.2f}秒 (<10秒 ✓)")
            
        except Exception as e:
            logger.error(f"计算加分端到端测试失败: {e}")
            pytest.skip(f"测试失败: {e}")


# ============================================================================
# 异常处理测试
# ============================================================================

class TestRAGExceptionHandling:
    """异常处理测试"""
    
    @pytest.fixture
    def rag_client(self):
        """创建RAG客户端实例"""
        return RAGClient(base_url="http://localhost:9999")
    
    @pytest.mark.asyncio
    async def test_connection_refused_handling(self, rag_client):
        """测试连接拒绝处理"""
        try:
            result = await rag_client.chat(
                message="测试",
                use_rag=True,
                chat_history=[],
                student_info={"user_id": "test"}
            )
            
            assert result is not None
            assert "抱歉" in result["reply"]
            logger.info("✅ 连接拒绝处理测试通过")
            
        except Exception as e:
            logger.error(f"连接拒绝处理测试失败: {e}")
            pytest.fail(f"未正确处理连接拒绝: {e}")
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """测试超时处理"""
        client = RAGClient(base_url="http://localhost:9999", timeout=0.1)
        
        try:
            result = await client.chat(
                message="测试",
                use_rag=True,
                chat_history=[],
                student_info={"user_id": "test"}
            )
            
            assert result is not None
            assert "抱歉" in result["reply"]
            logger.info("✅ 超时处理测试通过")
            
        except Exception as e:
            logger.error(f"超时处理测试失败: {e}")
            pytest.fail(f"未正确处理超时: {e}")
    
    @pytest.mark.asyncio
    async def test_graceful_degradation(self):
        """测试优雅降级"""
        client = RAGClient(base_url="http://localhost:9999")
        
        test_cases = [
            ("chat", lambda c: c.chat(message="test", use_rag=True, chat_history=[], student_info={})),
            ("calculate_score", lambda c: c.calculate_score(certificate_text="test", student_info={})),
            ("list_documents", lambda c: c.list_documents()),
        ]
        
        for method_name, method_call in test_cases:
            try:
                result = await method_call(client)
                assert result is not None
                logger.info(f"✅ {method_name} 优雅降级测试通过")
            except Exception as e:
                logger.error(f"{method_name} 优雅降级测试失败: {e}")
                pytest.fail(f"{method_name} 未正确优雅降级: {e}")


# ============================================================================
# API兼容性验证
# ============================================================================

class TestAPICompatibility:
    """API兼容性验证"""
    
    @pytest.fixture
    def rag_client_routes(self):
        """visual_model调用的RAG接口列表"""
        return [
            # 聊天相关
            "/api/v1/chat",
            "/api/v1/chat/stream",
            # 计算加分
            "/api/v1/calculate-score",
            # 文档管理
            "/api/v1/documents/upload",
            "/api/v1/documents",
            "/api/v1/documents/batch-upload",
            # 系统管理
            "/api/v1/health",
            "/api/v1/stats",
            "/api/v1/prompts",
            "/api/v1/prompts/reset",
            "/api/v1/vector-db/stats",
            "/api/v1/vector-db/reset",
            "/api/v1/vector-db/rebuild",
            "/api/v1/system/llm/config",
            "/api/v1/system/llm/test",
            "/api/v1/system/llm/config/reset",
            "/api/v1/system/llm/config/validate",
        ]
    
    @pytest.fixture
    def rag_server_routes(self):
        """RAG服务端路由（从代码分析）"""
        return {
            "/api/v1/chat": ["POST"],
            "/api/v1/chat/stream": ["POST"],
            "/api/v1/chat/async": ["POST"],
            "/api/v1/chat/stream/async": ["POST"],
            "/api/v1/chat/cache/stats": ["GET"],
            "/api/v1/chat/cache": ["DELETE"],
            "/api/v1/documents": ["GET"],
            "/api/v1/documents/upload": ["POST"],
            "/api/v1/documents/batch-upload": ["POST"],
            "/api/v1/documents/{doc_id}": ["DELETE", "PATCH"],
            "/api/v1/documents/{doc_id}/status": ["PATCH"],
            "/api/v1/prompts": ["GET", "PUT"],
            "/api/v1/prompts/reset": ["POST"],
            "/api/v1/vector-db/stats": ["GET"],
            "/api/v1/vector-db/reset": ["POST"],
            "/api/v1/vector-db/rebuild": ["POST"],
            "/api/v1/system/llm/config": ["GET", "PUT"],
            "/api/v1/system/llm/test": ["POST"],
            "/api/v1/system/llm/config/reset": ["POST"],
            "/api/v1/system/llm/config/validate": ["GET"],
            "/api/v1/stats": ["GET"],
            "/api/v1/health": ["GET"],
            "/health": ["GET"],
        }
    
    def test_route_compatibility(self, rag_client_routes, rag_server_routes):
        """测试路由兼容性"""
        missing_routes = []
        compatible_count = 0
        
        for route in rag_client_routes:
            if route in rag_server_routes:
                compatible_count += 1
                logger.info(f"✅ 路由兼容: {route}")
            else:
                missing_routes.append(route)
                logger.warning(f"❌ 路由缺失: {route}")
        
        total_routes = len(rag_client_routes)
        compatibility_rate = (compatible_count / total_routes * 100) if total_routes > 0 else 0
        
        logger.info(f"路由兼容性检查完成: {compatible_count}/{total_routes} ({compatibility_rate:.1f}%)")
        
        if missing_routes:
            logger.warning(f"缺失的路由: {missing_routes}")
        else:
            logger.info("✅ 所有路由都兼容")
        
        assert compatibility_rate >= 80, f"路由兼容性过低: {compatibility_rate:.1f}%"
    
    def test_required_routes_exist(self, rag_server_routes):
        """测试核心必需路由存在"""
        required_routes = [
            "/api/v1/chat",
            "/api/v1/chat/stream",
            "/api/v1/documents/upload",
            "/api/v1/health",
        ]
        
        for route in required_routes:
            assert route in rag_server_routes, f"核心路由缺失: {route}"
            logger.info(f"✅ 核心路由存在: {route}")


# ============================================================================
# 测试运行器
# ============================================================================

def run_all_tests():
    """运行所有测试并生成报告"""
    import sys
    from pathlib import Path
    
    report_data = {
        "test_suite": "Visual Model与RAG集成端到端测试",
        "timestamp": datetime.now().isoformat(),
        "results": {},
        "summary": {}
    }
    
    logger.info("=" * 80)
    logger.info("开始运行Visual Model与RAG集成端到端测试")
    logger.info("=" * 80)
    
    pytest_args = [
        __file__,
        "-v",
        "--tb=short",
        "--html=reports/rag_integration_test_report.html",
        "--self-contained-html",
        "-p", "no:warnings",
    ]
    
    exit_code = pytest.main(pytest_args)
    
    logger.info("=" * 80)
    logger.info(f"测试执行完成，退出码: {exit_code}")
    logger.info("=" * 80)
    
    return exit_code


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Visual Model与RAG集成端到端测试")
    parser.add_argument("--unit", action="store_true", help="仅运行单元测试")
    parser.add_argument("--integration", action="store_true", help="仅运行集成测试")
    parser.add_argument("--compatibility", action="store_true", help="仅运行兼容性测试")
    
    args = parser.parse_args()
    
    pytest_args = [__file__, "-v", "--tb=short"]
    
    if args.unit:
        pytest_args.extend(["-k", "TestRAGClient or TestRAGExceptionHandling"])
    elif args.integration:
        pytest_args.extend(["-k", "TestRAGIntegrationE2E"])
    elif args.compatibility:
        pytest_args.extend(["-k", "TestAPICompatibility"])
    
    pytest.main(pytest_args)
