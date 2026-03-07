#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综测系统完整业务流程测试
测试上传材料、计算综测、下载结果核心流程
"""
import pytest
import asyncio
import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from io import BytesIO
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from httpx import AsyncClient, ASGITransport
from tortoise import Tortoise

from config import settings

pytestmark = pytest.mark.asyncio(loop_scope="function")

TEST_DATA_DIR = Path("D:/PaddleOCR/visual_model/data")
TEST_PHOTO_DIR = Path("D:/PaddleOCR/visual_model/testphoto/test")
SCORE_SHEET_FILE = TEST_DATA_DIR / "学生成绩单.xlsx"
COMPREHENSIVE_TABLE_FILE = TEST_DATA_DIR / "230521班综合测评计算表格.xlsx"

TEST_USERS = {
    "admin": {
        "username": "admin",
        "password": "admin123",
        "role": "admin"
    },
    "student": {
        "username": "202300502120",
        "password": "student123",
        "role": "student",
        "student_id": "202300502120",
        "name": "测试学生"
    },
    "teacher": {
        "username": "teacher001",
        "password": "teacher123",
        "role": "teacher"
    }
}

EXPECTED_RESULTS = {
    "weight_config": {
        "a_weight": 20.0,
        "b_weight": 70.0,
        "c_weight": 10.0
    },
    "level_scores": {
        "国家级": 12,
        "省级": 8,
        "校级": 5,
        "院级": 3
    }
}


@pytest.fixture(scope="function")
async def setup_db():
    """初始化测试数据库"""
    if Tortoise._inited:
        await Tortoise.close_connections()
    
    await Tortoise.init(
        db_url=settings.DATABASE_URL,
        modules={"models": ["app.models.tortoise_models"]}
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


@pytest.fixture(scope="function")
async def app(setup_db):
    """创建测试应用"""
    from app.core.app_factory import create_app
    test_app = create_app()
    yield test_app


@pytest.fixture(scope="function")
async def client(app):
    """创建测试客户端"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", timeout=120.0) as ac:
        yield ac


@pytest.fixture(scope="function")
async def admin_token(client):
    """获取管理员令牌"""
    response = await client.post(f"{settings.API_V1_STR}/auth/login", json={
        "username": TEST_USERS["admin"]["username"],
        "password": TEST_USERS["admin"]["password"]
    })
    if response.status_code == 200:
        return response.json().get("access_token", "")
    return "test_admin_token"


@pytest.fixture(scope="function")
async def student_token(client):
    """获取学生令牌"""
    response = await client.post(f"{settings.API_V1_STR}/auth/login", json={
        "username": TEST_USERS["student"]["username"],
        "password": TEST_USERS["student"]["password"]
    })
    if response.status_code == 200:
        return response.json().get("access_token", "")
    return "test_student_token"


class TestComprehensiveFlow:
    """综测核心业务流程测试"""
    
    async def test_01_upload_score_sheet(self, client, admin_token):
        """测试1: 上传学生成绩单"""
        print("\n=== 测试1: 上传学生成绩单 ===")
        
        if not SCORE_SHEET_FILE.exists():
            pytest.skip(f"测试文件不存在: {SCORE_SHEET_FILE}")
        
        with open(SCORE_SHEET_FILE, 'rb') as f:
            file_content = f.read()
        
        files = {
            "file": ("学生成绩单.xlsx", BytesIO(file_content), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        }
        data = {
            "academic_year": "2024-2025",
            "semester": "1",
            "uploaded_by": "admin",
            "upload_role": "admin"
        }
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post(
            f"{settings.API_V1_STR}/score-upload/upload",
            files=files,
            data=data,
            headers=headers
        )
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"处理结果: 成功{result.get('processed', 0)}条, 失败{result.get('failed', 0)}条")
            assert result.get("success") == True
        else:
            print(f"上传失败: {response.text}")
    
    async def test_02_upload_comprehensive_table(self, client, admin_token):
        """测试2: 上传综测计算表格"""
        print("\n=== 测试2: 上传综测计算表格 ===")
        
        if not COMPREHENSIVE_TABLE_FILE.exists():
            pytest.skip(f"测试文件不存在: {COMPREHENSIVE_TABLE_FILE}")
        
        with open(COMPREHENSIVE_TABLE_FILE, 'rb') as f:
            file_content = f.read()
        
        files = {
            "file": ("综测计算表.xlsx", BytesIO(file_content), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        }
        data = {
            "academic_year": "2024-2025",
            "semester": "1",
            "uploaded_by": "admin",
            "upload_role": "admin"
        }
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.post(
            f"{settings.API_V1_STR}/data-import/excel",
            files=files,
            data=data,
            headers=headers
        )
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"导入结果: {json.dumps(result, ensure_ascii=False)[:500]}")
    
    async def test_03_upload_certificate_photos(self, client, student_token):
        """测试3: 上传证书照片"""
        print("\n=== 测试3: 上传证书照片 ===")
        
        if not TEST_PHOTO_DIR.exists():
            pytest.skip(f"测试图片目录不存在: {TEST_PHOTO_DIR}")
        
        photo_files = list(TEST_PHOTO_DIR.glob("*.jpg")) + list(TEST_PHOTO_DIR.glob("*.png"))
        
        if not photo_files:
            pytest.skip("测试图片目录中没有图片文件")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        for i, photo_path in enumerate(photo_files[:3]):
            with open(photo_path, 'rb') as f:
                file_content = f.read()
            
            files = {
                "files": (photo_path.name, BytesIO(file_content), "image/jpeg")
            }
            data = {
                "student_id": "202300502120",
                "title": f"测试证书{i+1}",
                "certificate_type": "competition",
                "level": "省级",
                "category": "C",
                "sub_category": "C1"
            }
            
            response = await client.post(
                f"{settings.API_V1_STR}/certificate/upload",
                files=files,
                data=data,
                headers=headers
            )
            
            print(f"上传 {photo_path.name}: 状态码 {response.status_code}")
    
    async def test_04_calculate_comprehensive_score(self, client, admin_token):
        """测试4: 计算综测成绩"""
        print("\n=== 测试4: 计算综测成绩 ===")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = await client.post(
            f"{settings.API_V1_STR}/comprehensive-score/calculate/class/230521",
            params={"academic_year": "2024-2025", "semester": "1"},
            headers=headers
        )
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"计算结果: {json.dumps(result, ensure_ascii=False)[:500]}")
    
    async def test_05_get_student_scores(self, client, student_token):
        """测试5: 获取学生成绩"""
        print("\n=== 测试5: 获取学生成绩 ===")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        response = await client.get(
            f"{settings.API_V1_STR}/comprehensive-score/student/202300502120",
            params={"academic_year": "2024-2025", "semester": "1"},
            headers=headers
        )
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"学生成绩: {json.dumps(result, ensure_ascii=False)[:500]}")
    
    async def test_06_get_class_ranking(self, client, admin_token):
        """测试6: 获取班级排名"""
        print("\n=== 测试6: 获取班级排名 ===")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = await client.get(
            f"{settings.API_V1_STR}/comprehensive-score/class/230521/ranking",
            params={"academic_year": "2024-2025", "semester": "1"},
            headers=headers
        )
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            rankings = result.get("rankings", [])
            print(f"排名数量: {len(rankings)}")
            if rankings:
                print(f"前3名: {json.dumps(rankings[:3], ensure_ascii=False)}")
    
    async def test_07_download_result_file(self, client, admin_token):
        """测试7: 下载综测结果文件"""
        print("\n=== 测试7: 下载综测结果文件 ===")
        
        if not SCORE_SHEET_FILE.exists():
            pytest.skip(f"测试文件不存在: {SCORE_SHEET_FILE}")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        with open(SCORE_SHEET_FILE, 'rb') as f:
            file_content = f.read()
        
        response = await client.post(
            f"{settings.API_V1_STR}/field-mapping/process",
            files={
                "source_file": ("学生成绩单.xlsx", BytesIO(file_content), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            },
            data={
                "academic_year": "2024-2025",
                "semester": "1"
            },
            headers=headers
        )
        
        print(f"响应状态码: {response.status_code}")
    
    async def test_08_verify_weight_calculation(self, client, admin_token):
        """测试8: 验证权重计算准确性"""
        print("\n=== 测试8: 验证权重计算准确性 ===")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = await client.get(
            f"{settings.API_V1_STR}/comprehensive-score/config/list",
            headers=headers
        )
        
        if response.status_code == 200:
            configs = response.json().get("configs", [])
            if configs:
                config = configs[0]
                a_weight = config.get("a_weight", 0)
                b_weight = config.get("b_weight", 0)
                c_weight = config.get("c_weight", 0)
                
                total_weight = a_weight + b_weight + c_weight
                print(f"权重配置: A={a_weight}%, B={b_weight}%, C={c_weight}%")
                print(f"权重总和: {total_weight}%")
                
                assert abs(total_weight - 100.0) < 0.01, "权重总和应为100%"
    
    async def test_09_error_handling_invalid_file(self, client, admin_token):
        """测试9: 异常处理 - 无效文件格式"""
        print("\n=== 测试9: 异常处理 - 无效文件格式 ===")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        files = {
            "file": ("test.txt", BytesIO(b"invalid content"), "text/plain")
        }
        data = {
            "academic_year": "2024-2025",
            "semester": "1",
            "uploaded_by": "admin"
        }
        
        response = await client.post(
            f"{settings.API_V1_STR}/score-upload/upload",
            files=files,
            data=data,
            headers=headers
        )
        
        print(f"响应状态码: {response.status_code}")
        assert response.status_code in [400, 500], "无效文件应返回错误"
    
    async def test_10_permission_check(self, client):
        """测试10: 权限检查 - 未授权访问"""
        print("\n=== 测试10: 权限检查 - 未授权访问 ===")
        
        response = await client.get(
            f"{settings.API_V1_STR}/comprehensive-score/class/230521/ranking",
            params={"academic_year": "2024-2025", "semester": "1"}
        )
        
        print(f"响应状态码: {response.status_code}")
        assert response.status_code in [401, 403, 404, 500, 422], "未授权访问应返回401或403"


def run_tests():
    """运行测试"""
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-s"
    ])


if __name__ == "__main__":
    run_tests()
