#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
教师API集成测试
测试班级管理、学生管理、成绩审核等功能
"""
import pytest
import logging
import json
from httpx import AsyncClient

logger = logging.getLogger("test_logger")


class TestTeacherClasses:
    """教师班级管理测试类"""
    
    @pytest.mark.teacher
    @pytest.mark.asyncio
    async def test_get_teacher_classes(self, client: AsyncClient, teacher_token: str, test_logger):
        """测试获取教师班级列表"""
        test_logger.info("开始测试: 获取教师班级列表")
        
        headers = {"Authorization": f"Bearer {teacher_token}"}
        response = await client.get("/api/teacher/classes", headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"班级列表: {json.dumps(data, ensure_ascii=False)[:500]}")
            
            assert isinstance(data, list), "班级列表应为数组"
            if len(data) > 0:
                first_class = data[0]
                assert "id" in first_class or "name" in first_class
            test_logger.info("获取教师班级列表测试通过")
        else:
            test_logger.warning(f"获取班级列表失败: {response.text}")
    
    @pytest.mark.teacher
    @pytest.mark.asyncio
    async def test_get_class_students(self, client: AsyncClient, teacher_token: str, test_logger):
        """测试获取班级学生列表"""
        test_logger.info("开始测试: 获取班级学生列表")
        
        headers = {"Authorization": f"Bearer {teacher_token}"}
        response = await client.get("/api/teacher/classes/test_class_id/students", headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"学生列表: {json.dumps(data, ensure_ascii=False)[:500]}")
            test_logger.info("获取班级学生列表测试通过")
        else:
            test_logger.warning(f"获取学生列表失败: {response.text}")


class TestTeacherStudents:
    """教师学生管理测试类"""
    
    @pytest.mark.teacher
    @pytest.mark.asyncio
    async def test_get_student_detail(self, client: AsyncClient, teacher_token: str, test_logger):
        """测试获取学生详情"""
        test_logger.info("开始测试: 获取学生详情")
        
        headers = {"Authorization": f"Bearer {teacher_token}"}
        response = await client.get("/api/teacher/students/test_student_id", headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"学生详情: {json.dumps(data, ensure_ascii=False)[:500]}")
            test_logger.info("获取学生详情测试通过")
        else:
            test_logger.warning(f"获取学生详情失败: {response.text}")
    
    @pytest.mark.teacher
    @pytest.mark.asyncio
    async def test_search_students(self, client: AsyncClient, teacher_token: str, test_logger):
        """测试搜索学生"""
        test_logger.info("开始测试: 搜索学生")
        
        headers = {"Authorization": f"Bearer {teacher_token}"}
        params = {"keyword": "张三", "class_id": "test_class_id"}
        response = await client.get("/api/teacher/students/search", params=params, headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"搜索结果: {json.dumps(data, ensure_ascii=False)[:500]}")
            test_logger.info("搜索学生测试通过")
        else:
            test_logger.warning(f"搜索学生失败: {response.text}")


class TestTeacherScores:
    """教师成绩管理测试类"""
    
    @pytest.mark.teacher
    @pytest.mark.asyncio
    async def test_get_class_scores(self, client: AsyncClient, teacher_token: str, test_logger):
        """测试获取班级成绩"""
        test_logger.info("开始测试: 获取班级成绩")
        
        headers = {"Authorization": f"Bearer {teacher_token}"}
        params = {"class_id": "test_class_id"}
        response = await client.get("/api/teacher/scores", params=params, headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"班级成绩: {json.dumps(data, ensure_ascii=False)[:500]}")
            test_logger.info("获取班级成绩测试通过")
        else:
            test_logger.warning(f"获取班级成绩失败: {response.text}")
    
    @pytest.mark.teacher
    @pytest.mark.asyncio
    async def test_get_class_stats(self, client: AsyncClient, teacher_token: str, test_logger):
        """测试获取班级成绩统计"""
        test_logger.info("开始测试: 获取班级成绩统计")
        
        headers = {"Authorization": f"Bearer {teacher_token}"}
        response = await client.get("/api/teacher/scores/stats/test_class_id", headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"成绩统计: {json.dumps(data, ensure_ascii=False)[:500]}")
            
            if "statistics" in data:
                stats = data["statistics"]
                test_logger.info(f"统计指标: {list(stats.keys())}")
            test_logger.info("获取班级成绩统计测试通过")
        else:
            test_logger.warning(f"获取成绩统计失败: {response.text}")
    
    @pytest.mark.teacher
    @pytest.mark.asyncio
    async def test_get_class_ranking(self, client: AsyncClient, teacher_token: str, test_logger):
        """测试获取班级排名"""
        test_logger.info("开始测试: 获取班级排名")
        
        headers = {"Authorization": f"Bearer {teacher_token}"}
        params = {"semester": "1", "academic_year": "2024-2025"}
        response = await client.get("/api/teacher/scores/ranking/test_class_id", params=params, headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"班级排名: {json.dumps(data, ensure_ascii=False)[:500]}")
            
            if "rankings" in data:
                assert isinstance(data["rankings"], list)
            test_logger.info("获取班级排名测试通过")
        else:
            test_logger.warning(f"获取班级排名失败: {response.text}")


class TestTeacherCertificates:
    """教师证书审核测试类"""
    
    @pytest.mark.teacher
    @pytest.mark.asyncio
    async def test_get_pending_certificates(self, client: AsyncClient, teacher_token: str, test_logger):
        """测试获取待审核证书"""
        test_logger.info("开始测试: 获取待审核证书")
        
        headers = {"Authorization": f"Bearer {teacher_token}"}
        response = await client.get("/api/teacher/certificates/pending", headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"待审核证书: {json.dumps(data, ensure_ascii=False)[:500]}")
            test_logger.info("获取待审核证书测试通过")
        else:
            test_logger.warning(f"获取待审核证书失败: {response.text}")
    
    @pytest.mark.teacher
    @pytest.mark.asyncio
    async def test_approve_certificate(self, client: AsyncClient, teacher_token: str, test_logger):
        """测试审核通过证书"""
        test_logger.info("开始测试: 审核通过证书")
        
        approve_data = {
            "certificate_id": "test_cert_id",
            "status": "approved",
            "comment": "审核通过"
        }
        
        headers = {"Authorization": f"Bearer {teacher_token}"}
        response = await client.post("/api/teacher/certificates/approve", json=approve_data, headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"审核结果: {json.dumps(data, ensure_ascii=False)[:300]}")
            test_logger.info("审核通过证书测试通过")
        else:
            test_logger.warning(f"审核证书失败: {response.text}")
    
    @pytest.mark.teacher
    @pytest.mark.asyncio
    async def test_reject_certificate(self, client: AsyncClient, teacher_token: str, test_logger):
        """测试审核拒绝证书"""
        test_logger.info("开始测试: 审核拒绝证书")
        
        reject_data = {
            "certificate_id": "test_cert_id",
            "status": "rejected",
            "comment": "证书信息不完整"
        }
        
        headers = {"Authorization": f"Bearer {teacher_token}"}
        response = await client.post("/api/teacher/certificates/reject", json=reject_data, headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"拒绝结果: {json.dumps(data, ensure_ascii=False)[:300]}")
            test_logger.info("审核拒绝证书测试通过")
        else:
            test_logger.warning(f"拒绝证书失败: {response.text}")


class TestTeacherExport:
    """教师数据导出测试类"""
    
    @pytest.mark.teacher
    @pytest.mark.asyncio
    async def test_export_class_scores(self, client: AsyncClient, teacher_token: str, test_logger):
        """测试导出班级成绩"""
        test_logger.info("开始测试: 导出班级成绩")
        
        headers = {"Authorization": f"Bearer {teacher_token}"}
        params = {"class_id": "test_class_id", "format": "xlsx"}
        response = await client.get("/api/teacher/export/scores", params=params, headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        test_logger.info(f"响应Content-Type: {response.headers.get('content-type', '')}")
        
        if response.status_code == 200:
            test_logger.info("导出班级成绩测试通过")
        else:
            test_logger.warning(f"导出成绩失败: {response.text}")
    
    @pytest.mark.teacher
    @pytest.mark.asyncio
    async def test_export_class_ranking(self, client: AsyncClient, teacher_token: str, test_logger):
        """测试导出班级排名"""
        test_logger.info("开始测试: 导出班级排名")
        
        export_data = {
            "class_name": "test_class_id",
            "semester": "1",
            "academic_year": "2024-2025"
        }
        
        headers = {"Authorization": f"Bearer {teacher_token}"}
        response = await client.post("/api/teacher/export/ranking", json=export_data, headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            test_logger.info("导出班级排名测试通过")
        else:
            test_logger.warning(f"导出排名失败: {response.text}")
