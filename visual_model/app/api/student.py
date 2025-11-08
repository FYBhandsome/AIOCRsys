#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学生API路由
"""
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from typing import Dict, Any
import asyncio

from app.models.auth import TokenData
from app.models.upload import OCRResult
from app.core.auth_middleware import get_student_user
from app.services.ocr_service import get_ocr_service
from app.services.upload_service import get_upload_service, UploadService
from app.services.database_tortoise import DatabaseService
from app.services.dependencies import get_db_service
from app.services.rag_client import get_rag_client
from app.core.executor_manager import get_executor
from app.core.logger import logger
from config import settings


router = APIRouter(prefix="/student", tags=["学生"])


@router.post("/certificate/upload", response_model=OCRResult)
async def upload_certificate(
    file: UploadFile = File(..., description="获奖证书图片"),
    current_user: TokenData = Depends(get_student_user),
    db_service: DatabaseService = Depends(get_db_service),
    upload_service: UploadService = Depends(get_upload_service)
):
    """学生上传获奖证书
    
    上传证书图片并进行OCR识别，自动计算综测加分
    """
    try:
        # 验证文件
        upload_service.validate_image_file(file)
        
        # 保存文件
        file_path, file_id = await upload_service.save_uploaded_file(file)
        
        # 读取文件内容
        file.file.seek(0)
        file_content = await file.read()
        file_size = len(file_content)
        
        # 创建文件记录（关联学生）
        await db_service.create_file(
            id=file_id,
            filename=file.filename,
            file_type=file.content_type,
            file_size=file_size,
            file_path=file_path,
            student_id=current_user.user_id
        )
        
        # OCR识别
        ocr_service = get_ocr_service()
        executor = get_executor()
        
        recognition_results = await asyncio.get_event_loop().run_in_executor(
            executor,
            ocr_service.recognize_text,
            file_path,
            None
        )
        
        certificate_info = ocr_service.extract_certificate_info(
            image_path=file_path,
            ocr_results=recognition_results
        )
        
        # 如果启用RAG，计算加分
        if settings.RAG_ENABLED and certificate_info.get("raw_text"):
            try:
                rag_client = get_rag_client()
                score_result = await rag_client.calculate_score(
                    certificate_text=certificate_info["raw_text"],
                    student_info={
                        "student_id": current_user.user_id,
                        "username": current_user.username
                    }
                )
                certificate_info["rag_score"] = score_result
                logger.info(f"RAG计算加分: {score_result.get('score', 0)}分")
            except Exception as e:
                logger.warning(f"RAG加分计算失败: {e}")
                certificate_info["rag_score"] = None
        
        logger.info(f"学生 {current_user.username} 上传证书成功: {file_id}")
        
        return OCRResult(
            file_id=file_id,
            filename=file.filename,
            file_size=file_size,
            recognition_results=recognition_results,
            certificate_info=certificate_info
        )
    
    except Exception as e:
        logger.error(f"上传证书失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"上传证书失败: {str(e)}")


@router.get("/scores/summary")
async def get_score_summary(
    current_user: TokenData = Depends(get_student_user)
) -> Dict[str, Any]:
    """获取学生综合成绩摘要
    
    返回学生的综测总分、各项得分等信息
    """
    # TODO: 从数据库查询实际成绩
    return {
        "student_id": current_user.user_id,
        "username": current_user.username,
        "total_score": 85.5,
        "rank": 12,
        "total_students": 120,
        "breakdown": {
            "academic": 75.0,      # 学业成绩
            "moral": 8.5,          # 德育分
            "physical": 10.0,      # 体育分
            "certificate": 12.0    # 获奖证书加分
        },
        "certificates": [
            {
                "id": "cert001",
                "name": "国家奖学金",
                "category": "国家级",
                "score": 10.0,
                "date": "2024-12-01"
            }
        ]
    }


@router.get("/scores/detail")
async def get_score_detail(
    current_user: TokenData = Depends(get_student_user)
) -> Dict[str, Any]:
    """获取学生各项详细成绩"""
    return {
        "student_id": current_user.user_id,
        "username": current_user.username,
        "academic_scores": [
            {"course": "高等数学", "score": 92, "credit": 4},
            {"course": "大学英语", "score": 88, "credit": 3},
            {"course": "计算机基础", "score": 95, "credit": 3}
        ],
        "moral_activities": [
            {"activity": "志愿服务", "hours": 20, "score": 5.0},
            {"activity": "社团活动", "hours": 10, "score": 3.5}
        ],
        "certificates": []
    }


@router.get("/uploads")
async def get_upload_history(
    current_user: TokenData = Depends(get_student_user),
    db_service: DatabaseService = Depends(get_db_service)
):
    """获取学生上传历史记录"""
    try:
        # 从数据库查询该学生的所有上传文件
        files = await db_service.get_files(student_id=current_user.user_id)
        
        # 格式化返回数据
        upload_history = []
        for file in files:
            upload_history.append({
                "id": file.id,
                "filename": file.filename,
                "type": "certificate",  # 根据文件类型区分
                "status": "completed",  # 可以根据处理状态设置
                "score": None,  # 从RAG结果或数据库获取加分
                "upload_time": file.created_at.strftime("%Y-%m-%d %H:%M:%S") if file.created_at else None,
                "file_size": file.file_size,
                "remark": None
            })
        
        logger.info(f"学生 {current_user.username} 查询上传历史，共 {len(upload_history)} 条记录")
        return upload_history
    
    except Exception as e:
        logger.error(f"获取上传历史失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取上传历史失败: {str(e)}")


@router.get("/certificates")
async def list_my_certificates(
    current_user: TokenData = Depends(get_student_user),
    db_service: DatabaseService = Depends(get_db_service)
):
    """查看我的获奖证书列表"""
    # TODO: 从数据库查询学生的证书记录
    return {
        "total": 0,
        "certificates": []
    }

