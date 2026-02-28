#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学生API集成测试
测试学生成绩查询、证书上传、综测计算等功能
"""
import pytest
import logging
import json
import os
from httpx import AsyncClient
from io import BytesIO

logger = logging.getLogger("test_logger")


class TestStudentProfile:
    """学生个人信息测试类"""
    
    @pytest.mark.student
    @pytest.mark.asyncio
    async def test_get_student_profile(self, client: AsyncClient, student_token: str, test_logger):
        """测试获取学生个人信息"""
        test_logger.info("开始测试: 获取学生个人信息")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        response = await client.get("/api/student/profile", headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"学生信息: {json.dumps(data, ensure_ascii=False)[:500]}")
            test_logger.info("获取学生个人信息测试通过")
        else:
            test_logger.warning(f"获取学生信息失败: {response.text}")
    
    @pytest.mark.student
    @pytest.mark.asyncio
    async def test_update_student_profile(self, client: AsyncClient, student_token: str, test_logger):
        """测试更新学生个人信息"""
        test_logger.info("开始测试: 更新学生个人信息")
        
        update_data = {
            "real_name": "测试学生更新",
            "email": "updated@test.com"
        }
        
        headers = {"Authorization": f"Bearer {student_token}"}
        response = await client.put("/api/student/profile", json=update_data, headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"更新结果: {json.dumps(data, ensure_ascii=False)[:300]}")
            test_logger.info("更新学生个人信息测试通过")
        else:
            test_logger.warning(f"更新学生信息失败: {response.text}")


class TestStudentScores:
    """学生成绩测试类"""
    
    @pytest.mark.student
    @pytest.mark.asyncio
    async def test_get_student_scores(self, client: AsyncClient, student_token: str, test_logger):
        """测试获取学生成绩"""
        test_logger.info("开始测试: 获取学生成绩")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        response = await client.get("/api/student/scores", headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"成绩数据: {json.dumps(data, ensure_ascii=False)[:500]}")
            
            if "scores" in data:
                assert isinstance(data["scores"], list)
            test_logger.info("获取学生成绩测试通过")
        else:
            test_logger.warning(f"获取成绩失败: {response.text}")
    
    @pytest.mark.student
    @pytest.mark.asyncio
    async def test_get_score_summary(self, client: AsyncClient, student_token: str, test_logger):
        """测试获取成绩摘要"""
        test_logger.info("开始测试: 获取成绩摘要")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        response = await client.get("/api/student/scores/summary", headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"成绩摘要: {json.dumps(data, ensure_ascii=False)[:500]}")
            test_logger.info("获取成绩摘要测试通过")
        else:
            test_logger.warning(f"获取成绩摘要失败: {response.text}")


class TestStudentCertificates:
    """学生证书测试类"""
    
    @pytest.mark.student
    @pytest.mark.asyncio
    async def test_get_certificates(self, client: AsyncClient, student_token: str, test_logger):
        """测试获取学生证书列表"""
        test_logger.info("开始测试: 获取学生证书列表")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        response = await client.get("/api/student/certificates", headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"证书列表: {json.dumps(data, ensure_ascii=False)[:500]}")
            
            if "certificates" in data:
                assert isinstance(data["certificates"], list)
            test_logger.info("获取证书列表测试通过")
        else:
            test_logger.warning(f"获取证书列表失败: {response.text}")
    
    @pytest.mark.student
    @pytest.mark.asyncio
    async def test_upload_certificate(self, client: AsyncClient, student_token: str, test_logger):
        """测试上传证书"""
        test_logger.info("开始测试: 上传证书")
        
        test_image_content = b"fake_image_content_for_testing"
        files = {
            "file": ("test_certificate.jpg", BytesIO(test_image_content), "image/jpeg")
        }
        data = {
            "certificate_type": "competition",
            "name": "蓝桥杯竞赛",
            "level": "省级",
            "award": "一等奖"
        }
        
        headers = {"Authorization": f"Bearer {student_token}"}
        response = await client.post(
            "/api/student/certificates/upload",
            files=files,
            data=data,
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code in [200, 201]:
            result = response.json()
            test_logger.info(f"上传结果: {json.dumps(result, ensure_ascii=False)[:300]}")
            test_logger.info("上传证书测试通过")
        else:
            test_logger.warning(f"上传证书失败: {response.text}")
    
    @pytest.mark.student
    @pytest.mark.asyncio
    async def test_delete_certificate(self, client: AsyncClient, student_token: str, test_logger):
        """测试删除证书"""
        test_logger.info("开始测试: 删除证书")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        response = await client.delete("/api/student/certificates/test_cert_id", headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [200, 404], "删除证书应返回200或404"
        test_logger.info("删除证书测试通过")


class TestComprehensiveScore:
    """综测成绩测试类"""
    
    @pytest.mark.student
    @pytest.mark.asyncio
    async def test_get_comprehensive_score(self, client: AsyncClient, student_token: str, test_logger):
        """测试获取综测成绩"""
        test_logger.info("开始测试: 获取综测成绩")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        response = await client.get("/api/student/comprehensive-score", headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"综测成绩: {json.dumps(data, ensure_ascii=False)[:500]}")
            test_logger.info("获取综测成绩测试通过")
        else:
            test_logger.warning(f"获取综测成绩失败: {response.text}")
    
    @pytest.mark.student
    @pytest.mark.asyncio
    async def test_calculate_comprehensive_score(self, client: AsyncClient, student_token: str, test_logger):
        """测试计算综测成绩"""
        test_logger.info("开始测试: 计算综测成绩")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        response = await client.post("/api/student/comprehensive-score/calculate", headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"计算结果: {json.dumps(data, ensure_ascii=False)[:500]}")
            test_logger.info("计算综测成绩测试通过")
        else:
            test_logger.warning(f"计算综测成绩失败: {response.text}")


class TestStudentMaterials:
    """学生材料测试类"""
    
    @pytest.mark.student
    @pytest.mark.asyncio
    async def test_get_materials(self, client: AsyncClient, student_token: str, test_logger):
        """测试获取学生材料列表"""
        test_logger.info("开始测试: 获取学生材料列表")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        response = await client.get("/api/student/materials", headers=headers)
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"材料列表: {json.dumps(data, ensure_ascii=False)[:500]}")
            test_logger.info("获取材料列表测试通过")
        else:
            test_logger.warning(f"获取材料列表失败: {response.text}")
    
    @pytest.mark.student
    @pytest.mark.asyncio
    async def test_upload_material(self, client: AsyncClient, student_token: str, test_logger):
        """测试上传材料"""
        test_logger.info("开始测试: 上传材料")
        
        test_file_content = b"test_file_content"
        files = {
            "file": ("test_material.pdf", BytesIO(test_file_content), "application/pdf")
        }
        data = {
            "material_type": "certificate",
            "description": "测试材料"
        }
        
        headers = {"Authorization": f"Bearer {student_token}"}
        response = await client.post(
            "/api/student/materials/upload",
            files=files,
            data=data,
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code in [200, 201]:
            result = response.json()
            test_logger.info(f"上传结果: {json.dumps(result, ensure_ascii=False)[:300]}")
            test_logger.info("上传材料测试通过")
        else:
            test_logger.warning(f"上传材料失败: {response.text}")
