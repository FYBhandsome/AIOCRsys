#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件上传管理服务
支持多文件上传、分片上传、断点续传
"""
import os
import json
import hashlib
import uuid
import shutil
import aiofiles
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import logging

from app.core.logger import get_logger
from app.models.tortoise_models import (
    FileMetadata, FileChunk, DownloadLog, FileAccessPermission, FileBackup
)

logger = get_logger(__name__)


class FileUploadService:
    """文件上传管理服务"""
    
    UPLOAD_ROOT = Path("D:/PaddleOCR/visual_model/uploads")
    RESULTS_ROOT = Path("D:/PaddleOCR/visual_model/results")
    BACKUP_ROOT = Path("D:/PaddleOCR/visual_model/backups")
    
    CHUNK_SIZE = 5 * 1024 * 1024  # 5MB per chunk
    MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
    
    FILE_CATEGORIES = {
        'transcript': 'transcripts',
        'photo': 'photos',
        'certificate': 'certificates',
        'template': 'templates',
        'result': 'results',
        'other': 'others'
    }
    
    ALLOWED_EXTENSIONS = {
        'transcript': ['.xlsx', '.xls', '.csv', '.pdf'],
        'photo': ['.jpg', '.jpeg', '.png', '.gif', '.bmp'],
        'certificate': ['.jpg', '.jpeg', '.png', '.pdf'],
        'template': ['.xlsx', '.xls', '.doc', '.docx'],
        'result': ['.xlsx', '.xls', '.csv', '.pdf'],
        'other': []
    }
    
    def __init__(self):
        self._ensure_directories()
        logger.info(f"文件上传服务初始化完成, 根目录: {self.UPLOAD_ROOT}")
    
    def _ensure_directories(self):
        """确保所有必要目录存在"""
        for category in self.FILE_CATEGORIES.values():
            dir_path = self.UPLOAD_ROOT / category
            dir_path.mkdir(parents=True, exist_ok=True)
        
        self.RESULTS_ROOT.mkdir(parents=True, exist_ok=True)
        self.BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
        
        chunks_dir = self.UPLOAD_ROOT / "chunks"
        chunks_dir.mkdir(parents=True, exist_ok=True)
        
        temp_dir = self.UPLOAD_ROOT / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
    
    def _log_data_trace(self, step: str, data: Any):
        """数据追踪日志"""
        if isinstance(data, (dict, list)):
            try:
                data_str = json.dumps(data, ensure_ascii=False, indent=2)
                if len(data_str) > 1000:
                    data_str = data_str[:1000] + "..."
            except Exception:
                data_str = str(data)[:1000]
        else:
            data_str = str(data)[:1000]
        
        logger.info(f"[文件上传-{step}]\n{data_str}")
    
    def _generate_file_id(self, owner_id: str, original_filename: str) -> str:
        """
        生成唯一文件标识
        格式: 学号/工号_时间戳_文件说明
        时间戳精确到毫秒: YYYYMMDDHHMMSSmmm
        """
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d%H%M%S") + f"{now.microsecond // 1000:03d}"
        
        name_part = Path(original_filename).stem
        name_part = "".join(c for c in name_part if c.isalnum() or c in '_-')[:30]
        
        file_id = f"{owner_id}_{timestamp}_{name_part}"
        
        self._log_data_trace("生成文件ID", {
            "owner_id": owner_id,
            "timestamp": timestamp,
            "file_id": file_id
        })
        
        return file_id
    
    def _get_storage_path(self, file_type: str, owner_id: str, filename: str) -> Tuple[Path, str]:
        """获取文件存储路径"""
        category_dir = self.FILE_CATEGORIES.get(file_type, 'others')
        
        owner_dir = self.UPLOAD_ROOT / category_dir / owner_id
        owner_dir.mkdir(parents=True, exist_ok=True)
        
        ext = Path(filename).suffix
        stored_filename = f"{uuid.uuid4().hex}{ext}"
        
        storage_path = owner_dir / stored_filename
        
        return storage_path, str(storage_path.relative_to(self.UPLOAD_ROOT))
    
    def _calculate_hash(self, file_content: bytes) -> str:
        """计算文件MD5哈希"""
        return hashlib.md5(file_content).hexdigest()
    
    def _validate_file(self, filename: str, file_size: int, file_type: str) -> Tuple[bool, str]:
        """验证文件"""
        ext = Path(filename).suffix.lower()
        
        allowed = self.ALLOWED_EXTENSIONS.get(file_type, [])
        if allowed and ext not in allowed:
            return False, f"不支持的文件格式: {ext}，允许的格式: {allowed}"
        
        if file_size > self.MAX_FILE_SIZE:
            return False, f"文件大小超过限制: {file_size} > {self.MAX_FILE_SIZE}"
        
        return True, "验证通过"
    
    async def upload_file(
        self,
        file_content: bytes,
        original_filename: str,
        file_type: str,
        owner_id: str,
        owner_type: str = "student",
        metadata: Dict[str, Any] = None,
        is_public: bool = False,
        is_encrypted: bool = False
    ) -> Dict[str, Any]:
        """
        上传单个文件
        
        Args:
            file_content: 文件内容
            original_filename: 原始文件名
            file_type: 文件类型
            owner_id: 所有者ID
            owner_type: 所有者类型
            metadata: 扩展元数据
            is_public: 是否公开
            is_encrypted: 是否加密
            
        Returns:
            上传结果
        """
        self._log_data_trace("开始上传文件", {
            "filename": original_filename,
            "file_type": file_type,
            "owner_id": owner_id,
            "size": len(file_content)
        })
        
        is_valid, msg = self._validate_file(original_filename, len(file_content), file_type)
        if not is_valid:
            return {"success": False, "error": msg}
        
        try:
            file_id = self._generate_file_id(owner_id, original_filename)
            storage_path, relative_path = self._get_storage_path(file_type, owner_id, original_filename)
            file_hash = self._calculate_hash(file_content)
            
            existing = await FileMetadata.get_or_none(file_hash=file_hash, status="active")
            if existing:
                self._log_data_trace("文件已存在(哈希匹配)", {
                    "existing_file_id": existing.file_id,
                    "new_file_id": file_id
                })
            
            async with aiofiles.open(storage_path, 'wb') as f:
                await f.write(file_content)
            
            mime_type = self._get_mime_type(original_filename)
            
            file_meta = await FileMetadata.create(
                file_id=file_id,
                original_filename=original_filename,
                stored_filename=storage_path.name,
                file_type=file_type,
                file_category=self.FILE_CATEGORIES.get(file_type, 'others'),
                mime_type=mime_type,
                file_extension=Path(original_filename).suffix.lower(),
                file_size=len(file_content),
                file_hash=file_hash,
                storage_path=str(storage_path),
                storage_directory=str(storage_path.parent),
                owner_id=owner_id,
                owner_type=owner_type,
                is_public=is_public,
                is_encrypted=is_encrypted,
                metadata=metadata
            )
            
            await self._grant_default_permissions(file_id, owner_id, owner_type)
            
            self._log_data_trace("文件上传成功", {
                "file_id": file_id,
                "storage_path": str(storage_path)
            })
            
            return {
                "success": True,
                "file_id": file_id,
                "original_filename": original_filename,
                "file_size": len(file_content),
                "file_hash": file_hash,
                "storage_path": str(storage_path),
                "created_at": file_meta.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"文件上传失败: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    async def upload_multiple_files(
        self,
        files: List[Tuple[str, bytes]],
        file_type: str,
        owner_id: str,
        owner_type: str = "student",
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        批量上传文件
        
        Args:
            files: 文件列表 [(filename, content), ...]
            file_type: 文件类型
            owner_id: 所有者ID
            owner_type: 所有者类型
            metadata: 扩展元数据
            
        Returns:
            批量上传结果
        """
        batch_id = str(uuid.uuid4())
        
        self._log_data_trace("开始批量上传", {
            "batch_id": batch_id,
            "file_count": len(files),
            "owner_id": owner_id
        })
        
        results = []
        success_count = 0
        failed_count = 0
        
        for filename, content in files:
            result = await self.upload_file(
                file_content=content,
                original_filename=filename,
                file_type=file_type,
                owner_id=owner_id,
                owner_type=owner_type,
                metadata=metadata
            )
            
            if result["success"]:
                success_count += 1
                await FileMetadata.filter(file_id=result["file_id"]).update(
                    upload_batch_id=batch_id
                )
            else:
                failed_count += 1
            
            results.append({
                "filename": filename,
                **result
            })
        
        return {
            "success": True,
            "batch_id": batch_id,
            "total": len(files),
            "success_count": success_count,
            "failed_count": failed_count,
            "results": results
        }
    
    async def init_chunk_upload(
        self,
        filename: str,
        file_size: int,
        file_type: str,
        owner_id: str,
        chunk_size: int = None
    ) -> Dict[str, Any]:
        """
        初始化分片上传
        
        Args:
            filename: 文件名
            file_size: 文件总大小
            file_type: 文件类型
            owner_id: 所有者ID
            chunk_size: 分片大小
            
        Returns:
            初始化结果，包含上传ID和分片信息
        """
        is_valid, msg = self._validate_file(filename, file_size, file_type)
        if not is_valid:
            return {"success": False, "error": msg}
        
        file_id = self._generate_file_id(owner_id, filename)
        chunk_size = chunk_size or self.CHUNK_SIZE
        chunk_count = (file_size + chunk_size - 1) // chunk_size
        
        storage_path, relative_path = self._get_storage_path(file_type, owner_id, filename)
        
        file_meta = await FileMetadata.create(
            file_id=file_id,
            original_filename=filename,
            stored_filename=storage_path.name,
            file_type=file_type,
            file_category=self.FILE_CATEGORIES.get(file_type, 'others'),
            file_extension=Path(filename).suffix.lower(),
            file_size=file_size,
            storage_path=str(storage_path),
            storage_directory=str(storage_path.parent),
            owner_id=owner_id,
            chunk_upload=True,
            chunk_count=chunk_count,
            chunk_uploaded=0,
            status="pending"
        )
        
        chunks_dir = self.UPLOAD_ROOT / "chunks" / file_id
        chunks_dir.mkdir(parents=True, exist_ok=True)
        
        for i in range(chunk_count):
            await FileChunk.create(
                file_id=file_id,
                chunk_index=i,
                chunk_size=min(chunk_size, file_size - i * chunk_size),
                status="pending"
            )
        
        self._log_data_trace("初始化分片上传", {
            "file_id": file_id,
            "chunk_count": chunk_count,
            "chunk_size": chunk_size
        })
        
        return {
            "success": True,
            "file_id": file_id,
            "chunk_count": chunk_count,
            "chunk_size": chunk_size,
            "chunk_urls": [f"/v1/file/chunk/{file_id}/{i}" for i in range(chunk_count)]
        }
    
    async def upload_chunk(
        self,
        file_id: str,
        chunk_index: int,
        chunk_content: bytes,
        upload_ip: str = None
    ) -> Dict[str, Any]:
        """
        上传文件分片
        
        Args:
            file_id: 文件ID
            chunk_index: 分片序号
            chunk_content: 分片内容
            upload_ip: 上传IP
            
        Returns:
            上传结果
        """
        file_meta = await FileMetadata.get_or_none(file_id=file_id)
        if not file_meta:
            return {"success": False, "error": "文件不存在"}
        
        if not file_meta.chunk_upload:
            return {"success": False, "error": "该文件不是分片上传模式"}
        
        chunk = await FileChunk.get_or_none(file_id=file_id, chunk_index=chunk_index)
        if not chunk:
            return {"success": False, "error": "分片不存在"}
        
        if chunk.status == "uploaded":
            return {"success": True, "message": "分片已上传", "chunk_index": chunk_index}
        
        try:
            chunk_hash = self._calculate_hash(chunk_content)
            
            chunk_path = self.UPLOAD_ROOT / "chunks" / file_id / f"chunk_{chunk_index}"
            async with aiofiles.open(chunk_path, 'wb') as f:
                await f.write(chunk_content)
            
            chunk.chunk_hash = chunk_hash
            chunk.chunk_path = str(chunk_path)
            chunk.status = "uploaded"
            chunk.upload_ip = upload_ip
            chunk.uploaded_at = datetime.now()
            await chunk.save()
            
            file_meta.chunk_uploaded = await FileChunk.filter(
                file_id=file_id, status="uploaded"
            ).count()
            await file_meta.save()
            
            self._log_data_trace("分片上传成功", {
                "file_id": file_id,
                "chunk_index": chunk_index,
                "progress": f"{file_meta.chunk_uploaded}/{file_meta.chunk_count}"
            })
            
            return {
                "success": True,
                "chunk_index": chunk_index,
                "chunk_hash": chunk_hash,
                "uploaded_count": file_meta.chunk_uploaded,
                "total_count": file_meta.chunk_count,
                "is_complete": file_meta.chunk_uploaded == file_meta.chunk_count
            }
            
        except Exception as e:
            logger.error(f"分片上传失败: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    async def complete_chunk_upload(self, file_id: str) -> Dict[str, Any]:
        """
        完成分片上传，合并文件
        
        Args:
            file_id: 文件ID
            
        Returns:
            合并结果
        """
        file_meta = await FileMetadata.get_or_none(file_id=file_id)
        if not file_meta:
            return {"success": False, "error": "文件不存在"}
        
        if file_meta.chunk_uploaded != file_meta.chunk_count:
            return {
                "success": False, 
                "error": f"分片未全部上传: {file_meta.chunk_uploaded}/{file_meta.chunk_count}"
            }
        
        try:
            storage_path = Path(file_meta.storage_path)
            storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_hash = hashlib.md5()
            
            async with aiofiles.open(storage_path, 'wb') as output_file:
                for i in range(file_meta.chunk_count):
                    chunk = await FileChunk.get(file_id=file_id, chunk_index=i)
                    chunk_path = Path(chunk.chunk_path)
                    
                    async with aiofiles.open(chunk_path, 'rb') as chunk_file:
                        content = await chunk_file.read()
                        await output_file.write(content)
                        file_hash.update(content)
                    
                    chunk.status = "merged"
                    await chunk.save()
            
            file_meta.file_hash = file_hash.hexdigest()
            file_meta.status = "active"
            await file_meta.save()
            
            chunks_dir = self.UPLOAD_ROOT / "chunks" / file_id
            shutil.rmtree(chunks_dir, ignore_errors=True)
            
            await self._grant_default_permissions(file_id, file_meta.owner_id, file_meta.owner_type)
            
            self._log_data_trace("分片合并完成", {
                "file_id": file_id,
                "file_hash": file_meta.file_hash,
                "storage_path": str(storage_path)
            })
            
            return {
                "success": True,
                "file_id": file_id,
                "file_hash": file_meta.file_hash,
                "storage_path": str(storage_path),
                "file_size": file_meta.file_size
            }
            
        except Exception as e:
            logger.error(f"合并分片失败: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    async def get_upload_progress(self, file_id: str) -> Dict[str, Any]:
        """获取上传进度"""
        file_meta = await FileMetadata.get_or_none(file_id=file_id)
        if not file_meta:
            return {"success": False, "error": "文件不存在"}
        
        if not file_meta.chunk_upload:
            return {
                "success": True,
                "file_id": file_id,
                "is_chunk_upload": False,
                "status": file_meta.status
            }
        
        chunks = await FileChunk.filter(file_id=file_id).all()
        chunk_status = [{
            "index": c.chunk_index,
            "status": c.status,
            "size": c.chunk_size
        } for c in chunks]
        
        return {
            "success": True,
            "file_id": file_id,
            "is_chunk_upload": True,
            "total_chunks": file_meta.chunk_count,
            "uploaded_chunks": file_meta.chunk_uploaded,
            "progress": file_meta.chunk_uploaded / file_meta.chunk_count if file_meta.chunk_count > 0 else 0,
            "status": file_meta.status,
            "chunks": chunk_status
        }
    
    def _get_mime_type(self, filename: str) -> str:
        """获取MIME类型"""
        ext = Path(filename).suffix.lower()
        mime_types = {
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.xls': 'application/vnd.ms-excel',
            '.csv': 'text/csv',
            '.pdf': 'application/pdf',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        return mime_types.get(ext, 'application/octet-stream')
    
    async def _grant_default_permissions(self, file_id: str, owner_id: str, owner_type: str):
        """授予默认权限"""
        permissions = ['read', 'write', 'delete', 'download']
        for perm in permissions:
            await FileAccessPermission.get_or_create(
                file_id=file_id,
                user_id=owner_id,
                permission_type=perm,
                defaults={
                    'role_type': owner_type,
                    'granted_by': 'system'
                }
            )


file_upload_service = FileUploadService()


def get_file_upload_service() -> FileUploadService:
    """获取文件上传服务实例"""
    return file_upload_service
