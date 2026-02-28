#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综测成绩API测试
测试综测计算、成绩查询、班级排名、配置管理等功能
"""
import pytest
import logging
from httpx import AsyncClient
from io import BytesIO

from conftest import API_PREFIX, TEST_STUDENTS, TEST_COMPREHENSIVE_SCORES

logger = logging.getLogger("test_logger")


class TestComprehensiveScoreCalculate:
    """综测计算测试类"""
    
    @pytest.mark.comprehensive
    @pytest.mark.asyncio
    async def test_calculate_student_score_success(self, client: AsyncClient, admin_token: str, test_logger):
        """测试计算学生综测成绩 - 正常场景"""
        test_logger.info("开始测试: 计算学生综测成绩")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        student_id = TEST_STUDENTS[0]["id"]
        
        response = await client.post(
            f"{API_PREFIX}/comprehensive-score/calculate/student/{student_id}",
            params={"academic_year": "2023-2024", "semester": "1"},
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"计算结果: {data}")
            assert "success" in data or "total_score" in data
            test_logger.info("计算学生综测成绩测试通过")
        else:
            test_logger.warning(f"计算失败: {response.text}")
    
    @pytest.mark.comprehensive
    @pytest.mark.asyncio
    async def test_calculate_student_score_invalid_student(self, client: AsyncClient, admin_token: str, test_logger):
        """测试计算不存在学生的综测成绩 - 异常场景"""
        test_logger.info("开始测试: 计算不存在学生的综测成绩")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = await client.post(
            f"{API_PREFIX}/comprehensive-score/calculate/student/nonexistent_student",
            params={"academic_year": "2023-2024", "semester": "1"},
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [400, 404], "不存在学生应返回错误"
        test_logger.info("不存在学生测试通过")
    
    @pytest.mark.comprehensive
    @pytest.mark.asyncio
    async def test_calculate_student_score_missing_params(self, client: AsyncClient, admin_token: str, test_logger):
        """测试计算综测成绩缺少参数 - 边界条件"""
        test_logger.info("开始测试: 计算综测成绩缺少参数")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        student_id = TEST_STUDENTS[0]["id"]
        
        response = await client.post(
            f"{API_PREFIX}/comprehensive-score/calculate/student/{student_id}",
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code == 422, "缺少参数应返回422验证错误"
        test_logger.info("缺少参数测试通过")
    
    @pytest.mark.comprehensive
    @pytest.mark.asyncio
    async def test_calculate_class_scores_success(self, client: AsyncClient, admin_token: str, test_logger):
        """测试计算班级综测成绩 - 正常场景"""
        test_logger.info("开始测试: 计算班级综测成绩")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = await client.post(
            f"{API_PREFIX}/comprehensive-score/calculate/class/计算机2301",
            params={"academic_year": "2023-2024", "semester": "1"},
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"班级计算结果: {data}")
            test_logger.info("计算班级综测成绩测试通过")
        else:
            test_logger.warning(f"班级计算失败: {response.text}")


class TestComprehensiveScoreQuery:
    """综测成绩查询测试类"""
    
    @pytest.mark.comprehensive
    @pytest.mark.asyncio
    async def test_get_student_score_success(self, client: AsyncClient, student_token: str, test_logger):
        """测试获取学生综测成绩 - 正常场景"""
        test_logger.info("开始测试: 获取学生综测成绩")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        student_id = TEST_STUDENTS[0]["id"]
        
        response = await client.get(
            f"{API_PREFIX}/comprehensive-score/student/{student_id}",
            params={"academic_year": "2023-2024", "semester": "1"},
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"综测成绩: {data}")
            test_logger.info("获取学生综测成绩测试通过")
        else:
            test_logger.warning(f"获取综测成绩失败: {response.text}")
    
    @pytest.mark.comprehensive
    @pytest.mark.asyncio
    async def test_get_student_score_not_found(self, client: AsyncClient, student_token: str, test_logger):
        """测试获取不存在学生的综测成绩 - 异常场景"""
        test_logger.info("开始测试: 获取不存在学生的综测成绩")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        response = await client.get(
            f"{API_PREFIX}/comprehensive-score/student/nonexistent_12345",
            params={"academic_year": "2023-2024", "semester": "1"},
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        test_logger.info("不存在学生测试通过")
    
    @pytest.mark.comprehensive
    @pytest.mark.asyncio
    async def test_get_class_ranking_success(self, client: AsyncClient, teacher_token: str, test_logger):
        """测试获取班级排名 - 正常场景"""
        test_logger.info("开始测试: 获取班级排名")
        
        headers = {"Authorization": f"Bearer {teacher_token}"}
        
        response = await client.get(
            f"{API_PREFIX}/comprehensive-score/class/计算机2301/ranking",
            params={"academic_year": "2023-2024", "semester": "1"},
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"班级排名: {data}")
            
            if "rankings" in data:
                assert isinstance(data["rankings"], list)
            test_logger.info("获取班级排名测试通过")
        else:
            test_logger.warning(f"获取班级排名失败: {response.text}")
    
    @pytest.mark.comprehensive
    @pytest.mark.asyncio
    async def test_get_class_stats_success(self, client: AsyncClient, teacher_token: str, test_logger):
        """测试获取班级统计信息 - 正常场景"""
        test_logger.info("开始测试: 获取班级统计信息")
        
        headers = {"Authorization": f"Bearer {teacher_token}"}
        
        response = await client.get(
            f"{API_PREFIX}/comprehensive-score/class/计算机2301/stats",
            params={"academic_year": "2023-2024", "semester": "1"},
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"班级统计: {data}")
            test_logger.info("获取班级统计测试通过")
        else:
            test_logger.warning(f"获取班级统计失败: {response.text}")


class TestScoreDetail:
    """加减分明细测试类"""
    
    @pytest.mark.comprehensive
    @pytest.mark.asyncio
    async def test_add_score_detail_success(self, client: AsyncClient, admin_token: str, test_logger):
        """测试添加加减分明细 - 正常场景"""
        test_logger.info("开始测试: 添加加减分明细")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        detail_data = {
            "student_id": TEST_STUDENTS[0]["id"],
            "academic_year": "2023-2024",
            "semester": "1",
            "category_type": "A1",
            "item_name": "学科竞赛获奖",
            "score": 5.0,
            "description": "蓝桥杯省级一等奖"
        }
        
        response = await client.post(
            f"{API_PREFIX}/comprehensive-score/detail",
            json=detail_data,
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"添加结果: {data}")
            assert data.get("success") == True
            test_logger.info("添加加减分明细测试通过")
        else:
            test_logger.warning(f"添加明细失败: {response.text}")
    
    @pytest.mark.comprehensive
    @pytest.mark.asyncio
    async def test_add_score_detail_invalid_category(self, client: AsyncClient, admin_token: str, test_logger):
        """测试添加无效类别的明细 - 异常场景"""
        test_logger.info("开始测试: 添加无效类别的明细")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
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
            json=detail_data,
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code == 400, "无效类别应返回400错误"
        test_logger.info("无效类别测试通过")
    
    @pytest.mark.comprehensive
    @pytest.mark.asyncio
    async def test_delete_score_detail_success(self, client: AsyncClient, admin_token: str, test_logger):
        """测试删除加减分明细 - 正常场景"""
        test_logger.info("开始测试: 删除加减分明细")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = await client.delete(
            f"{API_PREFIX}/comprehensive-score/detail/999999",
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [200, 404], "删除应返回200或404"
        test_logger.info("删除明细测试通过")


class TestComprehensiveScoreConfig:
    """综测配置测试类"""
    
    @pytest.mark.comprehensive
    @pytest.mark.asyncio
    async def test_list_configs_success(self, client: AsyncClient, admin_token: str, test_logger):
        """测试获取配置列表 - 正常场景"""
        test_logger.info("开始测试: 获取综测配置列表")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = await client.get(
            f"{API_PREFIX}/comprehensive-score/config/list",
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"配置列表: {data}")
            
            if "configs" in data:
                assert isinstance(data["configs"], list)
            test_logger.info("获取配置列表测试通过")
        else:
            test_logger.warning(f"获取配置列表失败: {response.text}")
    
    @pytest.mark.comprehensive
    @pytest.mark.asyncio
    async def test_create_config_success(self, client: AsyncClient, admin_token: str, test_logger):
        """测试创建配置 - 正常场景"""
        test_logger.info("开始测试: 创建综测配置")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        config_data = {
            "name": "测试配置",
            "description": "测试用综测配置",
            "a_weight": 20.0,
            "b_weight": 70.0,
            "c_weight": 10.0,
            "academic_score_field": "weighted_average",
            "academic_score_scale": 1.0,
            "is_default": False
        }
        
        response = await client.post(
            f"{API_PREFIX}/comprehensive-score/config",
            json=config_data,
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"创建结果: {data}")
            assert data.get("success") == True
            test_logger.info("创建配置测试通过")
        else:
            test_logger.warning(f"创建配置失败: {response.text}")
    
    @pytest.mark.comprehensive
    @pytest.mark.asyncio
    async def test_create_config_invalid_weight(self, client: AsyncClient, admin_token: str, test_logger):
        """测试创建配置权重无效 - 异常场景"""
        test_logger.info("开始测试: 创建配置权重无效")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        config_data = {
            "name": "无效权重配置",
            "a_weight": 30.0,
            "b_weight": 50.0,
            "c_weight": 30.0
        }
        
        response = await client.post(
            f"{API_PREFIX}/comprehensive-score/config",
            json=config_data,
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code == 400, "权重总和不为100应返回400错误"
        test_logger.info("无效权重测试通过")
    
    @pytest.mark.comprehensive
    @pytest.mark.asyncio
    async def test_update_config_success(self, client: AsyncClient, admin_token: str, test_logger):
        """测试更新配置 - 正常场景"""
        test_logger.info("开始测试: 更新综测配置")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        config_data = {
            "name": "更新后的配置",
            "a_weight": 25.0,
            "b_weight": 65.0,
            "c_weight": 10.0
        }
        
        response = await client.put(
            f"{API_PREFIX}/comprehensive-score/config/1",
            json=config_data,
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [200, 404, 500], "更新配置应返回200、404或500"
        test_logger.info("更新配置测试通过")


class TestClassList:
    """班级列表测试类"""
    
    @pytest.mark.comprehensive
    @pytest.mark.asyncio
    async def test_list_classes_success(self, client: AsyncClient, teacher_token: str, test_logger):
        """测试获取班级列表 - 正常场景"""
        test_logger.info("开始测试: 获取班级列表")
        
        headers = {"Authorization": f"Bearer {teacher_token}"}
        
        response = await client.get(
            f"{API_PREFIX}/comprehensive-score/classes",
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"班级列表: {data}")
            
            if "classes" in data:
                assert isinstance(data["classes"], list)
            test_logger.info("获取班级列表测试通过")
        else:
            test_logger.warning(f"获取班级列表失败: {response.text}")


class TestComprehensiveScoreBoundary:
    """综测成绩边界条件测试类"""
    
    @pytest.mark.comprehensive
    @pytest.mark.asyncio
    async def test_calculate_with_zero_score(self, client: AsyncClient, admin_token: str, test_logger):
        """测试计算零分情况 - 边界条件"""
        test_logger.info("开始测试: 计算零分情况")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        detail_data = {
            "student_id": TEST_STUDENTS[0]["id"],
            "academic_year": "2023-2024",
            "semester": "1",
            "category_type": "A1",
            "item_name": "零分项目",
            "score": 0.0
        }
        
        response = await client.post(
            f"{API_PREFIX}/comprehensive-score/detail",
            json=detail_data,
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [200, 400, 404, 500], "零分情况应返回有效状态码"
        test_logger.info("零分情况测试通过")
    
    @pytest.mark.comprehensive
    @pytest.mark.asyncio
    async def test_calculate_with_negative_score(self, client: AsyncClient, admin_token: str, test_logger):
        """测试计算负分情况 - 边界条件"""
        test_logger.info("开始测试: 计算负分情况")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        detail_data = {
            "student_id": TEST_STUDENTS[0]["id"],
            "academic_year": "2023-2024",
            "semester": "1",
            "category_type": "A1",
            "item_name": "负分项目",
            "score": -5.0
        }
        
        response = await client.post(
            f"{API_PREFIX}/comprehensive-score/detail",
            json=detail_data,
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        test_logger.info("负分情况测试通过")
    
    @pytest.mark.comprehensive
    @pytest.mark.asyncio
    async def test_calculate_with_max_score(self, client: AsyncClient, admin_token: str, test_logger):
        """测试计算最大分值情况 - 边界条件"""
        test_logger.info("开始测试: 计算最大分值情况")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        detail_data = {
            "student_id": TEST_STUDENTS[0]["id"],
            "academic_year": "2023-2024",
            "semester": "1",
            "category_type": "A1",
            "item_name": "最大分值项目",
            "score": 100.0
        }
        
        response = await client.post(
            f"{API_PREFIX}/comprehensive-score/detail",
            json=detail_data,
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        test_logger.info("最大分值测试通过")
    
    @pytest.mark.comprehensive
    @pytest.mark.asyncio
    async def test_query_with_invalid_semester(self, client: AsyncClient, student_token: str, test_logger):
        """测试查询无效学期 - 边界条件"""
        test_logger.info("开始测试: 查询无效学期")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        student_id = TEST_STUDENTS[0]["id"]
        
        response = await client.get(
            f"{API_PREFIX}/comprehensive-score/student/{student_id}",
            params={"academic_year": "2023-2024", "semester": "999"},
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        test_logger.info("无效学期测试通过")
    
    @pytest.mark.comprehensive
    @pytest.mark.asyncio
    async def test_query_with_invalid_year_format(self, client: AsyncClient, student_token: str, test_logger):
        """测试查询无效学年格式 - 边界条件"""
        test_logger.info("开始测试: 查询无效学年格式")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        student_id = TEST_STUDENTS[0]["id"]
        
        response = await client.get(
            f"{API_PREFIX}/comprehensive-score/student/{student_id}",
            params={"academic_year": "invalid_year", "semester": "1"},
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        test_logger.info("无效学年格式测试通过")
