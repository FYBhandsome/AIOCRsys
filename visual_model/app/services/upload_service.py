#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件上传服务

统一处理文件上传、验证、保存等操作。
"""

import os
import uuid
from pathlib import Path
from typing import Optional, List

from fastapi import UploadFile, HTTPException

from app.core.logger import logger
from app.core.utils import generate_task_id
from config import settings


class UploadService:
    """文件上传服务"""
    
    def __init__(self):
        """初始化上传服务"""
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        logger.info("文件上传服务已初始化")
    
    def validate_image_file(self, file: UploadFile) -> None:
        """验证图片文件
        
        Args:
            file: 上传的文件
            
        Raises:
            HTTPException: 文件验证失败
        """
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail=f"文件 {file.filename} 不是有效的图片格式"
            )
    
    def validate_image_files(self, files: List[UploadFile], max_count: int = 10) -> None:
        """批量验证图片文件
        
        Args:
            files: 上传的文件列表
            max_count: 最大文件数量
            
        Raises:
            HTTPException: 文件验证失败
        """
        if len(files) > max_count:
            raise HTTPException(
                status_code=400,
                detail=f"批量上传文件数量不能超过{max_count}个"
            )
        
        for file in files:
            self.validate_image_file(file)
    
    async def save_uploaded_file(self, file: UploadFile, 
                                 task_id: Optional[str] = None) -> tuple[str, str]:
        """保存上传的文件
        
        Args:
            file: 上传的文件
            task_id: 任务ID（可选，用于文件命名）
            
        Returns:
            (file_path, task_id) 元组
        """
        # 生成任务ID
        if task_id is None:
            task_id = generate_task_id()
        
        # 生成唯一文件名
        file_extension = Path(file.filename).suffix if file.filename else '.jpg'
        if task_id.startswith('cert_ocr_'):
            filename = f"{task_id}{file_extension}"
        else:
            filename = f"{task_id}_{file.filename}"
        
        # 完整文件路径
        file_path = self.upload_dir / filename
        
        # 读取并保存文件
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"文件已保存: {file_path}")
        return str(file_path), task_id
    
    def generate_cert_task_id(self) -> str:
        """生成证书OCR任务ID"""
        return f"cert_ocr_{uuid.uuid4().hex[:8]}"


# 全局单例
_upload_service_instance: Optional[UploadService] = None


def get_upload_service() -> UploadService:
    """获取文件上传服务单例"""
    global _upload_service_instance
    if _upload_service_instance is None:
        _upload_service_instance = UploadService()
    return _upload_service_instance

