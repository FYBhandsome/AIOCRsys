#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件上传API路由

提供文件上传、OCR识别等功能。
"""

from fastapi import APIRouter, Depends, File, UploadFile
import os
import asyncio
import time
from functools import partial

from app.core.exceptions import FileUploadException
from app.core.executor_manager import get_executor
from app.models.upload import (
    OCRResult,
    FileDeleteResponse
)
from app.services.dependencies import get_db_service
from app.services.database_tortoise import DatabaseService
from app.services.upload_service import get_upload_service, UploadService
from app.services.ocr_service import get_ocr_service
from app.core.logger import logger
from config import settings

# ============================================================================
# API路由定义
# ============================================================================

router = APIRouter(prefix="/upload", tags=["文件上传"])


@router.post("/certificate", response_model=OCRResult)
async def upload_certificate(
    file: UploadFile = File(..., description="证书图片文件"),
    db_service: DatabaseService = Depends(get_db_service),
    upload_service: UploadService = Depends(get_upload_service)
):
    """上传证书图片进行OCR识别，直接返回识别结果
    
    Args:
        file: 上传的图片文件
        db_service: 数据库服务
        upload_service: 上传服务
        
    Returns:
        OCRResult: OCR识别结果
    """
    try:
        # 验证文件类型
        upload_service.validate_image_file(file)
        
        # 保存文件并生成文件ID
        file_path, file_id = await upload_service.save_uploaded_file(file)
        
        # 读取文件内容用于记录
        file.file.seek(0)  # 重置文件指针
        file_content = await file.read()
        file_size = len(file_content)
        
        # 创建文件记录
        await db_service.create_file(
            id=file_id,
            filename=file.filename,
            file_type=file.content_type,
            file_size=file_size,
            file_path=file_path
        )
        
        # 在线程池中执行OCR识别（避免阻塞事件循环）
        ocr_service = get_ocr_service()
        executor = get_executor()
        
        # 识别与信息提取
        t0 = time.perf_counter()
        recognition_results = await asyncio.get_event_loop().run_in_executor(
            executor,
            ocr_service.recognize_text,
            file_path,
            None  # 使用配置的阈值
        )
        t1 = time.perf_counter()
        
        certificate_info = ocr_service.extract_certificate_info(
            image_path=file_path,
            ocr_results=recognition_results
        )
        t2 = time.perf_counter()
        
        logger.info(f"OCR完成: file_id={file_id}, 耗时={t2-t0:.2f}s, "
                   f"识别数={len(recognition_results)}, avg_conf={certificate_info.get('confidence', 0):.3f}")
        
        return OCRResult(
            file_id=file_id,
            filename=file.filename,
            file_size=file_size,
            recognition_results=recognition_results,
            certificate_info=certificate_info
        )
    
    except FileUploadException:
        raise
    except Exception as e:
        logger.error(f"上传证书图片失败: {e}", exc_info=True)
        raise FileUploadException(f"上传证书图片失败: {str(e)}")


@router.delete("/file/{file_id}", response_model=FileDeleteResponse)
async def delete_file(
    file_id: str,
    db_service: DatabaseService = Depends(get_db_service)
):
    """删除文件及其关联的数据
    
    该接口会删除：
    1. 文件记录
    2. 物理文件（如果存在）
    
    Args:
        file_id: 文件ID
        
    Returns:
        FileDeleteResponse: 删除结果
    """
    try:
        # 获取文件记录
        file = await db_service.get_file(file_id)
        if not file:
            raise FileUploadException(f"文件不存在: {file_id}")
        
        file_path = file.file_path
        
        # 删除文件记录
        success = await db_service.delete_file(file_id)
        
        if not success:
            raise FileUploadException(f"删除文件记录失败: {file_id}")
        
        # 删除物理文件
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"删除物理文件成功: {file_path}")
            except Exception as e:
                logger.warning(f"删除物理文件失败: {file_path}, 错误: {e}")
        
        return FileDeleteResponse(
            file_id=file_id,
            message="文件删除成功"
        )
    
    except FileUploadException:
        raise
    except Exception as e:
        logger.error(f"删除文件失败: {e}", exc_info=True)
        raise FileUploadException(f"删除文件失败: {str(e)}")
