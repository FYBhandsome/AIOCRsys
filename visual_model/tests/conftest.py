#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成测试配置文件
提供测试客户端、数据库连接、测试数据等共享资源
"""
import asyncio
import os
import sys
import pytest
import logging
from typing import AsyncGenerator, Generator
from datetime import datetime
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch, MagicMock
from tortoise import Tortoise

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("test_logger")

API_PREFIX = settings.API_V1_STR


TEST_USERS = {
    "admin": {
        "username": "admin",
        "password": "admin123",
        "role": "admin",
        "email": "admin@test.com",
        "real_name": "测试管理员"
    },
    "teacher": {
        "username": "teacher",
        "password": "teacher123",
        "role": "teacher",
        "email": "teacher@test.com",
        "real_name": "测试教师"
    },
    "student": {
        "username": "student_202300502128",
        "password": "student123",
        "role": "student",
        "email": "student@test.com",
        "real_name": "测试学生",
        "student_id": "202300502128"
    }
}


TEST_CLASSES = [
    {
        "id": "test_class_001",
        "name": "测试班级2021级1班",
        "grade": "2021",
        "major": "计算机科学与技术"
    },
    {
        "id": "test_class_002",
        "name": "测试班级2021级2班",
        "grade": "2021",
        "major": "软件工程"
    }
]


TEST_CERTIFICATES = [
    {
        "name": "蓝桥杯全国软件和信息技术专业人才大赛",
        "level": "省级",
        "award": "一等奖",
        "expected_score": 15.0
    },
    {
        "name": "全国大学生英语竞赛",
        "level": "国家级",
        "award": "二等奖",
        "expected_score": 12.0
    }
]


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def initialize_db():
    """初始化测试数据库"""
    logger.info("初始化测试数据库...")
    
    await Tortoise.init(
        db_url=settings.DATABASE_URL,
        modules={"models": ["app.models.tortoise_models"]}
    )
    await Tortoise.generate_schemas()
    
    logger.info("测试数据库初始化完成")
    
    yield
    
    logger.info("关闭测试数据库连接...")
    await Tortoise.close_connections()


@pytest.fixture(scope="session")
async def app(initialize_db):
    """创建测试应用实例"""
    from app.core.app_factory import create_app
    test_app = create_app()
    yield test_app


@pytest.fixture
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    """创建异步HTTP测试客户端"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_client(client: AsyncClient) -> AsyncClient:
    """带认证的客户端"""
    return client


@pytest.fixture
async def admin_token(client: AsyncClient) -> str:
    """获取管理员令牌"""
    response = await client.post(f"{API_PREFIX}/auth/login", json={
        "username": TEST_USERS["admin"]["username"],
        "password": TEST_USERS["admin"]["password"]
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token", "")
    return "test_admin_token"


@pytest.fixture
async def teacher_token(client: AsyncClient) -> str:
    """获取教师令牌"""
    response = await client.post(f"{API_PREFIX}/auth/login", json={
        "username": TEST_USERS["teacher"]["username"],
        "password": TEST_USERS["teacher"]["password"]
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token", "")
    return "test_teacher_token"


@pytest.fixture
async def student_token(client: AsyncClient) -> str:
    """获取学生令牌"""
    response = await client.post(f"{API_PREFIX}/auth/login", json={
        "username": TEST_USERS["student"]["username"],
        "password": TEST_USERS["student"]["password"]
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token", "")
    return "test_student_token"


@pytest.fixture
def test_logger():
    """测试日志记录器"""
    return logger


@pytest.fixture
def mock_db_service():
    """模拟数据库服务"""
    mock_service = AsyncMock()
    mock_service.get_user_by_username = AsyncMock(return_value=None)
    mock_service.create_user = AsyncMock(return_value={"id": "test_user_id"})
    mock_service.get_classes = AsyncMock(return_value=[])
    mock_service.get_students_by_class = AsyncMock(return_value=[])
    return mock_service


@pytest.fixture
def mock_rag_client():
    """模拟RAG客户端"""
    mock_client = AsyncMock()
    mock_client.chat = AsyncMock(return_value={
        "reply": "这是测试回复",
        "success": True,
        "sources": []
    })
    mock_client.chat_stream = AsyncMock(return_value=[])
    return mock_client


def pytest_configure(config):
    """pytest配置钩子"""
    config.addinivalue_line(
        "markers", "auth: 认证相关测试"
    )
    config.addinivalue_line(
        "markers", "student: 学生相关测试"
    )
    config.addinivalue_line(
        "markers", "teacher: 教师相关测试"
    )
    config.addinivalue_line(
        "markers", "admin: 管理员相关测试"
    )
    config.addinivalue_line(
        "markers", "ai: AI助手相关测试"
    )
    config.addinivalue_line(
        "markers", "integration: 集成测试"
    )


def pytest_collection_modifyitems(config, items):
    """修改测试项"""
    for item in items:
        if "asyncio" in str(item.fspath):
            item.add_marker(pytest.mark.asyncio)
