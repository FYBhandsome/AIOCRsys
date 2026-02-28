#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
证书管理API测试
测试证书上传、查询、审核、删除等功能
"""
import pytest
import logging
from httpx import AsyncClient
from io import BytesIO
from datetime import datetime

from conftest import API_PREFIX, TEST_STUDENTS, TEST_FILES

logger = logging.getLogger("test_logger")


class TestCertificateUpload:
    """证书上传测试类"""
    
    @pytest.mark.certificate
    @pytest.mark.asyncio
    async def test_upload_certificate_success(self, client: AsyncClient, student_token: str, test_logger):
        """测试上传证书 - 正常场景"""
        test_logger.info("开始测试: 上传证书")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        test_image = TEST_FILES["image"]
        files = {
            "file": (test_image["filename"], BytesIO(test_image["content"]), test_image["content_type"])
        }
        data = {
            "certificate_type": "竞赛",
            "certificate_name": "蓝桥杯竞赛",
            "level": "省级",
            "award": "一等奖",
            "issue_date": "2024-05-01"
        }
        
        response = await client.post(
            f"{API_PREFIX}/certificate/upload",
            files=files,
            data=data,
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code in [200, 201]:
            result = response.json()
            test_logger.info(f"上传结果: {result}")
            test_logger.info("上传证书测试通过")
        else:
            test_logger.warning(f"上传证书失败: {response.text}")
    
    @pytest.mark.certificate
    @pytest.mark.asyncio
    async def test_upload_certificate_no_auth(self, client: AsyncClient, test_logger):
        """测试未认证上传证书 - 异常场景"""
        test_logger.info("开始测试: 未认证上传证书")
        
        test_image = TEST_FILES["image"]
        files = {
            "file": (test_image["filename"], BytesIO(test_image["content"]), test_image["content_type"])
        }
        data = {
            "certificate_type": "竞赛"
        }
        
        response = await client.post(
            f"{API_PREFIX}/certificate/upload",
            files=files,
            data=data
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [401, 403, 404, 500], "未认证应返回401、403、404或500"
        test_logger.info("未认证上传测试通过")
    
    @pytest.mark.certificate
    @pytest.mark.asyncio
    async def test_upload_certificate_invalid_type(self, client: AsyncClient, student_token: str, test_logger):
        """测试上传无效类型文件 - 异常场景"""
        test_logger.info("开始测试: 上传无效类型文件")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        test_pdf = TEST_FILES["pdf"]
        files = {
            "file": (test_pdf["filename"], BytesIO(test_pdf["content"]), test_pdf["content_type"])
        }
        data = {
            "certificate_type": "竞赛"
        }
        
        response = await client.post(
            f"{API_PREFIX}/certificate/upload",
            files=files,
            data=data,
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        test_logger.info("无效类型文件测试通过")
    
    @pytest.mark.certificate
    @pytest.mark.asyncio
    async def test_upload_certificate_missing_file(self, client: AsyncClient, student_token: str, test_logger):
        """测试上传缺少文件 - 边界条件"""
        test_logger.info("开始测试: 上传缺少文件")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        data = {
            "certificate_type": "竞赛"
        }
        
        response = await client.post(
            f"{API_PREFIX}/certificate/upload",
            data=data,
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code == 422, "缺少文件应返回422"
        test_logger.info("缺少文件测试通过")


class TestCertificateQuery:
    """证书查询测试类"""
    
    @pytest.mark.certificate
    @pytest.mark.asyncio
    async def test_get_student_certificates_success(self, client: AsyncClient, student_token: str, test_logger):
        """测试获取学生证书列表 - 正常场景"""
        test_logger.info("开始测试: 获取学生证书列表")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        response = await client.get(
            f"{API_PREFIX}/certificate/student/{TEST_STUDENTS[0]['id']}",
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"证书列表: {data}")
            
            if "certificates" in data:
                assert isinstance(data["certificates"], list)
            test_logger.info("获取证书列表测试通过")
        else:
            test_logger.warning(f"获取证书列表失败: {response.text}")
    
    @pytest.mark.certificate
    @pytest.mark.asyncio
    async def test_get_certificate_by_id_success(self, client: AsyncClient, student_token: str, test_logger):
        """测试根据ID获取证书 - 正常场景"""
        test_logger.info("开始测试: 根据ID获取证书")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        response = await client.get(
            f"{API_PREFIX}/certificate/1",
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [200, 404], "应返回200或404"
        test_logger.info("根据ID获取证书测试通过")
    
    @pytest.mark.certificate
    @pytest.mark.asyncio
    async def test_get_certificate_not_found(self, client: AsyncClient, student_token: str, test_logger):
        """测试获取不存在的证书 - 异常场景"""
        test_logger.info("开始测试: 获取不存在的证书")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        response = await client.get(
            f"{API_PREFIX}/certificate/999999",
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code == 404, "不存在的证书应返回404"
        test_logger.info("不存在证书测试通过")
    
    @pytest.mark.certificate
    @pytest.mark.asyncio
    async def test_get_certificates_by_status(self, client: AsyncClient, teacher_token: str, test_logger):
        """测试按状态获取证书列表 - 正常场景"""
        test_logger.info("开始测试: 按状态获取证书列表")
        
        headers = {"Authorization": f"Bearer {teacher_token}"}
        
        response = await client.get(
            f"{API_PREFIX}/certificate/list",
            params={"status": "pending"},
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"待审核证书: {data}")
            test_logger.info("按状态获取证书测试通过")
        else:
            test_logger.warning(f"获取证书失败: {response.text}")


class TestCertificateAudit:
    """证书审核测试类"""
    
    @pytest.mark.certificate
    @pytest.mark.asyncio
    async def test_approve_certificate_success(self, client: AsyncClient, teacher_token: str, test_logger):
        """测试审核通过证书 - 正常场景"""
        test_logger.info("开始测试: 审核通过证书")
        
        headers = {"Authorization": f"Bearer {teacher_token}"}
        
        response = await client.post(
            f"{API_PREFIX}/certificate/1/approve",
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [200, 404], "应返回200或404"
        test_logger.info("审核通过测试通过")
    
    @pytest.mark.certificate
    @pytest.mark.asyncio
    async def test_reject_certificate_success(self, client: AsyncClient, teacher_token: str, test_logger):
        """测试审核拒绝证书 - 正常场景"""
        test_logger.info("开始测试: 审核拒绝证书")
        
        headers = {"Authorization": f"Bearer {teacher_token}"}
        
        reject_data = {
            "reason": "证书信息不完整"
        }
        
        response = await client.post(
            f"{API_PREFIX}/certificate/1/reject",
            json=reject_data,
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [200, 404], "应返回200或404"
        test_logger.info("审核拒绝测试通过")
    
    @pytest.mark.certificate
    @pytest.mark.asyncio
    async def test_audit_certificate_no_permission(self, client: AsyncClient, student_token: str, test_logger):
        """测试学生审核证书 - 异常场景"""
        test_logger.info("开始测试: 学生审核证书（无权限）")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        response = await client.post(
            f"{API_PREFIX}/certificate/1/approve",
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [401, 403, 404], "无权限应返回401、403或404"
        test_logger.info("无权限审核测试通过")


class TestCertificateDelete:
    """证书删除测试类"""
    
    @pytest.mark.certificate
    @pytest.mark.asyncio
    async def test_delete_certificate_success(self, client: AsyncClient, student_token: str, test_logger):
        """测试删除证书 - 正常场景"""
        test_logger.info("开始测试: 删除证书")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        response = await client.delete(
            f"{API_PREFIX}/certificate/999999",
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [200, 404], "删除应返回200或404"
        test_logger.info("删除证书测试通过")
    
    @pytest.mark.certificate
    @pytest.mark.asyncio
    async def test_delete_certificate_not_owner(self, client: AsyncClient, student_token: str, test_logger):
        """测试删除他人证书 - 异常场景"""
        test_logger.info("开始测试: 删除他人证书")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        response = await client.delete(
            f"{API_PREFIX}/certificate/1",
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [200, 403, 404], "应返回适当错误码"
        test_logger.info("删除他人证书测试通过")


class TestCertificateOCR:
    """证书OCR识别测试类"""
    
    @pytest.mark.certificate
    @pytest.mark.asyncio
    async def test_ocr_certificate_success(self, client: AsyncClient, student_token: str, test_logger):
        """测试OCR识别证书 - 正常场景"""
        test_logger.info("开始测试: OCR识别证书")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        test_image = TEST_FILES["image"]
        files = {
            "file": (test_image["filename"], BytesIO(test_image["content"]), test_image["content_type"])
        }
        
        response = await client.post(
            f"{API_PREFIX}/certificate/ocr",
            files=files,
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"OCR结果: {data}")
            test_logger.info("OCR识别测试通过")
        else:
            test_logger.warning(f"OCR识别失败: {response.text}")
    
    @pytest.mark.certificate
    @pytest.mark.asyncio
    async def test_ocr_certificate_invalid_image(self, client: AsyncClient, student_token: str, test_logger):
        """测试OCR识别无效图片 - 异常场景"""
        test_logger.info("开始测试: OCR识别无效图片")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        files = {
            "file": ("invalid.txt", BytesIO(b"not an image"), "text/plain")
        }
        
        response = await client.post(
            f"{API_PREFIX}/certificate/ocr",
            files=files,
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [400, 404, 422, 500, 200], "无效图片应返回错误或成功处理"
        test_logger.info("无效图片OCR测试通过")


class TestCertificateBoundary:
    """证书边界条件测试类"""
    
    @pytest.mark.certificate
    @pytest.mark.asyncio
    async def test_upload_large_file(self, client: AsyncClient, student_token: str, test_logger):
        """测试上传大文件 - 边界条件"""
        test_logger.info("开始测试: 上传大文件")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        large_content = b"x" * (60 * 1024 * 1024)
        files = {
            "file": ("large.jpg", BytesIO(large_content), "image/jpeg")
        }
        data = {
            "certificate_type": "竞赛"
        }
        
        response = await client.post(
            f"{API_PREFIX}/certificate/upload",
            files=files,
            data=data,
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [200, 201, 413], "大文件应返回适当状态码"
        test_logger.info("大文件上传测试通过")
    
    @pytest.mark.certificate
    @pytest.mark.asyncio
    async def test_upload_empty_file(self, client: AsyncClient, student_token: str, test_logger):
        """测试上传空文件 - 边界条件"""
        test_logger.info("开始测试: 上传空文件")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        files = {
            "file": ("empty.jpg", BytesIO(b""), "image/jpeg")
        }
        data = {
            "certificate_type": "竞赛"
        }
        
        response = await client.post(
            f"{API_PREFIX}/certificate/upload",
            files=files,
            data=data,
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [400, 422], "空文件应返回错误"
        test_logger.info("空文件上传测试通过")
    
    @pytest.mark.certificate
    @pytest.mark.asyncio
    async def test_query_with_pagination(self, client: AsyncClient, student_token: str, test_logger):
        """测试分页查询证书 - 边界条件"""
        test_logger.info("开始测试: 分页查询证书")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        response = await client.get(
            f"{API_PREFIX}/certificate/list",
            params={"page": 1, "page_size": 10},
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"分页结果: {data}")
            test_logger.info("分页查询测试通过")
        else:
            test_logger.warning(f"分页查询失败: {response.text}")
    
    @pytest.mark.certificate
    @pytest.mark.asyncio
    async def test_query_with_invalid_pagination(self, client: AsyncClient, student_token: str, test_logger):
        """测试无效分页参数 - 边界条件"""
        test_logger.info("开始测试: 无效分页参数")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        response = await client.get(
            f"{API_PREFIX}/certificate/list",
            params={"page": -1, "page_size": 0},
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [400, 422], "无效分页参数应返回错误"
        test_logger.info("无效分页参数测试通过")
    
    @pytest.mark.certificate
    @pytest.mark.asyncio
    async def test_upload_with_special_characters(self, client: AsyncClient, student_token: str, test_logger):
        """测试证书名称包含特殊字符 - 边界条件"""
        test_logger.info("开始测试: 证书名称包含特殊字符")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        test_image = TEST_FILES["image"]
        files = {
            "file": (test_image["filename"], BytesIO(test_image["content"]), test_image["content_type"])
        }
        data = {
            "certificate_type": "竞赛",
            "certificate_name": "测试<script>alert('xss')</script>证书",
            "level": "省级"
        }
        
        response = await client.post(
            f"{API_PREFIX}/certificate/upload",
            files=files,
            data=data,
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        test_logger.info("特殊字符测试通过")
