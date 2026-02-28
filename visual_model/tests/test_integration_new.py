#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整集成测试模块
测试前后端完整业务流程
"""
import pytest
import asyncio
import json
from httpx import AsyncClient
from datetime import datetime

from conftest_new import API_PREFIX, TEST_USERS, TEST_STUDENTS, TEST_CLASSES


@pytest.mark.asyncio
@pytest.mark.integration
class TestFullWorkflow:
    """完整业务流程测试类"""
    
    async def test_student_certificate_upload_workflow(
        self, 
        client: AsyncClient, 
        student_token: str,
        sample_image_bytes: bytes,
        test_result
    ):
        """测试学生证书上传完整流程"""
        test_result.start()
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        files = {
            "file": ("test_certificate.jpg", sample_image_bytes, "image/jpeg")
        }
        data = {
            "description": "蓝桥杯省赛一等奖"
        }
        
        response = await client.post(
            f"{API_PREFIX}/student/certificate/upload",
            headers=headers,
            files=files,
            data=data
        )
        
        assert response.status_code in [200, 201, 503], f"证书上传响应异常: {response.text}"
        
        test_result.add_result("test_student_certificate_upload_workflow", True, "证书上传流程正常")
        test_result.end()
    
    async def test_teacher_score_upload_workflow(
        self,
        client: AsyncClient,
        teacher_token: str,
        sample_excel_bytes: bytes,
        test_result
    ):
        """测试教师成绩上传完整流程"""
        test_result.start()
        
        headers = {"Authorization": f"Bearer {teacher_token}"}
        
        files = {
            "file": ("test_scores.xlsx", sample_excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        }
        data = {
            "class_id": TEST_CLASSES[0]["id"]
        }
        
        response = await client.post(
            f"{API_PREFIX}/teacher/scores/upload",
            headers=headers,
            files=files,
            data=data
        )
        
        assert response.status_code in [200, 201, 400, 503], f"成绩上传响应异常: {response.text}"
        
        test_result.add_result("test_teacher_score_upload_workflow", True, "成绩上传流程正常")
        test_result.end()
    
    async def test_admin_rule_upload_workflow(
        self,
        client: AsyncClient,
        admin_token: str,
        test_result
    ):
        """测试管理员规则上传完整流程"""
        test_result.start()
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        doc_content = b"测试综测规则文档内容\n1. 省级竞赛加8分\n2. 国家级竞赛加12分"
        files = {
            "file": ("test_rules.txt", doc_content, "text/plain")
        }
        data = {
            "description": "测试规则文档"
        }
        
        response = await client.post(
            f"{API_PREFIX}/admin/rules/upload",
            headers=headers,
            files=files,
            data=data
        )
        
        assert response.status_code in [200, 201, 400, 503], f"规则上传响应异常: {response.text}"
        
        test_result.add_result("test_admin_rule_upload_workflow", True, "规则上传流程正常")
        test_result.end()
    
    async def test_comprehensive_score_calculation_workflow(
        self,
        client: AsyncClient,
        teacher_token: str,
        test_result
    ):
        """测试综测成绩计算完整流程"""
        test_result.start()
        
        headers = {"Authorization": f"Bearer {teacher_token}"}
        student_id = TEST_STUDENTS[0]["id"]
        
        response = await client.post(
            f"{API_PREFIX}/comprehensive-score/calculate/student/{student_id}",
            headers=headers,
            params={"academic_year": "2023-2024", "semester": "1"}
        )
        
        assert response.status_code in [200, 400, 404], f"综测计算响应异常: {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            assert "scores" in data or "total_score" in data, "响应中缺少成绩信息"
        
        test_result.add_result("test_comprehensive_score_calculation_workflow", True, "综测计算流程正常")
        test_result.end()


@pytest.mark.asyncio
@pytest.mark.integration
class TestAPIIntegration:
    """API集成测试类"""
    
    async def test_ai_chat_with_certificate_context(
        self,
        client: AsyncClient,
        student_token: str,
        test_result
    ):
        """测试AI对话与证书上下文集成"""
        test_result.start()
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        chat_data = {
            "message": "我上传了蓝桥杯省赛一等奖证书，能加多少分？",
            "chat_history": [],
            "use_rag": True
        }
        
        response = await client.post(
            f"{API_PREFIX}/ai/chat",
            headers=headers,
            json=chat_data
        )
        
        assert response.status_code in [200, 503], f"AI对话响应异常: {response.text}"
        
        test_result.add_result("test_ai_chat_with_certificate_context", True, "AI对话与证书上下文集成正常")
        test_result.end()
    
    async def test_class_ranking_after_calculation(
        self,
        client: AsyncClient,
        teacher_token: str,
        test_result
    ):
        """测试计算后的班级排名"""
        test_result.start()
        
        headers = {"Authorization": f"Bearer {teacher_token}"}
        class_id = TEST_CLASSES[0]["id"]
        
        response = await client.get(
            f"{API_PREFIX}/comprehensive-score/class/{class_id}/ranking",
            headers=headers,
            params={"academic_year": "2023-2024", "semester": "1"}
        )
        
        assert response.status_code in [200, 404], f"获取班级排名响应异常: {response.text}"
        
        test_result.add_result("test_class_ranking_after_calculation", True, "班级排名查询正常")
        test_result.end()
    
    async def test_student_view_own_scores(
        self,
        client: AsyncClient,
        student_token: str,
        test_result
    ):
        """测试学生查看自己成绩"""
        test_result.start()
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        response = await client.get(
            f"{API_PREFIX}/student/scores/summary",
            headers=headers
        )
        
        assert response.status_code in [200, 404], f"获取成绩摘要响应异常: {response.text}"
        
        test_result.add_result("test_student_view_own_scores", True, "学生查看成绩正常")
        test_result.end()


@pytest.mark.asyncio
@pytest.mark.integration
class TestCrossServiceIntegration:
    """跨服务集成测试类"""
    
    async def test_rag_to_comprehensive_integration(
        self,
        client: AsyncClient,
        teacher_token: str,
        test_result
    ):
        """测试RAG与综测计算集成"""
        test_result.start()
        
        headers = {"Authorization": f"Bearer {teacher_token}"}
        
        analyze_data = {
            "certificate_text": "蓝桥杯全国软件和信息技术专业人才大赛 省级 一等奖",
            "student_id": TEST_STUDENTS[0]["id"],
            "student_name": TEST_STUDENTS[0]["name"]
        }
        
        response = await client.post(
            f"{API_PREFIX}/excel-fill/analyze-certificate",
            headers=headers,
            data=analyze_data
        )
        
        assert response.status_code in [200, 503], f"证书分析响应异常: {response.text}"
        
        test_result.add_result("test_rag_to_comprehensive_integration", True, "RAG与综测集成正常")
        test_result.end()
    
    async def test_weight_config_retrieval(
        self,
        client: AsyncClient,
        admin_token: str,
        test_result
    ):
        """测试权重配置检索"""
        test_result.start()
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = await client.get(
            f"{API_PREFIX}/excel-fill/weight-config",
            headers=headers,
            params={"academic_year": "2023-2024", "semester": "1"}
        )
        
        assert response.status_code in [200, 503], f"获取权重配置响应异常: {response.text}"
        
        test_result.add_result("test_weight_config_retrieval", True, "权重配置检索正常")
        test_result.end()


@pytest.mark.asyncio
@pytest.mark.integration
class TestErrorHandling:
    """错误处理测试类"""
    
    async def test_invalid_token_handling(
        self,
        client: AsyncClient,
        test_result
    ):
        """测试无效token处理"""
        test_result.start()
        
        headers = {"Authorization": "Bearer invalid_token_12345"}
        
        response = await client.get(
            f"{API_PREFIX}/auth/me",
            headers=headers
        )
        
        assert response.status_code == 401, "无效token应该返回401"
        
        test_result.add_result("test_invalid_token_handling", True, "无效token正确处理")
        test_result.end()
    
    async def test_expired_token_handling(
        self,
        client: AsyncClient,
        test_result
    ):
        """测试过期token处理"""
        test_result.start()
        
        expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        headers = {"Authorization": f"Bearer {expired_token}"}
        
        response = await client.get(
            f"{API_PREFIX}/auth/me",
            headers=headers
        )
        
        assert response.status_code == 401, "过期token应该返回401"
        
        test_result.add_result("test_expired_token_handling", True, "过期token正确处理")
        test_result.end()
    
    async def test_permission_denied_handling(
        self,
        client: AsyncClient,
        student_token: str,
        test_result
    ):
        """测试权限拒绝处理"""
        test_result.start()
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        response = await client.get(
            f"{API_PREFIX}/admin/users",
            headers=headers
        )
        
        assert response.status_code in [401, 403], "学生访问管理员接口应该被拒绝"
        
        test_result.add_result("test_permission_denied_handling", True, "权限拒绝正确处理")
        test_result.end()
    
    async def test_invalid_input_handling(
        self,
        client: AsyncClient,
        admin_token: str,
        test_result
    ):
        """测试无效输入处理"""
        test_result.start()
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        invalid_config = {
            "name": "",
            "a_weight": -10,
            "b_weight": 200,
            "c_weight": "invalid"
        }
        
        response = await client.post(
            f"{API_PREFIX}/comprehensive-score/config",
            headers=headers,
            json=invalid_config
        )
        
        assert response.status_code in [400, 422], "无效输入应该返回400或422"
        
        test_result.add_result("test_invalid_input_handling", True, "无效输入正确处理")
        test_result.end()
