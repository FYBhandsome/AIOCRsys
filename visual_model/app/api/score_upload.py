#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
成绩上传API路由
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from typing import Optional, List
from datetime import datetime

from app.services.score_upload_service import get_score_upload_service
from app.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/score-upload", tags=["成绩上传"])


@router.post("/upload")
async def upload_score_sheet(
    file: UploadFile = File(..., description="成绩单Excel文件"),
    academic_year: str = Form(..., description="学年，如2024-2025"),
    semester: str = Form(..., description="学期，如1或2"),
    uploaded_by: str = Form(..., description="上传者用户名"),
    upload_role: str = Form("student", description="上传者角色")
):
    """
    上传成绩单并处理
    
    Args:
        file: 成绩单Excel文件
        academic_year: 学年
        semester: 学期
        uploaded_by: 上传者
        upload_role: 上传者角色
    
    Returns:
        处理结果
    """
    logger.info(f"上传成绩单: {file.filename}, academic_year={academic_year}, semester={semester}")
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="只支持Excel文件格式(.xlsx, .xls)")
    
    try:
        file_content = await file.read()
        
        service = get_score_upload_service()
        result = await service.process_upload(
            file_content=file_content,
            filename=file.filename,
            academic_year=academic_year,
            semester=semester,
            uploaded_by=uploaded_by,
            upload_role=upload_role
        )
        
        if result['success']:
            return JSONResponse(content={
                'success': True,
                'message': f"处理完成：成功{result['processed']}条，失败{result['failed']}条",
                'file_id': result['file_id'],
                'upload_id': result['upload_id'],
                'processed': result['processed'],
                'failed': result['failed']
            })
        else:
            raise HTTPException(status_code=500, detail=result.get('error', '处理失败'))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传成绩单失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.get("/history/{student_id}")
async def get_student_score_history(
    student_id: str,
    academic_year: Optional[str] = Query(None, description="学年"),
    semester: Optional[str] = Query(None, description="学期")
):
    """
    获取学生成绩历史记录
    
    Args:
        student_id: 学号
        academic_year: 学年（可选）
        semester: 学期（可选）
    
    Returns:
        历史记录列表
    """
    service = get_score_upload_service()
    history = await service.get_student_score_history(
        student_id=student_id,
        academic_year=academic_year,
        semester=semester
    )
    
    return JSONResponse(content={
        'success': True,
        'student_id': student_id,
        'history': history,
        'total': len(history)
    })


@router.get("/upload-records")
async def get_upload_records(
    upload_by: Optional[str] = Query(None, description="上传者"),
    status: Optional[str] = Query(None, description="状态"),
    limit: int = Query(20, description="返回数量限制")
):
    """
    获取上传记录列表
    
    Args:
        upload_by: 上传者（可选）
        status: 状态（可选）
        limit: 返回数量限制
    
    Returns:
        上传记录列表
    """
    service = get_score_upload_service()
    records = await service.get_upload_records(
        upload_by=upload_by,
        status=status,
        limit=limit
    )
    
    return JSONResponse(content={
        'success': True,
        'records': records,
        'total': len(records)
    })


@router.get("/field-mapping")
async def get_field_mapping():
    """获取字段映射信息"""
    from app.services.score_upload_service import ScoreUploadService
    
    return JSONResponse(content={
        'mapping': ScoreUploadService.FIELD_MAPPING,
        'description': 'Excel列名到数据库字段的映射关系'
    })


@router.post("/preview")
async def preview_score_sheet(
    file: UploadFile = File(..., description="成绩单Excel文件"),
    rows: int = Form(10, description="预览行数")
):
    """
    预览成绩单数据
    
    Args:
        file: 成绩单Excel文件
        rows: 预览行数
    
    Returns:
        数据预览
    """
    import pandas as pd
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="只支持Excel文件格式")
    
    try:
        df = pd.read_excel(file.file, sheet_name=0, header=0, nrows=rows)
        
        return JSONResponse(content={
            'success': True,
            'columns': list(df.columns),
            'row_count': len(df),
            'data': df.to_dict(orient='records')
        })
        
    except Exception as e:
        logger.error(f"预览成绩单失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"预览失败: {str(e)}")
