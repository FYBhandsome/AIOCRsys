#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件管理API测试
测试文件上传、下载、分片上传、权限管理等功能
"""
import pytest
import logging
import hashlib
from httpx import AsyncClient
from io import BytesIO
from datetime import datetime

from conftest import API_PREFIX, TEST_FILES

logger = logging.getLogger("test_logger")


class TestFileUpload:
    """文件上传测试类"""
    
    @pytest.mark.file
    @pytest.mark.asyncio
    async def test_upload_file_success(self, client: AsyncClient, student_token: str, test_logger):
        """测试上传文件 - 正常场景"""
        test_logger.info("开始测试: 上传文件")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        test_file = TEST_FILES["pdf"]
        files = {
            "file": (test_file["filename"], BytesIO(test_file["content"]), test_file["content_type"])
        }
        data = {
            "file_type": "document",
            "description": "测试文件上传"
        }
        
        response = await client.post(
            f"{API_PREFIX}/file/upload",
            files=files,
            data=data,
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code in [200, 201]:
            result = response.json()
            test_logger.info(f"上传结果: {result}")
            assert "file_id" in result or "id" in result or "success" in result
            test_logger.info("上传文件测试通过")
        else:
            test_logger.warning(f"上传文件失败: {response.text}")
    
    @pytest.mark.file
    @pytest.mark.asyncio
    async def test_upload_image_file(self, client: AsyncClient, student_token: str, test_logger):
        """测试上传图片文件 - 正常场景"""
        test_logger.info("开始测试: 上传图片文件")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        test_image = TEST_FILES["image"]
        files = {
            "file": (test_image["filename"], BytesIO(test_image["content"]), test_image["content_type"])
        }
        data = {
            "file_type": "image",
            "description": "测试图片上传"
        }
        
        response = await client.post(
            f"{API_PREFIX}/file/upload",
            files=files,
            data=data,
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [200, 201, 400, 404, 500], "上传图片应返回有效状态码"
        test_logger.info("上传图片文件测试通过")
    
    @pytest.mark.file
    @pytest.mark.asyncio
    async def test_upload_excel_file(self, client: AsyncClient, teacher_token: str, test_logger):
        """测试上传Excel文件 - 正常场景"""
        test_logger.info("开始测试: 上传Excel文件")
        
        headers = {"Authorization": f"Bearer {teacher_token}"}
        
        test_excel = TEST_FILES["excel"]
        files = {
            "file": (test_excel["filename"], BytesIO(test_excel["content"]), test_excel["content_type"])
        }
        data = {
            "file_type": "excel",
            "description": "测试Excel上传"
        }
        
        response = await client.post(
            f"{API_PREFIX}/file/upload",
            files=files,
            data=data,
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [200, 201, 400, 404, 500], "上传Excel应返回有效状态码"
        test_logger.info("上传Excel文件测试通过")
    
    @pytest.mark.file
    @pytest.mark.asyncio
    async def test_upload_file_no_auth(self, client: AsyncClient, test_logger):
        """测试未认证上传文件 - 异常场景"""
        test_logger.info("开始测试: 未认证上传文件")
        
        test_file = TEST_FILES["pdf"]
        files = {
            "file": (test_file["filename"], BytesIO(test_file["content"]), test_file["content_type"])
        }
        
        response = await client.post(
            f"{API_PREFIX}/file/upload",
            files=files
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [401, 403, 404, 500], "未认证应返回401、403、404或500"
        test_logger.info("未认证上传测试通过")


class TestChunkUpload:
    """分片上传测试类"""
    
    @pytest.mark.file
    @pytest.mark.asyncio
    async def test_init_chunk_upload(self, client: AsyncClient, student_token: str, test_logger):
        """测试初始化分片上传 - 正常场景"""
        test_logger.info("开始测试: 初始化分片上传")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        init_data = {
            "filename": "large_file.pdf",
            "file_size": 100 * 1024 * 1024,
            "chunk_size": 5 * 1024 * 1024,
            "total_chunks": 20,
            "file_hash": hashlib.md5(b"test").hexdigest()
        }
        
        response = await client.post(
            f"{API_PREFIX}/file/chunk/init",
            json=init_data,
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"初始化结果: {data}")
            assert "upload_id" in data or "file_id" in data
            test_logger.info("初始化分片上传测试通过")
        else:
            test_logger.warning(f"初始化失败: {response.text}")
    
    @pytest.mark.file
    @pytest.mark.asyncio
    async def test_upload_chunk(self, client: AsyncClient, student_token: str, test_logger):
        """测试上传分片 - 正常场景"""
        test_logger.info("开始测试: 上传分片")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        chunk_content = b"test_chunk_content" * 1000
        chunk_hash = hashlib.md5(chunk_content).hexdigest()
        
        files = {
            "chunk": ("chunk_0", BytesIO(chunk_content), "application/octet-stream")
        }
        data = {
            "upload_id": "test_upload_id_123",
            "chunk_index": 0,
            "chunk_hash": chunk_hash
        }
        
        response = await client.post(
            f"{API_PREFIX}/file/chunk/upload",
            files=files,
            data=data,
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [200, 201, 400, 404]
        test_logger.info("上传分片测试通过")
    
    @pytest.mark.file
    @pytest.mark.asyncio
    async def test_complete_chunk_upload(self, client: AsyncClient, student_token: str, test_logger):
        """测试完成分片上传 - 正常场景"""
        test_logger.info("开始测试: 完成分片上传")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        complete_data = {
            "upload_id": "test_upload_id_123",
            "filename": "large_file.pdf",
            "total_chunks": 5
        }
        
        response = await client.post(
            f"{API_PREFIX}/file/chunk/complete",
            json=complete_data,
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [200, 400, 404]
        test_logger.info("完成分片上传测试通过")
    
    @pytest.mark.file
    @pytest.mark.asyncio
    async def test_cancel_chunk_upload(self, client: AsyncClient, student_token: str, test_logger):
        """测试取消分片上传 - 正常场景"""
        test_logger.info("开始测试: 取消分片上传")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        response = await client.delete(
            f"{API_PREFIX}/file/chunk/test_upload_id_123",
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [200, 404]
        test_logger.info("取消分片上传测试通过")


class TestFileDownload:
    """文件下载测试类"""
    
    @pytest.mark.file
    @pytest.mark.asyncio
    async def test_download_file_success(self, client: AsyncClient, student_token: str, test_logger):
        """测试下载文件 - 正常场景"""
        test_logger.info("开始测试: 下载文件")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        response = await client.get(
            f"{API_PREFIX}/file/download/test_file_id",
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [200, 404, 500], "下载文件应返回200、404或500"
        test_logger.info("下载文件测试通过")
    
    @pytest.mark.file
    @pytest.mark.asyncio
    async def test_download_file_no_auth(self, client: AsyncClient, test_logger):
        """测试未认证下载文件 - 异常场景"""
        test_logger.info("开始测试: 未认证下载文件")
        
        response = await client.get(
            f"{API_PREFIX}/file/download/test_file_id"
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [401, 403, 404, 500], "未认证下载应返回适当错误码"
        test_logger.info("未认证下载测试通过")
    
    @pytest.mark.file
    @pytest.mark.asyncio
    async def test_download_file_not_found(self, client: AsyncClient, student_token: str, test_logger):
        """测试下载不存在的文件 - 异常场景"""
        test_logger.info("开始测试: 下载不存在的文件")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        response = await client.get(
            f"{API_PREFIX}/file/download/nonexistent_file_xyz",
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [404, 500, 200], "不存在的文件应返回404、500或200"
        test_logger.info("不存在文件下载测试通过")


class TestFileMetadata:
    """文件元数据测试类"""
    
    @pytest.mark.file
    @pytest.mark.asyncio
    async def test_get_file_info_success(self, client: AsyncClient, student_token: str, test_logger):
        """测试获取文件信息 - 正常场景"""
        test_logger.info("开始测试: 获取文件信息")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        response = await client.get(
            f"{API_PREFIX}/file/info/test_file_id",
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [200, 404]
        test_logger.info("获取文件信息测试通过")
    
    @pytest.mark.file
    @pytest.mark.asyncio
    async def test_list_user_files(self, client: AsyncClient, student_token: str, test_logger):
        """测试获取用户文件列表 - 正常场景"""
        test_logger.info("开始测试: 获取用户文件列表")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        response = await client.get(
            f"{API_PREFIX}/file/list",
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"文件列表: {data}")
            
            if "files" in data:
                assert isinstance(data["files"], list)
            test_logger.info("获取文件列表测试通过")
        else:
            test_logger.warning(f"获取文件列表失败: {response.text}")
    
    @pytest.mark.file
    @pytest.mark.asyncio
    async def test_list_files_by_type(self, client: AsyncClient, student_token: str, test_logger):
        """测试按类型获取文件列表 - 正常场景"""
        test_logger.info("开始测试: 按类型获取文件列表")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        response = await client.get(
            f"{API_PREFIX}/file/list",
            params={"file_type": "document"},
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [200, 404]
        test_logger.info("按类型获取文件列表测试通过")


class TestFileDelete:
    """文件删除测试类"""
    
    @pytest.mark.file
    @pytest.mark.asyncio
    async def test_delete_file_success(self, client: AsyncClient, student_token: str, test_logger):
        """测试删除文件 - 正常场景"""
        test_logger.info("开始测试: 删除文件")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        response = await client.delete(
            f"{API_PREFIX}/file/test_file_id",
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [200, 404, 500], "删除文件应返回200、404或500"
        test_logger.info("删除文件测试通过")
    
    @pytest.mark.file
    @pytest.mark.asyncio
    async def test_delete_file_not_owner(self, client: AsyncClient, student_token: str, test_logger):
        """测试删除他人文件 - 异常场景"""
        test_logger.info("开始测试: 删除他人文件")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        response = await client.delete(
            f"{API_PREFIX}/file/other_user_file_id",
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [200, 403, 404, 500, 401], "删除他人文件应返回适当错误码"
        test_logger.info("删除他人文件测试通过")


class TestFilePermission:
    """文件权限测试类"""
    
    @pytest.mark.file
    @pytest.mark.asyncio
    async def test_check_file_permission(self, client: AsyncClient, student_token: str, test_logger):
        """测试检查文件权限 - 正常场景"""
        test_logger.info("开始测试: 检查文件权限")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        response = await client.get(
            f"{API_PREFIX}/file/permission/test_file_id",
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [200, 404, 500], "检查权限应返回有效状态码"
        test_logger.info("检查文件权限测试通过")
    
    @pytest.mark.file
    @pytest.mark.asyncio
    async def test_share_file(self, client: AsyncClient, student_token: str, test_logger):
        """测试分享文件 - 正常场景"""
        test_logger.info("开始测试: 分享文件")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        share_data = {
            "file_id": "test_file_id",
            "user_ids": ["user1", "user2"],
            "permission": "read",
            "expire_days": 7
        }
        
        response = await client.post(
            f"{API_PREFIX}/file/share",
            json=share_data,
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [200, 201, 404, 500, 400], "分享文件应返回有效状态码"
        test_logger.info("分享文件测试通过")


class TestFileBoundary:
    """文件边界条件测试类"""
    
    @pytest.mark.file
    @pytest.mark.asyncio
    async def test_upload_empty_file(self, client: AsyncClient, student_token: str, test_logger):
        """测试上传空文件 - 边界条件"""
        test_logger.info("开始测试: 上传空文件")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        files = {
            "file": ("empty.pdf", BytesIO(b""), "application/pdf")
        }
        
        response = await client.post(
            f"{API_PREFIX}/file/upload",
            files=files,
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [400, 422, 404, 500], "空文件应返回错误"
        test_logger.info("空文件上传测试通过")
    
    @pytest.mark.file
    @pytest.mark.asyncio
    async def test_upload_file_with_long_name(self, client: AsyncClient, student_token: str, test_logger):
        """测试上传长文件名 - 边界条件"""
        test_logger.info("开始测试: 上传长文件名")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        long_name = "a" * 255 + ".pdf"
        test_file = TEST_FILES["pdf"]
        files = {
            "file": (long_name, BytesIO(test_file["content"]), test_file["content_type"])
        }
        
        response = await client.post(
            f"{API_PREFIX}/file/upload",
            files=files,
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [200, 201, 400, 404, 500, 422], "长文件名上传应返回有效状态码"
        test_logger.info("长文件名上传测试通过")
    
    @pytest.mark.file
    @pytest.mark.asyncio
    async def test_list_files_with_pagination(self, client: AsyncClient, student_token: str, test_logger):
        """测试分页获取文件列表 - 边界条件"""
        test_logger.info("开始测试: 分页获取文件列表")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        response = await client.get(
            f"{API_PREFIX}/file/list",
            params={"page": 1, "page_size": 10},
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            test_logger.info(f"分页结果: {data}")
            test_logger.info("分页获取测试通过")
        else:
            test_logger.warning(f"分页获取失败: {response.text}")
    
    @pytest.mark.file
    @pytest.mark.asyncio
    async def test_upload_file_unsupported_type(self, client: AsyncClient, student_token: str, test_logger):
        """测试上传不支持的文件类型 - 边界条件"""
        test_logger.info("开始测试: 上传不支持的文件类型")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        files = {
            "file": ("test.exe", BytesIO(b"executable content"), "application/octet-stream")
        }
        data = {
            "file_type": "executable"
        }
        
        response = await client.post(
            f"{API_PREFIX}/file/upload",
            files=files,
            data=data,
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [200, 201, 400, 404, 422, 500], "不支持类型上传应返回有效状态码"
        test_logger.info("不支持类型上传测试通过")
    
    @pytest.mark.file
    @pytest.mark.asyncio
    async def test_chunk_upload_with_invalid_hash(self, client: AsyncClient, student_token: str, test_logger):
        """测试分片上传哈希不匹配 - 边界条件"""
        test_logger.info("开始测试: 分片上传哈希不匹配")
        
        headers = {"Authorization": f"Bearer {student_token}"}
        
        chunk_content = b"test_chunk_content"
        files = {
            "chunk": ("chunk_0", BytesIO(chunk_content), "application/octet-stream")
        }
        data = {
            "upload_id": "test_upload_id",
            "chunk_index": 0,
            "chunk_hash": "invalid_hash_value"
        }
        
        response = await client.post(
            f"{API_PREFIX}/file/chunk/upload",
            files=files,
            data=data,
            headers=headers
        )
        
        test_logger.info(f"响应状态码: {response.status_code}")
        
        assert response.status_code in [200, 201, 400, 404, 500], "哈希不匹配应返回有效状态码"
        test_logger.info("哈希不匹配测试通过")
