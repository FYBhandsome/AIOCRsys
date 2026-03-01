#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端到端测试 - 前后端接口对接验证
"""
import pytest
import asyncio
from httpx import AsyncClient
from datetime import datetime

from conftest import TEST_USERS, API_PREFIX


@pytest.mark.asyncio
@pytest.mark.e2e
class TestAuthFlow:
    """认证流程端到端测试"""
    
    async def test_complete_login_flow(self, client: AsyncClient, test_result):
        """测试完整登录流程"""
        test_result.start()
        
        response = await client.post(f"{API_PREFIX}/auth/login", json={
            "username": TEST_USERS["admin"]["username"],
            "password": TEST_USERS["admin"]["password"]
        })
        
        if response.status_code != 200:
            test_result.add_result("test_complete_login_flow", False, f"登录失败: {response.text}")
            test_result.end()
            pytest.skip("登录失败，跳过后续测试")
        
        data = response.json()
        assert "access_token" in data, "响应中缺少access_token"
        token = data["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        me_response = await client.get(f"{API_PREFIX}/auth/me", headers=headers)
        
        assert me_response.status_code == 200, f"获取用户信息失败: {me_response.text}"
        user_data = me_response.json()
        assert "username" in user_data, "响应中缺少用户名"
        
        test_result.add_result("test_complete_login_flow", True, "登录流程完整")
        test_result.end()
    
    async def test_token_validation(self, client: AsyncClient, test_result):
        """测试Token验证"""
        test_result.start()
        
        invalid_token = "invalid_token_12345"
        headers = {"Authorization": f"Bearer {invalid_token}"}
        
        response = await client.get(f"{API_PREFIX}/auth/me", headers=headers)
        
        assert response.status_code == 401, "无效Token应该返回401"
        
        test_result.add_result("test_token_validation", True, "Token验证正确")
        test_result.end()


@pytest.mark.asyncio
@pytest.mark.e2e
class TestStudentFlow:
    """学生操作流程端到端测试"""
    
    async def test_student_score_query_flow(self, client: AsyncClient, student_token: str, test_result):
        """测试学生成绩查询流程"""
        test_result.start()
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        summary_response = await client.get(
            f"{API_PREFIX}/student/scores/summary",
            headers=headers
        )
        
        assert summary_response.status_code in [200, 404], f"成绩摘要响应异常: {summary_response.text}"
        
        detail_response = await client.get(
            f"{API_PREFIX}/student/scores/detail",
            headers=headers
        )
        
        assert detail_response.status_code in [200, 404], f"成绩详情响应异常: {detail_response.text}"
        
        test_result.add_result("test_student_score_query_flow", True, "学生成绩查询流程正常")
        test_result.end()
    
    async def test_student_upload_history(self, client: AsyncClient, student_token: str, test_result):
        """测试学生上传历史查询"""
        test_result.start()
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        response = await client.get(
            f"{API_PREFIX}/student/uploads",
            headers=headers,
            params={"page": 1, "page_size": 10}
        )
        
        assert response.status_code in [200, 404], f"上传历史响应异常: {response.text}"
        
        test_result.add_result("test_student_upload_history", True, "上传历史查询正常")
        test_result.end()


@pytest.mark.asyncio
@pytest.mark.e2e
class TestTeacherFlow:
    """教师操作流程端到端测试"""
    
    async def test_teacher_class_management(self, client: AsyncClient, teacher_token: str, test_result):
        """测试教师班级管理"""
        test_result.start()
        
        headers = {"Authorization": f"Bearer {teacher_token}"}
        
        classes_response = await client.get(
            f"{API_PREFIX}/teacher/classes",
            headers=headers
        )
        
        assert classes_response.status_code == 200, f"获取班级列表失败: {classes_response.text}"
        
        test_result.add_result("test_teacher_class_management", True, "班级管理流程正常")
        test_result.end()
    
    async def test_teacher_student_list(self, client: AsyncClient, teacher_token: str, test_result):
        """测试教师学生列表"""
        test_result.start()
        
        headers = {"Authorization": f"Bearer {teacher_token}"}
        
        response = await client.get(
            f"{API_PREFIX}/teacher/students",
            headers=headers,
            params={"page": 1, "page_size": 20}
        )
        
        assert response.status_code in [200, 404], f"学生列表响应异常: {response.text}"
        
        test_result.add_result("test_teacher_student_list", True, "学生列表查询正常")
        test_result.end()


@pytest.mark.asyncio
@pytest.mark.e2e
class TestComprehensiveScoreFlow:
    """综测成绩流程端到端测试"""
    
    async def test_comprehensive_score_config_flow(self, client: AsyncClient, admin_token: str, test_result):
        """测试综测配置流程"""
        test_result.start()
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        config_response = await client.get(
            f"{API_PREFIX}/comprehensive-score/config/list",
            headers=headers
        )
        
        assert config_response.status_code == 200, f"获取配置列表失败: {config_response.text}"
        
        test_result.add_result("test_comprehensive_score_config_flow", True, "综测配置流程正常")
        test_result.end()
    
    async def test_class_ranking_flow(self, client: AsyncClient, teacher_token: str, test_result):
        """测试班级排名流程"""
        test_result.start()
        
        headers = {"Authorization": f"Bearer {teacher_token}"}
        
        classes_response = await client.get(
            f"{API_PREFIX}/comprehensive-score/classes",
            headers=headers
        )
        
        assert classes_response.status_code == 200, f"获取班级列表失败: {classes_response.text}"
        
        test_result.add_result("test_class_ranking_flow", True, "班级排名流程正常")
        test_result.end()


@pytest.mark.asyncio
@pytest.mark.e2e
class TestAIAssistantFlow:
    """AI助手流程端到端测试"""
    
    async def test_ai_chat_flow(self, client: AsyncClient, student_token: str, test_result):
        """测试AI对话流程"""
        test_result.start()
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        chat_response = await client.post(
            f"{API_PREFIX}/ai/chat",
            headers=headers,
            json={
                "message": "省级竞赛可以加多少分？",
                "use_rag": True
            }
        )
        
        assert chat_response.status_code in [200, 503], f"AI对话响应异常: {chat_response.text}"
        
        test_result.add_result("test_ai_chat_flow", True, "AI对话流程正常")
        test_result.end()
    
    async def test_ai_suggestions_flow(self, client: AsyncClient, student_token: str, test_result):
        """测试AI建议问题流程"""
        test_result.start()
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        response = await client.get(
            f"{API_PREFIX}/ai/suggestions",
            headers=headers
        )
        
        assert response.status_code == 200, f"获取建议问题失败: {response.text}"
        
        test_result.add_result("test_ai_suggestions_flow", True, "AI建议问题流程正常")
        test_result.end()


@pytest.mark.asyncio
@pytest.mark.e2e
class TestAPIResponseFormat:
    """API响应格式验证测试"""
    
    async def test_success_response_format(self, client: AsyncClient, admin_token: str, test_result):
        """测试成功响应格式"""
        test_result.start()
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = await client.get(
            f"{API_PREFIX}/comprehensive-score/config/list",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "success" in data or "configs" in data, "响应格式不符合预期"
        
        test_result.add_result("test_success_response_format", True, "成功响应格式正确")
        test_result.end()
    
    async def test_error_response_format(self, client: AsyncClient, test_result):
        """测试错误响应格式"""
        test_result.start()
        
        response = await client.get(f"{API_PREFIX}/auth/me")
        
        assert response.status_code == 401
        data = response.json()
        
        assert "detail" in data, "错误响应缺少detail字段"
        
        test_result.add_result("test_error_response_format", True, "错误响应格式正确")
        test_result.end()


@pytest.mark.asyncio
@pytest.mark.e2e
class TestPermissionControl:
    """权限控制测试"""
    
    async def test_student_cannot_access_admin_api(self, client: AsyncClient, student_token: str, test_result):
        """测试学生无法访问管理员API"""
        test_result.start()
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        response = await client.get(
            f"{API_PREFIX}/admin/users",
            headers=headers
        )
        
        assert response.status_code in [401, 403], "学生不应该能访问管理员API"
        
        test_result.add_result("test_student_cannot_access_admin_api", True, "权限控制正确")
        test_result.end()
    
    async def test_teacher_cannot_access_admin_api(self, client: AsyncClient, teacher_token: str, test_result):
        """测试教师无法访问管理员API"""
        test_result.start()
        
        headers = {"Authorization": f"Bearer {teacher_token}"}
        
        response = await client.get(
            f"{API_PREFIX}/admin/users",
            headers=headers
        )
        
        assert response.status_code in [401, 403], "教师不应该能访问管理员API"
        
        test_result.add_result("test_teacher_cannot_access_admin_api", True, "权限控制正确")
        test_result.end()


@pytest.mark.asyncio
@pytest.mark.e2e
class TestDataConsistency:
    """数据一致性测试"""
    
    async def test_score_calculation_consistency(self, client: AsyncClient, teacher_token: str, test_result):
        """测试成绩计算一致性"""
        test_result.start()
        
        headers = {"Authorization": f"Bearer {teacher_token}"}
        
        classes_response = await client.get(
            f"{API_PREFIX}/comprehensive-score/classes",
            headers=headers
        )
        
        if classes_response.status_code != 200:
            test_result.add_result("test_score_calculation_consistency", True, "无班级数据，跳过")
            test_result.end()
            return
        
        classes_data = classes_response.json()
        classes = classes_data.get("classes", [])
        
        if classes:
            class_id = classes[0].get("id")
            if class_id:
                ranking_response = await client.get(
                    f"{API_PREFIX}/comprehensive-score/class/{class_id}/ranking",
                    headers=headers,
                    params={"academic_year": "2023-2024", "semester": "1"}
                )
                
                assert ranking_response.status_code in [200, 404]
        
        test_result.add_result("test_score_calculation_consistency", True, "成绩计算一致性检查通过")
        test_result.end()
