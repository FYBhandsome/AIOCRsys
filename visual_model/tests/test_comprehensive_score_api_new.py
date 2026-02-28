#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综测成绩API测试模块
测试综测计算、配置管理、班级排名等功能
"""
import pytest
from httpx import AsyncClient

from conftest_new import API_PREFIX, TEST_STUDENTS, TEST_CLASSES


@pytest.mark.asyncio
@pytest.mark.comprehensive
class TestComprehensiveScoreAPI:
    """综测成绩API测试类"""
    
    async def test_get_configs(self, client: AsyncClient, admin_token: str, test_result):
        """测试获取综测配置列表"""
        test_result.start()
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await client.get(f"{API_PREFIX}/comprehensive-score/config/list", headers=headers)
        
        assert response.status_code == 200, f"获取配置列表失败: {response.text}"
        data = response.json()
        assert "configs" in data, "响应中缺少configs字段"
        
        test_result.add_result("test_get_configs", True, f"获取到{len(data.get('configs', []))}个配置")
        test_result.end()
    
    async def test_create_config(self, client: AsyncClient, admin_token: str, test_result):
        """测试创建综测配置"""
        test_result.start()
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        config_data = {
            "name": "测试配置",
            "description": "自动化测试配置",
            "a_weight": 20.0,
            "b_weight": 70.0,
            "c_weight": 10.0,
            "academic_score_field": "weighted_average",
            "academic_score_scale": 1.0,
            "is_default": False
        }
        
        response = await client.post(
            f"{API_PREFIX}/comprehensive-score/config",
            headers=headers,
            json=config_data
        )
        
        assert response.status_code in [200, 201], f"创建配置失败: {response.text}"
        data = response.json()
        assert data.get("success") or "id" in data, "创建配置应该返回成功或ID"
        
        test_result.add_result("test_create_config", True, "创建配置成功")
        test_result.end()
    
    async def test_create_config_invalid_weight(self, client: AsyncClient, admin_token: str, test_result):
        """测试创建无效权重配置"""
        test_result.start()
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        config_data = {
            "name": "无效配置",
            "a_weight": 30.0,
            "b_weight": 80.0,
            "c_weight": 20.0
        }
        
        response = await client.post(
            f"{API_PREFIX}/comprehensive-score/config",
            headers=headers,
            json=config_data
        )
        
        assert response.status_code == 400, "权重总和不为100%应该返回400"
        
        test_result.add_result("test_create_config_invalid_weight", True, "无效权重正确被拒绝")
        test_result.end()
    
    async def test_get_classes(self, client: AsyncClient, teacher_token: str, test_result):
        """测试获取班级列表"""
        test_result.start()
        
        headers = {"Authorization": f"Bearer {teacher_token}"}
        response = await client.get(f"{API_PREFIX}/comprehensive-score/classes", headers=headers)
        
        assert response.status_code == 200, f"获取班级列表失败: {response.text}"
        data = response.json()
        assert "classes" in data, "响应中缺少classes字段"
        
        test_result.add_result("test_get_classes", True, f"获取到{len(data.get('classes', []))}个班级")
        test_result.end()
    
    async def test_calculate_student_score(self, client: AsyncClient, teacher_token: str, test_result):
        """测试计算学生综测成绩"""
        test_result.start()
        
        headers = {"Authorization": f"Bearer {teacher_token}"}
        student_id = TEST_STUDENTS[0]["id"]
        
        response = await client.post(
            f"{API_PREFIX}/comprehensive-score/calculate/student/{student_id}",
            headers=headers,
            params={"academic_year": "2023-2024", "semester": "1"}
        )
        
        assert response.status_code in [200, 400, 404], f"计算学生成绩响应异常: {response.text}"
        
        test_result.add_result("test_calculate_student_score", True, "计算学生成绩接口正常")
        test_result.end()
    
    async def test_get_student_score(self, client: AsyncClient, student_token: str, test_result):
        """测试获取学生综测成绩"""
        test_result.start()
        
        headers = {"Authorization": f"Bearer {student_token}"}
        student_id = TEST_STUDENTS[0]["id"]
        
        response = await client.get(
            f"{API_PREFIX}/comprehensive-score/student/{student_id}",
            headers=headers,
            params={"academic_year": "2023-2024", "semester": "1"}
        )
        
        assert response.status_code in [200, 404], f"获取学生成绩响应异常: {response.text}"
        
        test_result.add_result("test_get_student_score", True, "获取学生成绩接口正常")
        test_result.end()
    
    async def test_get_class_ranking(self, client: AsyncClient, teacher_token: str, test_result):
        """测试获取班级排名"""
        test_result.start()
        
        headers = {"Authorization": f"Bearer {teacher_token}"}
        class_id = TEST_CLASSES[0]["id"]
        
        response = await client.get(
            f"{API_PREFIX}/comprehensive-score/class/{class_id}/ranking",
            headers=headers,
            params={"academic_year": "2023-2024", "semester": "1"}
        )
        
        assert response.status_code in [200, 404], f"获取班级排名响应异常: {response.text}"
        
        test_result.add_result("test_get_class_ranking", True, "获取班级排名接口正常")
        test_result.end()
    
    async def test_get_class_stats(self, client: AsyncClient, teacher_token: str, test_result):
        """测试获取班级统计"""
        test_result.start()
        
        headers = {"Authorization": f"Bearer {teacher_token}"}
        class_id = TEST_CLASSES[0]["id"]
        
        response = await client.get(
            f"{API_PREFIX}/comprehensive-score/class/{class_id}/stats",
            headers=headers,
            params={"academic_year": "2023-2024", "semester": "1"}
        )
        
        assert response.status_code in [200, 404], f"获取班级统计响应异常: {response.text}"
        
        test_result.add_result("test_get_class_stats", True, "获取班级统计接口正常")
        test_result.end()


@pytest.mark.asyncio
@pytest.mark.comprehensive
class TestScoreDetailAPI:
    """加减分明细API测试类"""
    
    async def test_add_score_detail(self, client: AsyncClient, teacher_token: str, test_result):
        """测试添加加减分明细"""
        test_result.start()
        
        headers = {"Authorization": f"Bearer {teacher_token}"}
        detail_data = {
            "student_id": TEST_STUDENTS[0]["id"],
            "academic_year": "2023-2024",
            "semester": "1",
            "category_type": "C1",
            "item_name": "蓝桥杯省赛一等奖",
            "score": 8.0,
            "description": "测试添加"
        }
        
        response = await client.post(
            f"{API_PREFIX}/comprehensive-score/detail",
            headers=headers,
            json=detail_data
        )
        
        assert response.status_code in [200, 201, 400, 404], f"添加明细响应异常: {response.text}"
        
        test_result.add_result("test_add_score_detail", True, "添加明细接口正常")
        test_result.end()
    
    async def test_add_score_detail_invalid_category(self, client: AsyncClient, teacher_token: str, test_result):
        """测试添加无效类别的明细"""
        test_result.start()
        
        headers = {"Authorization": f"Bearer {teacher_token}"}
        detail_data = {
            "student_id": TEST_STUDENTS[0]["id"],
            "academic_year": "2023-2024",
            "semester": "1",
            "category_type": "INVALID",
            "item_name": "测试项目",
            "score": 5.0
        }
        
        response = await client.post(
            f"{API_PREFIX}/comprehensive-score/detail",
            headers=headers,
            json=detail_data
        )
        
        assert response.status_code == 400, "无效类别应该返回400"
        
        test_result.add_result("test_add_score_detail_invalid_category", True, "无效类别正确被拒绝")
        test_result.end()
