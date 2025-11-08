#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获奖证书OCR识别API路由

处理获奖证书图片上传和OCR识别请求（同步处理版本）。
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends
from fastapi.responses import JSONResponse
from typing import Optional, List
from pathlib import Path
import asyncio

from app.core.logger import logger
from app.core.executor_manager import get_executor
from app.business import CertificateOCRService
from app.models.upload import OCRResult
from app.services.upload_service import get_upload_service, UploadService
from config import settings


router = APIRouter()
certificate_ocr_service = CertificateOCRService()


async def _process_single_certificate(
    file: UploadFile,
    upload_service: UploadService
) -> dict:
    """处理单个证书文件（内部辅助函数）
    
    Args:
        file: 上传的文件
        upload_service: 上传服务
        
    Returns:
        处理结果字典
    """
    # 生成任务ID
    task_id = upload_service.generate_cert_task_id()
    
    # 保存文件
    file_path, _ = await upload_service.save_uploaded_file(file, task_id)
    
    # 在线程池中同步处理OCR识别（避免阻塞事件循环）
    executor = get_executor()
    result = await asyncio.get_event_loop().run_in_executor(
        executor,
        certificate_ocr_service.process_certificate_image,
        file_path
    )
    
    return {
        "file_id": task_id,
        "filename": file.filename,
        "success": result["success"],
        "message": "获奖证书OCR识别完成" if result["success"] else f"识别失败: {result.get('error', '未知错误')}",
        "result": result
    }


@router.post("/certificate/ocr")
async def upload_certificate_for_ocr(
    file: UploadFile = File(..., description="获奖证书图片文件"),
    student_id: Optional[str] = Form(None, description="学生ID"),
    class_id: Optional[str] = Form(None, description="班级ID"),
    upload_service: UploadService = Depends(get_upload_service)
):
    """上传获奖证书图片进行OCR识别（同步处理）
    
    Args:
        file: 上传的获奖证书图片文件
        student_id: 学生ID（可选）
        class_id: 班级ID（可选）
        upload_service: 上传服务
        
    Returns:
        直接返回OCR识别结果
    """
    try:
        # 验证文件类型
        upload_service.validate_image_file(file)
        
        # 处理证书
        result_data = await _process_single_certificate(file, upload_service)
        
        return {
            "file_id": result_data["file_id"],
            "filename": result_data["filename"],
            "success": result_data["success"],
            "message": result_data["message"],
            "result": result_data["result"]
        }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"处理获奖证书OCR识别请求失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"处理请求失败: {str(e)}")


@router.post("/certificate/ocr/batch")
async def upload_certificates_for_ocr_batch(
    files: List[UploadFile] = File(..., description="获奖证书图片文件列表"),
    student_id: Optional[str] = Form(None, description="学生ID"),
    class_id: Optional[str] = Form(None, description="班级ID"),
    upload_service: UploadService = Depends(get_upload_service)
):
    """批量上传获奖证书图片进行OCR识别
    
    Args:
        files: 上传的获奖证书图片文件列表
        student_id: 学生ID（可选）
        class_id: 班级ID（可选）
        upload_service: 上传服务
        
    Returns:
        批量任务响应，包含所有任务ID和状态
    """
    try:
        # 验证文件
        upload_service.validate_image_files(files, max_count=10)
        
        # 批量处理
        results = []
        for file in files:
            try:
                result_data = await _process_single_certificate(file, upload_service)
                results.append(result_data)
            except Exception as e:
                logger.error(f"处理文件 {file.filename} 失败: {e}")
                results.append({
                    "file_id": upload_service.generate_cert_task_id(),
                    "filename": file.filename,
                    "success": False,
                    "message": f"处理失败: {str(e)}",
                    "result": {"success": False, "error": str(e)}
                })
        
        return {
            "success": True,
            "message": f"批量处理完成，共处理 {len(files)} 个文件",
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量处理获奖证书OCR识别请求失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"批量处理请求失败: {str(e)}")




@router.get("/certificate/ocr/result/{task_id}")
async def get_certificate_ocr_result(task_id: str):
    """获取获奖证书OCR识别结果
    
    Args:
        task_id: 任务ID
        
    Returns:
        OCR识别结果
    """
    try:
        result_dir = Path(settings.RESULT_DIR)
        
        # 查找结果文件
        result_files = list(result_dir.glob(f"*{task_id}*ocr_result.json"))
        
        if not result_files:
            raise HTTPException(status_code=404, detail="未找到OCR识别结果")
        
        # 读取结果文件
        import json
        with open(result_files[0], 'r', encoding='utf-8') as f:
            result_data = json.load(f)
        
        return JSONResponse(content=result_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取识别结果失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取识别结果失败: {str(e)}")
