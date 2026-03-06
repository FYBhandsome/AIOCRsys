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
import tempfile
import shutil
from typing import AsyncGenerator, Generator, Dict, Any
from datetime import datetime
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch, MagicMock
from tortoise import Tortoise
from pathlib import Path

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

TEST_STUDENTS = [
    {
        "id": "202300502101",
        "name": "张三",
        "gender": "男",
        "class_name": "计算机2301",
        "major": "计算机科学与技术",
        "grade": "2023"
    },
    {
        "id": "202300502102",
        "name": "李四",
        "gender": "女",
        "class_name": "计算机2301",
        "major": "计算机科学与技术",
        "grade": "2023"
    },
    {
        "id": "202300502103",
        "name": "王五",
        "gender": "男",
        "class_name": "计算机2302",
        "major": "计算机科学与技术",
        "grade": "2023"
    }
]

TEST_ACADEMIC_SCORES = [
    {
        "student_id": "202300502101",
        "academic_year": "2023-2024",
        "semester": "1",
        "course_name": "高等数学",
        "credit": 4.0,
        "score": 85.0,
        "score_type": "期末成绩"
    },
    {
        "student_id": "202300502101",
        "academic_year": "2023-2024",
        "semester": "1",
        "course_name": "大学英语",
        "credit": 3.0,
        "score": 90.0,
        "score_type": "期末成绩"
    }
]

TEST_COMPREHENSIVE_SCORES = [
    {
        "student_id": "202300502101",
        "academic_year": "2023-2024",
        "semester": "1",
        "a_total_score": 15.0,
        "b_total_score": 70.0,
        "c_total_score": 8.0,
        "total_score": 93.0
    }
]

TEST_FILES = {
    "image": {
        "filename": "test_certificate.jpg",
        "content": b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' \",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07\"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1F0b\x16$3br\x82\t\n\x17\x18\x19\x1a%&\'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xfa\xfe)\xa8\xfd\xfe?\xff\xd9",
        "content_type": "image/jpeg"
    },
    "pdf": {
        "filename": "test_document.pdf",
        "content": b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n190\n%%EOF",
        "content_type": "application/pdf"
    },
    "excel": {
        "filename": "test_scores.xlsx",
        "content": b"PK\x03\x04\x14\x00\x00\x00\x08\x00",
        "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    }
}


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def temp_db_path(tmp_path_factory):
    """创建临时数据库文件路径"""
    tmp_path = tmp_path_factory.mktemp("test_db")
    return str(tmp_path / "test_database.db")


@pytest.fixture
async def initialize_db(temp_db_path):
    """初始化测试数据库"""
    logger.info(f"初始化测试数据库: {temp_db_path}")
    
    temp_db_url = f"sqlite:///{temp_db_path}"
    
    await Tortoise.init(
        db_url=temp_db_url,
        modules={"models": ["app.models.tortoise_models"]}
    )
    await Tortoise.generate_schemas()
    
    from app.models.tortoise_models import User, Student
    from app.core.security import get_password_hash
    
    test_users_data = [
        {"username": "admin", "password": "admin123", "role": "admin", "email": "admin@test.com", "real_name": "系统管理员", "is_active": True},
        {"username": "teacher", "password": "teacher123", "role": "teacher", "email": "teacher@test.com", "real_name": "测试教师", "is_active": True},
        {"username": "student_202300502128", "password": "student123", "role": "student", "email": "student@test.com", "real_name": "测试学生", "student_id": "202300502128", "is_active": True},
    ]
    
    for user_data in test_users_data:
        existing = await User.filter(username=user_data["username"]).first()
        if not existing:
            await User.create(
                username=user_data["username"],
                password=get_password_hash(user_data["password"]),
                role=user_data["role"],
                email=user_data["email"],
                real_name=user_data["real_name"],
                student_id=user_data.get("student_id"),
                is_active=user_data["is_active"]
            )
            logger.info(f"创建测试用户: {user_data['username']}")
    
    test_students_data = [
        {"id": "202300502101", "name": "张三", "college": "计算机学院", "major": "计算机科学与技术", "class_name": "计算机2301", "grade": "2023"},
        {"id": "202300502128", "name": "测试学生", "college": "计算机学院", "major": "计算机科学与技术", "class_name": "计算机2301", "grade": "2023"},
    ]
    
    for student_data in test_students_data:
        existing = await Student.filter(id=student_data["id"]).first()
        if not existing:
            await Student.create(**student_data)
            logger.info(f"创建测试学生: {student_data['id']}")
    
    logger.info("测试数据库初始化完成")
    
    yield
    
    logger.info("关闭测试数据库连接...")
    await Tortoise.close_connections()


@pytest.fixture
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
async def test_student_data():
    """测试学生数据"""
    return TEST_STUDENTS.copy()


@pytest.fixture
async def test_class_data():
    """测试班级数据"""
    return TEST_CLASSES.copy()


@pytest.fixture
async def test_certificate_data():
    """测试证书数据"""
    return TEST_CERTIFICATES.copy()


@pytest.fixture
async def test_file_data():
    """测试文件数据"""
    return TEST_FILES.copy()


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
def pagination_params():
    """分页参数工厂"""
    def _get_params(page: int = 1, page_size: int = 20, **kwargs):
        params = {"page": page, "page_size": page_size}
        params.update(kwargs)
        return params
    return _get_params


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
    config.addinivalue_line(
        "markers", "comprehensive: 综测相关测试"
    )
    config.addinivalue_line(
        "markers", "certificate: 证书相关测试"
    )
    config.addinivalue_line(
        "markers", "file: 文件管理相关测试"
    )
    config.addinivalue_line(
        "markers", "middleware: 中间件相关测试"
    )
    config.addinivalue_line(
        "markers", "api: API响应规范测试"
    )
    config.addinivalue_line(
        "markers", "ocr: OCR识别相关测试"
    )


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
    """测试结果记录器"""
    return TestResult()


@pytest.fixture
def sample_excel_bytes():
    """示例Excel文件字节数据"""
    import openpyxl
    from io import BytesIO
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "成绩表"
    ws.append(["学号", "姓名", "班级", "成绩"])
    ws.append(["202300502101", "张三", "计算机2301", 85.5])
    ws.append(["202300502102", "李四", "计算机2301", 88.0])
    
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.read()


@pytest.fixture
def sample_image_bytes():
    """示例图片文件字节数据"""
    from PIL import Image
    from io import BytesIO
    
    img = Image.new('RGB', (100, 100), color='red')
    buffer = BytesIO()
    img.save(buffer, format='JPEG')
    buffer.seek(0)
    return buffer.read()


@pytest.fixture
async def certificate_test_cleanup():
    """测试证书数据清理fixture"""
    from app.models.tortoise_models import Certificate, CertificateImage, CertificateBatch
    
    created_certificate_ids = []
    created_image_ids = []
    created_batch_ids = []
    test_file_paths = []
    
    yield {
        "created_certificate_ids": created_certificate_ids,
        "created_image_ids": created_image_ids,
        "created_batch_ids": created_batch_ids,
        "test_file_paths": test_file_paths
    }
    
    logger.info("开始清理证书测试数据...")
    
    try:
        if created_image_ids:
            await CertificateImage.filter(id__in=created_image_ids).delete()
            logger.info(f"已删除 {len(created_image_ids)} 条证书图片记录")
        
        if created_certificate_ids:
            await Certificate.filter(id__in=created_certificate_ids).delete()
            logger.info(f"已删除 {len(created_certificate_ids)} 条证书记录")
        
        if created_batch_ids:
            await CertificateBatch.filter(id__in=created_batch_ids).delete()
            logger.info(f"已删除 {len(created_batch_ids)} 条批次记录")
        
        import os
        for file_path in test_file_paths:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"已删除测试文件: {file_path}")
                except Exception as e:
                    logger.warning(f"删除测试文件失败: {file_path}, 错误: {e}")
    except Exception as e:
        logger.error(f"清理测试数据时出错: {e}")
    
    logger.info("证书测试数据清理完成")


@pytest.fixture
def test_photo_dir():
    """测试照片目录"""
    from pathlib import Path
    test_dir = Path(__file__).parent.parent / "testphoto" / "test"
    return str(test_dir)


@pytest.fixture
def get_test_photos(test_photo_dir):
    """获取测试照片文件路径"""
    from pathlib import Path
    import glob
    
    def _get_photos(ext=None, count=None):
        pattern = f"*.{ext}" if ext else "*.*"
        photo_paths = glob.glob(str(Path(test_photo_dir) / pattern))
        if count and len(photo_paths) > count:
            return photo_paths[:count]
        return photo_paths
    
    return _get_photos


def pytest_collection_modifyitems(config, items):
    """修改测试项"""
    for item in items:
        if "asyncio" in str(item.fspath):
            item.add_marker(pytest.mark.asyncio)
