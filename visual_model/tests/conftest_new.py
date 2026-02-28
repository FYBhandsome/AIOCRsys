#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综测计算助手 - Pytest配置文件
提供统一的测试配置、fixtures和钩子函数
"""
import asyncio
import os
import sys
import pytest
import logging
import tempfile
import shutil
import json
from typing import AsyncGenerator, Generator, Dict, Any, List
from datetime import datetime
from httpx import AsyncClient, ASGITransport
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings

API_PREFIX = settings.API_V1_STR

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("test_framework")

TEST_USERS = {
    "admin": {
        "username": "test_admin",
        "password": "admin123456",
        "role": "admin",
        "email": "admin@test.com",
        "real_name": "测试管理员"
    },
    "teacher": {
        "username": "test_teacher",
        "password": "teacher123456",
        "role": "teacher",
        "email": "teacher@test.com",
        "real_name": "测试教师"
    },
    "student": {
        "username": "test_student_001",
        "password": "student123456",
        "role": "student",
        "email": "student@test.com",
        "real_name": "测试学生",
        "student_id": "202300502001"
    }
}

TEST_CLASSES = [
    {
        "id": "test_class_001",
        "name": "测试班级2301",
        "grade": "2023",
        "major": "计算机科学与技术",
        "college": "计算机学院"
    },
    {
        "id": "test_class_002",
        "name": "测试班级2302",
        "grade": "2023",
        "major": "软件工程",
        "college": "计算机学院"
    }
]

TEST_STUDENTS = [
    {
        "id": "202300502001",
        "name": "张三",
        "gender": "男",
        "class_name": "测试班级2301",
        "major": "计算机科学与技术",
        "grade": "2023"
    },
    {
        "id": "202300502002",
        "name": "李四",
        "gender": "女",
        "class_name": "测试班级2301",
        "major": "计算机科学与技术",
        "grade": "2023"
    },
    {
        "id": "202300502003",
        "name": "王五",
        "gender": "男",
        "class_name": "测试班级2302",
        "major": "软件工程",
        "grade": "2023"
    }
]

TEST_CERTIFICATES = [
    {
        "name": "蓝桥杯全国软件和信息技术专业人才大赛",
        "level": "省级",
        "award": "一等奖",
        "category": "C1",
        "expected_score": 8.0
    },
    {
        "name": "全国大学生英语竞赛",
        "level": "国家级",
        "award": "二等奖",
        "category": "C1",
        "expected_score": 12.0
    },
    {
        "name": "优秀学生干部",
        "level": "校级",
        "award": "荣誉称号",
        "category": "A2",
        "expected_score": 5.0
    }
]

TEST_ACADEMIC_SCORES = [
    {
        "student_id": "202300502001",
        "academic_year": "2023-2024",
        "semester": "1",
        "course_name": "高等数学",
        "credit": 4.0,
        "score": 85.0,
        "score_type": "期末成绩"
    },
    {
        "student_id": "202300502001",
        "academic_year": "2023-2024",
        "semester": "1",
        "course_name": "大学英语",
        "credit": 3.0,
        "score": 90.0,
        "score_type": "期末成绩"
    },
    {
        "student_id": "202300502001",
        "academic_year": "2023-2024",
        "semester": "1",
        "course_name": "程序设计基础",
        "credit": 4.0,
        "score": 92.0,
        "score_type": "期末成绩"
    }
]

TEST_COMPREHENSIVE_SCORES = [
    {
        "student_id": "202300502001",
        "academic_year": "2023-2024",
        "semester": "1",
        "a1_score": 100.0,
        "a2_score": 10.0,
        "a3_score": 0.0,
        "a_total_score": 22.0,
        "b_total_score": 70.0,
        "c1_score": 8.0,
        "c2_score": 0.0,
        "c3_score": 0.0,
        "c4_score": 0.0,
        "c_total_score": 0.8,
        "total_score": 92.8
    }
]


def pytest_configure(config):
    """pytest配置钩子"""
    config.addinivalue_line("markers", "auth: 认证相关测试")
    config.addinivalue_line("markers", "student: 学生相关测试")
    config.addinivalue_line("markers", "teacher: 教师相关测试")
    config.addinivalue_line("markers", "admin: 管理员相关测试")
    config.addinivalue_line("markers", "ai: AI助手相关测试")
    config.addinivalue_line("markers", "integration: 集成测试")
    config.addinivalue_line("markers", "comprehensive: 综测相关测试")
    config.addinivalue_line("markers", "certificate: 证书相关测试")
    config.addinivalue_line("markers", "file: 文件管理相关测试")
    config.addinivalue_line("markers", "rag: RAG系统相关测试")
    config.addinivalue_line("markers", "slow: 慢速测试")
    config.addinivalue_line("markers", "unit: 单元测试")
    config.addinivalue_line("markers", "api: API测试")


def pytest_collection_modifyitems(config, items):
    """修改测试项"""
    for item in items:
        if "asyncio" in str(item.fspath):
            item.add_marker(pytest.mark.asyncio)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_data() -> Dict[str, Any]:
    """测试数据集合"""
    return {
        "users": TEST_USERS,
        "classes": TEST_CLASSES,
        "students": TEST_STUDENTS,
        "certificates": TEST_CERTIFICATES,
        "academic_scores": TEST_ACADEMIC_SCORES,
        "comprehensive_scores": TEST_COMPREHENSIVE_SCORES
    }


@pytest.fixture(scope="session")
async def app():
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
def auth_headers():
    """认证请求头工厂"""
    def _get_headers(token: str) -> Dict[str, str]:
        return {"Authorization": f"Bearer {token}"}
    return _get_headers


@pytest.fixture
def assert_response():
    """响应断言助手"""
    def _assert(response, expected_status: int, check_data: bool = True):
        assert response.status_code == expected_status, \
            f"期望状态码 {expected_status}，实际 {response.status_code}，响应: {response.text[:500]}"
        
        if check_data and response.status_code < 400:
            data = response.json()
            assert data is not None, "响应数据不应为空"
            return data
        return response.json() if response.text else None
    return _assert


@pytest.fixture
def temp_upload_dir():
    """临时上传目录"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_file(temp_upload_dir):
    """创建临时测试文件"""
    def _create_file(filename: str, content: bytes, content_type: str = None):
        file_path = Path(temp_upload_dir) / filename
        with open(file_path, "wb") as f:
            f.write(content)
        return file_path
    return _create_file


@pytest.fixture
def sample_image_bytes():
    """示例图片字节数据"""
    return (
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n"
        b"\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d"
        b"\x1a\x1c\x1c $.\' \",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0"
        b"\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00"
        b"\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01"
        b"\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01"
        b"\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04"
        b"\x11\x05\x12!1A\x06\x13Qa\x07\"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15"
        b"R\xd1F0b\x16$3br\x82\t\n\x17\x18\x19\x1a%&\'()*456789:CDEFGHIJSTUVWXY"
        b"Zcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96"
        b"\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5"
        b"\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4"
        b"\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1"
        b"\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x08\x01\x01\x00\x00?"
        b"\x00\xfa\xfe)\xa8\xfd\xfe?\xff\xd9"
    )


@pytest.fixture
def sample_excel_bytes():
    """示例Excel字节数据"""
    return (
        b"PK\x03\x04\x14\x00\x00\x00\x08\x00\x00\x00!\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00[Content_Types].xml"
    )


@pytest.fixture
def test_logger():
    """测试日志记录器"""
    return logging.getLogger("test_case")


@pytest.fixture
def test_result():
    """测试结果记录器"""
    return TestResult()


class TestResult:
    """测试结果记录器"""
    
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.passed = 0
        self.failed = 0
        self.errors = 0
        self.start_time = None
        self.end_time = None
    
    def start(self):
        self.start_time = datetime.now()
    
    def end(self):
        self.end_time = datetime.now()
    
    def add_result(self, test_name: str, success: bool, message: str = "", duration: float = 0):
        self.results.append({
            "test_name": test_name,
            "success": success,
            "message": message,
            "duration_ms": duration,
            "timestamp": datetime.now().isoformat()
        })
        if success:
            self.passed += 1
        else:
            self.failed += 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": {
                "total": len(self.results),
                "passed": self.passed,
                "failed": self.failed,
                "errors": self.errors,
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "end_time": self.end_time.isoformat() if self.end_time else None,
                "duration_seconds": (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else 0
            },
            "results": self.results
        }


@pytest.fixture
def test_result():
    """测试结果记录器实例"""
    return TestResult()
