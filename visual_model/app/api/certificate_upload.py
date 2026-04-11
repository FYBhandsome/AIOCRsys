#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
证书上传API路由
支持多张证书图片上传，OCR识别，RAG检索和加分计算
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
import json
import uuid
import asyncio
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
    
    完整流程:
    1. 上传证书图片
    2. OCR识别提取文字
    3. RAG检索相关规则
    4. AI计算加分
    
    Returns:
        上传结果，包含OCR识别结果、RAG检索信息、加分结果
    """
    logger.info(f"[证书上传] 开始处理: student_id={student_id}, file_count={len(files)}")
    logger.info(f"[证书上传] 文件列表: {[f.filename for f in files]}")
    
    if not student_id:
        logger.warning(f"[证书上传] 学号为空")
        raise HTTPException(status_code=400, detail="学号不能为空")
    
    if not files:
        logger.warning(f"[证书上传] 未提供任何文件")
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
            logger.info(f"[证书上传] 读取文件: {file.filename}, size={len(content)}")
        
        result = await service.upload_certificate_images(
            student_id=student_id,
            files=file_list,
            certificate_info=certificate_info,
            upload_ip=upload_ip,
            upload_device=upload_device
        )
        
        if not result["success"]:
            logger.error(f"[证书上传] 存储失败: {result.get('error')}")
            raise HTTPException(status_code=500, detail=result.get("error", "上传失败"))
        
        certificate_id = result["certificate_id"]
        logger.info(f"[证书上传] 证书存储成功: certificate_id={certificate_id}")
        
        ocr_results = []
        rag_results = []
        score_results = []
        
        try:
            from app.services.ocr_service import get_ocr_service
            from app.services.certificate_service import get_certificate_service
            from app.core.executor import get_executor
            
            ocr_service = get_ocr_service()
            cert_service = get_certificate_service()
            executor = get_executor()
            
            for i, (filename, content) in enumerate(file_list):
                logger.info(f"[证书上传] 开始OCR识别: {filename}")
                
                import tempfile
                import os
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp:
                    tmp.write(content)
                    tmp_path = tmp.name
                
                try:
                    recognition_results = await asyncio.get_event_loop().run_in_executor(
                        executor,
                        ocr_service.recognize_text,
                        tmp_path,
                        None
                    )
                    
                    certificate_info_extracted = ocr_service.extract_certificate_info(
                        image_path=tmp_path,
                        ocr_results=recognition_results
                    )
                    
                    cert_text = certificate_info_extracted.get("raw_text", "")
                    if not cert_text:
                        cert_text = " ".join([item.get("text", "") for item in recognition_results])

                    logger.info(f"[证书上传] OCR识别完成: {filename}, text_length={len(cert_text)}")

                    ocr_result = {
                        "filename": filename,
                        "recognition_results": recognition_results,
                        "certificate_info": certificate_info_extracted,
                        "raw_text": cert_text
                    }
                    ocr_results.append(ocr_result)

                    logger.info(f"[证书上传] 开始RAG检索和加分计算: {filename}")

                    classification_result = await cert_service.classify_and_calculate_score(
                        certificate_text=cert_text,
                        certificate_info=certificate_info_extracted,
                        student_info={"student_id": student_id}
                    )
                    
                    logger.info(f"[证书上传] 加分计算完成: category={classification_result.get('category')}, score={classification_result.get('score')}")
                    
                    rag_result = {
                        "filename": filename,
                        "used_rag": classification_result.get("rag_used", False),
                        "retrieved_rules": classification_result.get("rag_rules", []),
                        "confidence": classification_result.get("confidence", 0.0),
                        "method": classification_result.get("method", "unknown")
                    }
                    rag_results.append(rag_result)
                    
                    score_result = {
                        "filename": filename,
                        "category": classification_result.get("category", "C"),
                        "score": classification_result.get("score", 0.0),
                        "reason": classification_result.get("reason", "")
                    }
                    score_results.append(score_result)
                    
                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
                        
        except Exception as e:
            logger.warning(f"[证书上传] OCR/RAG处理失败，使用默认值: {e}")
        
        total_score = sum(s["score"] for s in score_results)
        
        logger.info(f"[证书上传] 上传完成: student_id={student_id}, certificate_id={certificate_id}, total_score={total_score}")
        
        return JSONResponse(content={
            "success": True,
            "message": f"上传完成: 成功{result['success_count']}个，失败{result['failed_count']}个",
            "certificate_id": certificate_id,
            "batch_id": result["batch_id"],
            "images": result["images"],
            "ocr_results": ocr_results,
            "rag_results": rag_results,
            "score_results": score_results,
            "total_score": total_score,
            "processed_at": datetime.now().isoformat()
        })
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[证书上传] 上传失败: {e}", exc_info=True)
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
