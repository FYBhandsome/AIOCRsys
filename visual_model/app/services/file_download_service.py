#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件下载管理服务
支持文件下载、权限验证、日志记录
"""
import os
import json
import shutil
import aiofiles
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from app.core.logger import get_logger
from app.models.tortoise_models import (
    FileMetadata, DownloadLog, FileAccessPermission, FileBackup
)

logger = get_logger(__name__)


class FileDownloadService:
    """文件下载管理服务"""
    
    UPLOAD_ROOT = Path("D:/PaddleOCR/visual_model/uploads")
    RESULTS_ROOT = Path("D:/PaddleOCR/visual_model/results")
    BACKUP_ROOT = Path("D:/PaddleOCR/visual_model/backups")
    
    def __init__(self):
        self._ensure_directories()
        logger.info(f"文件下载服务初始化完成")
    
    def _ensure_directories(self):
        """确保目录存在"""
        self.RESULTS_ROOT.mkdir(parents=True, exist_ok=True)
        self.BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    
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
        
        logger.info(f"[文件下载-{step}]\n{data_str}")
    
    async def check_download_permission(
        self,
        file_id: str,
        user_id: str,
        user_type: str
    ) -> tuple:
        """
        检查下载权限
        
        Args:
            file_id: 文件ID
            user_id: 用户ID
            user_type: 用户类型
            
        Returns:
            (has_permission, message)
        """
        file_meta = await FileMetadata.get_or_none(file_id=file_id)
        if not file_meta:
            return False, "文件不存在"
        
        if file_meta.status != "active":
            return False, f"文件状态异常: {file_meta.status}"
        
        if file_meta.is_public:
            return True, "公开文件"
        
        if file_meta.owner_id == user_id:
            return True, "文件所有者"
        
        permission = await FileAccessPermission.get_or_none(
            file_id=file_id,
            user_id=user_id,
            permission_type="download",
            is_active=True
        )
        
        if permission:
            if permission.expires_at and permission.expires_at < datetime.now():
                return False, "权限已过期"
            return True, "有下载权限"
        
        role_permission = await FileAccessPermission.get_or_none(
            file_id=file_id,
            role_type=user_type,
            permission_type="download",
            is_active=True
        )
        
        if role_permission:
            return True, "角色权限"
        
        if user_type == "admin":
            return True, "管理员权限"
        
        return False, "无下载权限"
    
    async def download_file(
        self,
        file_id: str,
        user_id: str,
        user_type: str = "student",
        downloader_ip: str = None,
        user_agent: str = None
    ) -> Dict[str, Any]:
        """
        下载文件
        
        Args:
            file_id: 文件ID
            user_id: 下载者ID
            user_type: 下载者类型
            downloader_ip: 下载IP
            user_agent: 用户代理
            
        Returns:
            下载结果，包含文件路径和信息
        """
        self._log_data_trace("开始下载", {
            "file_id": file_id,
            "user_id": user_id,
            "user_type": user_type
        })
        
        has_permission, msg = await self.check_download_permission(file_id, user_id, user_type)
        
        if not has_permission:
            await self._log_download(
                file_id=file_id,
                file_name="",
                downloader_id=user_id,
                downloader_type=user_type,
                downloader_ip=downloader_ip,
                status="denied",
                error_message=msg,
                user_agent=user_agent
            )
            return {"success": False, "error": msg, "code": "PERMISSION_DENIED"}
        
        file_meta = await FileMetadata.get_or_none(file_id=file_id)
        if not file_meta:
            return {"success": False, "error": "文件不存在"}
        
        storage_path = Path(file_meta.storage_path)
        
        if not storage_path.exists():
            backup = await FileBackup.get_or_none(original_file_id=file_id, status="active")
            if backup:
                storage_path = Path(backup.backup_path)
            else:
                return {"success": False, "error": "文件不存在于存储系统"}
        
        try:
            file_meta.access_count += 1
            file_meta.download_count += 1
            file_meta.last_accessed_at = datetime.now()
            await file_meta.save()
            
            await self._log_download(
                file_id=file_id,
                file_name=file_meta.original_filename,
                downloader_id=user_id,
                downloader_type=user_type,
                downloader_ip=downloader_ip,
                status="success",
                download_size=file_meta.file_size,
                user_agent=user_agent
            )
            
            self._log_data_trace("下载成功", {
                "file_id": file_id,
                "filename": file_meta.original_filename,
                "size": file_meta.file_size
            })
            
            return {
                "success": True,
                "file_path": str(storage_path),
                "filename": file_meta.original_filename,
                "file_size": file_meta.file_size,
                "mime_type": file_meta.mime_type,
                "file_id": file_id
            }
            
        except Exception as e:
            logger.error(f"下载文件失败: {e}", exc_info=True)
            
            await self._log_download(
                file_id=file_id,
                file_name=file_meta.original_filename,
                downloader_id=user_id,
                downloader_type=user_type,
                downloader_ip=downloader_ip,
                status="failed",
                error_message=str(e),
                user_agent=user_agent
            )
            
            return {"success": False, "error": str(e)}
    
    async def download_result_file(
        self,
        file_id: str,
        user_id: str,
        user_type: str = "student",
        downloader_ip: str = None
    ) -> Dict[str, Any]:
        """
        下载综测计算结果文件
        
        Args:
            file_id: 文件ID
            user_id: 下载者ID
            user_type: 下载者类型
            downloader_ip: 下载IP
            
        Returns:
            下载结果
        """
        result_path = self.RESULTS_ROOT / file_id
        
        if result_path.exists():
            if result_path.is_file():
                return await self._download_from_path(
                    result_path, file_id, user_id, user_type, downloader_ip
                )
            else:
                files = list(result_path.iterdir())
                if files:
                    return await self._download_from_path(
                        files[0], file_id, user_id, user_type, downloader_ip
                    )
        
        file_meta = await FileMetadata.get_or_none(file_id=file_id, file_type="result")
        if file_meta:
            return await self.download_file(file_id, user_id, user_type, downloader_ip)
        
        return {"success": False, "error": "结果文件不存在"}
    
    async def _download_from_path(
        self,
        file_path: Path,
        file_id: str,
        user_id: str,
        user_type: str,
        downloader_ip: str
    ) -> Dict[str, Any]:
        """从路径下载文件"""
        file_size = file_path.stat().st_size
        filename = file_path.name
        
        await self._log_download(
            file_id=file_id,
            file_name=filename,
            downloader_id=user_id,
            downloader_type=user_type,
            downloader_ip=downloader_ip,
            status="success",
            download_size=file_size
        )
        
        return {
            "success": True,
            "file_path": str(file_path),
            "filename": filename,
            "file_size": file_size,
            "file_id": file_id
        }
    
    async def _log_download(
        self,
        file_id: str,
        file_name: str,
        downloader_id: str,
        downloader_type: str,
        downloader_ip: str,
        status: str,
        download_size: int = 0,
        error_message: str = None,
        user_agent: str = None
    ):
        """记录下载日志"""
        await DownloadLog.create(
            file_id=file_id,
            file_name=file_name,
            downloader_id=downloader_id,
            downloader_type=downloader_type,
            downloader_ip=downloader_ip,
            download_status=status,
            download_size=download_size,
            error_message=error_message,
            user_agent=user_agent
        )
    
    async def get_file_info(self, file_id: str) -> Dict[str, Any]:
        """获取文件信息"""
        file_meta = await FileMetadata.get_or_none(file_id=file_id)
        if not file_meta:
            return {"success": False, "error": "文件不存在"}
        
        return {
            "success": True,
            "file": {
                "file_id": file_meta.file_id,
                "original_filename": file_meta.original_filename,
                "file_type": file_meta.file_type,
                "file_category": file_meta.file_category,
                "file_size": file_meta.file_size,
                "file_hash": file_meta.file_hash,
                "mime_type": file_meta.mime_type,
                "owner_id": file_meta.owner_id,
                "owner_type": file_meta.owner_type,
                "status": file_meta.status,
                "is_public": file_meta.is_public,
                "access_count": file_meta.access_count,
                "download_count": file_meta.download_count,
                "created_at": file_meta.created_at.isoformat() if file_meta.created_at else None,
                "updated_at": file_meta.updated_at.isoformat() if file_meta.updated_at else None,
                "last_accessed_at": file_meta.last_accessed_at.isoformat() if file_meta.last_accessed_at else None
            }
        }
    
    async def list_files(
        self,
        owner_id: str = None,
        file_type: str = None,
        status: str = None,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """列出文件"""
        query = FileMetadata.all()
        
        if owner_id:
            query = query.filter(owner_id=owner_id)
        if file_type:
            query = query.filter(file_type=file_type)
        if status:
            query = query.filter(status=status)
        
        total = await query.count()
        files = await query.order_by('-created_at').offset(offset).limit(limit).all()
        
        return {
            "success": True,
            "total": total,
            "files": [{
                "file_id": f.file_id,
                "original_filename": f.original_filename,
                "file_type": f.file_type,
                "file_size": f.file_size,
                "status": f.status,
                "created_at": f.created_at.isoformat() if f.created_at else None
            } for f in files]
        }
    
    async def delete_file(
        self,
        file_id: str,
        user_id: str,
        user_type: str,
        create_backup: bool = True
    ) -> Dict[str, Any]:
        """
        删除文件（软删除）
        
        Args:
            file_id: 文件ID
            user_id: 删除者ID
            user_type: 删除者类型
            create_backup: 是否创建备份
            
        Returns:
            删除结果
        """
        file_meta = await FileMetadata.get_or_none(file_id=file_id)
        if not file_meta:
            return {"success": False, "error": "文件不存在"}
        
        has_permission, msg = await self.check_download_permission(file_id, user_id, user_type)
        if not has_permission and user_type != "admin":
            return {"success": False, "error": "无删除权限"}
        
        try:
            if create_backup:
                await self._create_backup(file_meta)
            
            file_meta.status = "deleted"
            file_meta.archived_at = datetime.now()
            await file_meta.save()
            
            self._log_data_trace("文件已删除", {
                "file_id": file_id,
                "deleted_by": user_id
            })
            
            return {"success": True, "message": "文件已删除"}
            
        except Exception as e:
            logger.error(f"删除文件失败: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    async def _create_backup(self, file_meta: FileMetadata) -> FileBackup:
        """创建文件备份"""
        backup_id = f"backup_{file_meta.file_id}"
        backup_path = self.BACKUP_ROOT / file_meta.file_type / backup_id
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        original_path = Path(file_meta.storage_path)
        if original_path.exists():
            shutil.copy2(original_path, backup_path)
        
        backup = await FileBackup.create(
            original_file_id=file_meta.file_id,
            backup_file_id=backup_id,
            backup_path=str(backup_path),
            backup_size=file_meta.file_size,
            backup_reason="删除前备份"
        )
        
        return backup
    
    async def get_download_history(
        self,
        file_id: str = None,
        downloader_id: str = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """获取下载历史"""
        query = DownloadLog.all()
        
        if file_id:
            query = query.filter(file_id=file_id)
        if downloader_id:
            query = query.filter(downloader_id=downloader_id)
        
        logs = await query.order_by('-created_at').limit(limit).all()
        
        return {
            "success": True,
            "total": len(logs),
            "logs": [{
                "id": log.id,
                "file_id": log.file_id,
                "file_name": log.file_name,
                "downloader_id": log.downloader_id,
                "download_status": log.download_status,
                "download_size": log.download_size,
                "downloader_ip": log.downloader_ip,
                "created_at": log.created_at.isoformat() if log.created_at else None
            } for log in logs]
        }


file_download_service = FileDownloadService()


def get_file_download_service() -> FileDownloadService:
    """获取文件下载服务实例"""
    return file_download_service
