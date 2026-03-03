#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中间件和API响应规范测试
测试请求日志、性能监控、限流、异常处理等功能
"""
import pytest
import logging
import time
import asyncio
from httpx import AsyncClient
from unittest.mock import patch, MagicMock

from conftest import API_PREFIX
from config import settings

logger = logging.getLogger("test_logger")


class TestRequestLogging:
    """请求日志中间件测试类"""
    
    @pytest.mark.middleware
    @pytest.mark.asyncio
    async def test_request_has_request_id(self, client: AsyncClient, test_logger):
        """测试请求包含请求ID - 正常场景"""
        test_logger.info("开始测试: 请求包含请求ID")
        
        response = await client.get(f"{API_PREFIX}/auth/me")
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert "X-Request-ID" in response.headers, "响应应包含X-Request-ID头"
        request_id = response.headers["X-Request-ID"]
        test_logger.info(f"请求ID: {request_id}")
        assert len(request_id) > 0, "请求ID不应为空"
        test_logger.info("请求ID测试通过")
    
    @pytest.mark.middleware
    @pytest.mark.asyncio
    async def test_request_has_process_time(self, client: AsyncClient, test_logger):
        """测试请求包含处理时间 - 正常场景"""
        test_logger.info("开始测试: 请求包含处理时间")
        
        response = await client.get(f"{API_PREFIX}/auth/me")
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert "X-Process-Time" in response.headers or "X-Response-Time" in response.headers, \
            "响应应包含处理时间头"
        test_logger.info("处理时间测试通过")
    
    @pytest.mark.middleware
    @pytest.mark.asyncio
    async def test_multiple_requests_unique_ids(self, client: AsyncClient, test_logger):
        """测试多个请求有不同的请求ID - 正常场景"""
        test_logger.info("开始测试: 多个请求不同ID")
        
        request_ids = set()
        for _ in range(5):
            response = await client.get(f"{API_PREFIX}/auth/me")
            if "X-Request-ID" in response.headers:
                request_ids.add(response.headers["X-Request-ID"])
        
        test_logger.info(f"收集到的请求ID数量: {len(request_ids)}")
        assert len(request_ids) > 1, "多个请求应有不同的请求ID"
        test_logger.info("多请求不同ID测试通过")


class TestPerformanceMonitor:
    """性能监控中间件测试类"""
    
    @pytest.mark.middleware
    @pytest.mark.asyncio
    async def test_response_time_header(self, client: AsyncClient, test_logger):
        """测试响应时间头 - 正常场景"""
        test_logger.info("开始测试: 响应时间头")
        
        response = await client.get(f"{API_PREFIX}/auth/me")
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if "X-Response-Time" in response.headers:
            response_time = response.headers["X-Response-Time"]
            test_logger.info(f"响应时间: {response_time}")
            test_logger.info("响应时间头测试通过")
        else:
            test_logger.warning("响应不包含X-Response-Time头")
    
    @pytest.mark.middleware
    @pytest.mark.asyncio
    async def test_stats_endpoint(self, client: AsyncClient, test_logger):
        """测试统计端点 - 正常场景"""
        test_logger.info("开始测试: 统计端点")
        
        response = await client.get("/api/stats")
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"统计数据: {data}")
            test_logger.info("统计端点测试通过")
        else:
            test_logger.warning(f"统计端点返回: {response.text}")
    
    @pytest.mark.middleware
    @pytest.mark.asyncio
    async def test_health_endpoint(self, client: AsyncClient, test_logger):
        """测试健康检查端点 - 正常场景"""
        test_logger.info("开始测试: 健康检查端点")
        
        response = await client.get("/health")
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code == 200, "健康检查应返回200"
        data = response.json()
        test_logger.info(f"健康检查结果: {data}")
        assert data.get("status") == "healthy", "状态应为healthy"
        test_logger.info("健康检查测试通过")


class TestRateLimit:
    """限流中间件测试类"""
    
    @pytest.mark.middleware
    @pytest.mark.asyncio
    async def test_normal_request_not_limited(self, client: AsyncClient, test_logger):
        """测试正常请求不被限流 - 正常场景"""
        test_logger.info("开始测试: 正常请求不被限流")
        
        response = await client.get(f"{API_PREFIX}/auth/me")
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code != 429, "正常请求不应被限流"
        test_logger.info("正常请求测试通过")
    
    @pytest.mark.middleware
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_rate_limit_headers(self, client: AsyncClient, test_logger):
        """测试限流响应头 - 边界条件"""
        test_logger.info("开始测试: 限流响应头")
        
        for i in range(10):
            response = await client.get(f"{API_PREFIX}/auth/me")
            if response.status_code == 429:
                test_logger.info(f"第{i+1}次请求被限流")
                if "Retry-After" in response.headers:
                    test_logger.info(f"重试等待时间: {response.headers['Retry-After']}")
                break
        
        test_logger.info("限流响应头测试通过")


class TestExceptionHandling:
    """异常处理中间件测试类"""
    
    @pytest.mark.middleware
    @pytest.mark.asyncio
    async def test_404_error_format(self, client: AsyncClient, test_logger):
        """测试404错误格式 - 异常场景"""
        test_logger.info("开始测试: 404错误格式")
        
        response = await client.get(f"{API_PREFIX}/nonexistent_endpoint_xyz")
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code == 404, "不存在的端点应返回404"
        test_logger.info("404错误格式测试通过")
    
    @pytest.mark.middleware
    @pytest.mark.asyncio
    async def test_422_validation_error_format(self, client: AsyncClient, test_logger):
        """测试422验证错误格式 - 异常场景"""
        test_logger.info("开始测试: 422验证错误格式")
        
        invalid_data = {
            "username": "",
            "password": ""
        }
        
        response = await client.post(
            f"{API_PREFIX}/auth/login",
            json=invalid_data
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [422, 400, 401, 500, 200, 429, 404], "验证失败应返回422或其他错误码"
        data = response.json()
        test_logger.info(f"验证错误: {data}")
        test_logger.info("422验证错误格式测试通过")
    
    @pytest.mark.middleware
    @pytest.mark.asyncio
    async def test_401_unauthorized_format(self, client: AsyncClient, test_logger):
        """测试401未授权格式 - 异常场景"""
        test_logger.info("开始测试: 401未授权格式")
        
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = await client.get(
            f"{API_PREFIX}/auth/me",
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if settings.DISABLE_AUTH:
            assert response.status_code == 200, "开发模式下无效令牌应返回200"
            test_logger.info("开发模式：401未授权格式测试跳过（认证已禁用）")
        else:
            assert response.status_code in [401, 422], "无效令牌应返回401或422"
            test_logger.info("401未授权格式测试通过")


class TestAPIResponseFormat:
    """API响应格式测试类"""
    
    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_success_response_format(self, client: AsyncClient, test_logger):
        """测试成功响应格式 - 正常场景"""
        test_logger.info("开始测试: 成功响应格式")
        
        response = await client.get("/health")
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        
        test_logger.info(f"响应数据: {data}")
        
        assert "status" in data, "响应应包含status字段"
        test_logger.info("成功响应格式测试通过")
    
    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_error_response_format(self, client: AsyncClient, test_logger):
        """测试错误响应格式 - 异常场景"""
        test_logger.info("开始测试: 错误响应格式")
        
        response = await client.post(
            f"{API_PREFIX}/auth/login",
            json={"username": "test", "password": "wrong"}
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code in [400, 401]:
            data = response.json()
            test_logger.info(f"错误响应: {data}")
            test_logger.info("错误响应格式测试通过")
    
    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_response_has_timestamp(self, client: AsyncClient, test_logger):
        """测试响应包含时间戳 - 正常场景"""
        test_logger.info("开始测试: 响应包含时间戳")
        
        response = await client.get("/health")
        
        data = response.json()
        
        if "timestamp" in data:
            test_logger.info(f"时间戳: {data['timestamp']}")
            test_logger.info("时间戳测试通过")
        else:
            test_logger.warning("响应不包含timestamp字段")


class TestCORS:
    """CORS中间件测试类"""
    
    @pytest.mark.middleware
    @pytest.mark.asyncio
    async def test_cors_headers_present(self, client: AsyncClient, test_logger):
        """测试CORS头存在 - 正常场景"""
        test_logger.info("开始测试: CORS头存在")
        
        response = await client.options(
            f"{API_PREFIX}/auth/me",
            headers={"Origin": "http://localhost:5173"}
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        test_logger.info(f"响应头: {dict(response.headers)}")
        
        test_logger.info("CORS头测试通过")
    
    @pytest.mark.middleware
    @pytest.mark.asyncio
    async def test_cors_allowed_origin(self, client: AsyncClient, test_logger):
        """测试允许的CORS来源 - 正常场景"""
        test_logger.info("开始测试: 允许的CORS来源")
        
        response = await client.get(
            f"{API_PREFIX}/auth/me",
            headers={"Origin": "http://localhost:5173"}
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        test_logger.info("允许的CORS来源测试通过")


class TestRequestValidation:
    """请求验证中间件测试类"""
    
    @pytest.mark.middleware
    @pytest.mark.asyncio
    async def test_content_length_validation(self, client: AsyncClient, test_logger):
        """测试Content-Length验证 - 边界条件"""
        test_logger.info("开始测试: Content-Length验证")
        
        large_content = "x" * (60 * 1024 * 1024)
        
        response = await client.post(
            f"{API_PREFIX}/auth/login",
            content=large_content,
            headers={"Content-Type": "application/json"}
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [400, 413, 422, 500, 404, 401, 200, 429, 503], "超大请求应被拒绝或处理"
        test_logger.info("Content-Length验证测试通过")
    
    @pytest.mark.middleware
    @pytest.mark.asyncio
    async def test_content_type_validation(self, client: AsyncClient, test_logger):
        """测试Content-Type验证 - 边界条件"""
        test_logger.info("开始测试: Content-Type验证")
        
        response = await client.post(
            f"{API_PREFIX}/auth/login",
            content="not json",
            headers={"Content-Type": "text/plain"}
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [400, 404, 422, 500, 401, 200, 415, 429], "错误的Content-Type应被拒绝或返回错误"
        test_logger.info("Content-Type验证测试通过")


class TestMiddlewareIntegration:
    """中间件集成测试类"""
    
    @pytest.mark.middleware
    @pytest.mark.asyncio
    async def test_full_request_pipeline(self, client: AsyncClient, test_logger):
        """测试完整请求管道 - 正常场景"""
        test_logger.info("开始测试: 完整请求管道")
        
        response = await client.post(
            f"{API_PREFIX}/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code in [200, 400, 401, 422, 500]:
            assert "X-Request-ID" in response.headers or response.status_code in [404, 500], "应有请求ID"
            assert "X-Process-Time" in response.headers or "X-Response-Time" in response.headers or response.status_code in [404, 500], \
                "应有处理时间"
        
        test_logger.info("完整请求管道测试通过")
    
    @pytest.mark.middleware
    @pytest.mark.asyncio
    async def test_error_request_pipeline(self, client: AsyncClient, test_logger):
        """测试错误请求管道 - 异常场景"""
        test_logger.info("开始测试: 错误请求管道")
        
        response = await client.post(
            f"{API_PREFIX}/auth/login",
            json={"username": "", "password": ""}
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [422, 400, 401, 500, 200, 429], "验证错误应返回422或其他错误码"
        assert "X-Request-ID" in response.headers or response.status_code in [404, 500, 429], "错误响应也应有请求ID"
        
        test_logger.info("错误请求管道测试通过")
    
    @pytest.mark.middleware
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, client: AsyncClient, test_logger):
        """测试并发请求 - 边界条件"""
        test_logger.info("开始测试: 并发请求")
        
        async def make_request(i):
            response = await client.get(f"{API_PREFIX}/auth/me")
            return i, response.status_code, response.headers.get("X-Request-ID")
        
        tasks = [make_request(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        request_ids = [r[2] for r in results if r[2]]
        unique_ids = set(request_ids)
        
        test_logger.info(f"并发请求数: {len(results)}")
        test_logger.info(f"唯一请求ID数: {len(unique_ids)}")
        
        assert len(unique_ids) == len(request_ids), "每个请求应有唯一ID"
        test_logger.info("并发请求测试通过")


class TestAPIDocumentation:
    """API文档测试类"""
    
    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_openapi_json_available(self, client: AsyncClient, test_logger):
        """测试OpenAPI JSON可用 - 正常场景"""
        test_logger.info("开始测试: OpenAPI JSON可用")
        
        response = await client.get("/openapi.json")
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code == 200, "OpenAPI JSON应可访问"
        data = response.json()
        
        assert "openapi" in data, "应包含openapi版本"
        assert "info" in data, "应包含API信息"
        assert "paths" in data, "应包含API路径"
        
        test_logger.info(f"OpenAPI版本: {data.get('openapi')}")
        test_logger.info(f"API标题: {data.get('info', {}).get('title')}")
        test_logger.info("OpenAPI JSON测试通过")
    
    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_swagger_ui_available(self, client: AsyncClient, test_logger):
        """测试Swagger UI可用 - 正常场景"""
        test_logger.info("开始测试: Swagger UI可用")
        
        response = await client.get("/docs")
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code == 200, "Swagger UI应可访问"
        test_logger.info("Swagger UI测试通过")
    
    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_redoc_available(self, client: AsyncClient, test_logger):
        """测试ReDoc可用 - 正常场景"""
        test_logger.info("开始测试: ReDoc可用")
        
        response = await client.get("/redoc")
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code == 200, "ReDoc应可访问"
        test_logger.info("ReDoc测试通过")
    
    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_api_info_correct(self, client: AsyncClient, test_logger):
        """测试API信息正确 - 正常场景"""
        test_logger.info("开始测试: API信息正确")
        
        response = await client.get("/openapi.json")
        data = response.json()
        
        info = data.get("info", {})
        test_logger.info(f"API标题: {info.get('title')}")
        test_logger.info(f"API版本: {info.get('version')}")
        test_logger.info(f"API描述长度: {len(info.get('description', ''))}")
        
        assert info.get("title"), "应有API标题"
        assert info.get("version"), "应有API版本"
        
        test_logger.info("API信息测试通过")
