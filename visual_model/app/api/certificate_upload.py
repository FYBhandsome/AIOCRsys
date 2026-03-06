#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
证书上传API路由
支持多张证书图片上传
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
import json
import uuid
from datetime import datetime

from app.services.certificate_storage_service import get_certificate_storage_service
from app.models.tortoise_models import Certificate, CertificateImage, CertificateBatch
from app.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/certificate", tags=["证书上传"])


@router.post("/upload")
async def upload_certificates(
    files: List[UploadFile] = File(..., description="证书图片文件列表"),
    student_id: str = Form(..., description="学号"),
    title: Optional[str] = Form(None, description="证书名称"),
    certificate_type: Optional[str] = Form(None, description="证书类型"),
    level: Optional[str] = Form(None, description="证书级别"),
    issuer: Optional[str] = Form(None, description="颁发机构"),
    issue_date: Optional[str] = Form(None, description="颁发日期"),
    category: Optional[str] = Form("C", description="证书类别"),
    sub_category: Optional[str] = Form(None, description="子类别"),
    score: Optional[float] = Form(0.0, description="加分分数"),
    upload_ip: Optional[str] = Form(None, description="上传IP"),
    upload_device: Optional[str] = Form(None, description="上传设备信息")
):
    """
    上传证书图片（支持多张）
    
    Args:
        files: 证书图片文件列表
        student_id: 学号
        title: 证书名称
        certificate_type: 证书类型
        level: 证书级别
        issuer: 颁发机构
        issue_date: 颁发日期
        category: 证书类别
        sub_category: 子类别
        score: 加分分数
        upload_ip: 上传IP
        upload_device: 上传设备信息
    
    Returns:
        上传结果
    """
    logger.info(f"开始上传证书: student_id={student_id}, file_count={len(files)}")
    
    if not student_id:
        raise HTTPException(status_code=400, detail="学号不能为空")
    
    if not files:
        raise HTTPException(status_code=400, detail="未提供任何文件")
    
    try:
        service = get_certificate_storage_service()
        
        certificate_info = {
            "title": title,
            "certificate_type": certificate_type,
            "level": level,
            "issuer": issuer,
            "issue_date": issue_date,
            "category": category,
            "sub_category": sub_category,
            "score": score
        }
        
        file_list = []
        for file in files:
            content = await file.read()
            file_list.append((file.filename, content))
        
        result = await service.upload_certificate_images(
            student_id=student_id,
            files=file_list,
            certificate_info=certificate_info,
            upload_ip=upload_ip,
            upload_device=upload_device
        )
        
        if result["success"]:
            return JSONResponse(content={
                "success": True,
                "message": f"上传完成: 成功{result['success_count']}个，失败{result['failed_count']}个",
                "certificate_id": result["certificate_id"],
                "batch_id": result["batch_id"],
                "images": result["images"]
            })
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "上传失败"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传证书失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.get("/student/{student_id}")
async def get_student_certificates(
    student_id: str,
    status: Optional[str] = Query(None, description="状态筛选"),
    category: Optional[str] = Query(None, description="证书类别筛选")
):
    """
    获取学生证书列表
    
    Args:
        student_id: 学号
        status: 状态筛选
        category: 证书类别筛选
    
    Returns:
        证书列表
    """
    service = get_certificate_storage_service()
    certificates = await service.get_student_certificates(
        student_id=student_id,
        status=status,
        category=category
    )
    
    return JSONResponse(content={
        "success": True,
        "student_id": student_id,
        "total": len(certificates),
        "certificates": certificates
    })


@router.get("/{certificate_id}")
async def get_certificate_detail(certificate_id: int):
    """
    获取证书详情
    
    Args:
        certificate_id: 证书ID
    
    Returns:
        证书详情
    """
    service = get_certificate_storage_service()
    result = await service.get_certificate_detail(certificate_id)
    
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result.get("error", "证书不存在"))
    
    return JSONResponse(content=result)


@router.delete("/{certificate_id}")
async def delete_certificate(
    certificate_id: int,
    deleted_by: Optional[str] = Query(None, description="删除者")
):
    """
    删除证书（软删除）
    
    Args:
        certificate_id: 证书ID
        deleted_by: 删除者
    
    Returns:
        删除结果
    """
    service = get_certificate_storage_service()
    result = await service.delete_certificate(certificate_id, deleted_by)
    
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result.get("error", "证书不存在"))
    
    return JSONResponse(content=result)


@router.put("/{certificate_id}")
async def update_certificate(
    certificate_id: int,
    title: Optional[str] = Form(None),
    certificate_type: Optional[str] = Form(None),
    level: Optional[str] = Form(None),
    issuer: Optional[str] = Form(None),
    issue_date: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    sub_category: Optional[str] = Form(None),
    score: Optional[float] = Form(None),
    updated_by: Optional[str] = Form(None)
):
    """
    更新证书信息
    
    Args:
        certificate_id: 证书ID
        其他字段: 可更新的证书信息
    
    Returns:
        更新结果
    """
    service = get_certificate_storage_service()
    
    info = {}
    if title is not None:
        info["title"] = title
    if certificate_type is not None:
        info["certificate_type"] = certificate_type
    if level is not None:
        info["level"] = level
    if issuer is not None:
        info["issuer"] = issuer
    if issue_date is not None:
        info["issue_date"] = issue_date
    if category is not None:
        info["category"] = category
    if sub_category is not None:
        info["sub_category"] = sub_category
    if score is not None:
        info["score"] = score
    
    result = await service.update_certificate_info(certificate_id, info, updated_by)
    
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result.get("error", "证书不存在"))
    
    return JSONResponse(content=result)


@router.get("/statistics/{student_id}")
async def get_certificate_statistics(student_id: str):
    """
    获取学生证书统计
    
    Args:
        student_id: 学号
    
    Returns:
        统计信息
    """
    service = get_certificate_storage_service()
    result = await service.get_certificate_statistics(student_id)
    
    return JSONResponse(content={
        "success": True,
        **result
    })


@router.post("/{certificate_id}/ocr/trigger")
async def trigger_certificate_ocr(certificate_id: int):
    """
    手动触发证书OCR处理
    
    Args:
        certificate_id: 证书ID
    
    Returns:
        处理结果
    """
    try:
        certificate = await Certificate.get_or_none(id=certificate_id)
        if not certificate:
            raise HTTPException(status_code=404, detail="证书不存在")
        
        from app.services.certificate_ocr_processing_service import get_certificate_ocr_processing_service
        ocr_processing_service = get_certificate_ocr_processing_service()
        
        result = await ocr_processing_service.process_certificate(certificate)
        
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"触发OCR处理失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"触发OCR处理失败: {str(e)}")


@router.post("/image/{image_id}/ocr/trigger")
async def trigger_image_ocr(image_id: int):
    """
    手动触发单张图片的OCR处理
    
    Args:
        image_id: 图片ID
    
    Returns:
        处理结果
    """
    try:
        image = await CertificateImage.get_or_none(id=image_id)
        if not image:
            raise HTTPException(status_code=404, detail="图片不存在")
        
        from app.services.certificate_ocr_processing_service import get_certificate_ocr_processing_service
        ocr_processing_service = get_certificate_ocr_processing_service()
        
        result = await ocr_processing_service.process_certificate_image(image)
        
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"触发图片OCR处理失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"触发图片OCR处理失败: {str(e)}")


@router.post("/batch-status")
async def batch_update_status(
    certificate_ids: List[int],
    status: str,
    reviewed_by: Optional[str] = None,
    review_comment: Optional[str] = None
):
    """
    批量更新证书状态
    
    Args:
        certificate_ids: 证书ID列表
        status: 新状态
        reviewed_by: 审核人
        review_comment: 审核意见
    
    Returns:
        更新结果
    """
    if status not in ["pending", "approved", "rejected", "cancelled"]:
        raise HTTPException(status_code=400, detail="无效的状态值")
    
    updated_count = 0
    for cert_id in certificate_ids:
        cert = await Certificate.get_or_none(id=cert_id)
        if cert:
            cert.status = status
            cert.reviewed_by = reviewed_by
            cert.reviewed_at = datetime.now()
            cert.review_comment = review_comment
            await cert.save()
            updated_count += 1
    
    return JSONResponse(content={
        "success": True,
        "updated_count": updated_count,
        "message": f"成功更新{updated_count}条记录"
    })
