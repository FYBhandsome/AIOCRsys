#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综测Excel填充API路由
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
import os
import tempfile
import shutil
from datetime import datetime

from app.services.excel_fill_service import get_excel_fill_service
from app.services.rag_comprehensive_service import get_rag_comprehensive_service
from app.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/excel-fill", tags=["Excel填充"])


class OCRProcessRequest(BaseModel):
    """OCR处理请求"""
    ocr_text: str
    student_id: Optional[str] = None
    student_name: Optional[str] = None
    academic_year: Optional[str] = None
    semester: Optional[str] = None


class BatchProcessRequest(BaseModel):
    """批量处理请求"""
    students_data: List[Dict[str, Any]]
    academic_year: str
    semester: str


@router.post("/from-template")
async def fill_from_template(
    template_file: UploadFile = File(..., description="Excel模板文件"),
    raw_data_file: UploadFile = File(..., description="原始数据文件（OCR识别文本或成绩单）"),
    academic_year: Optional[str] = Form(None, description="学年"),
    semester: Optional[str] = Form(None, description="学期"),
    class_id: Optional[str] = Form(None, description="班级ID")
):
    """
    使用RAG检索结果填充Excel模板
    
    Args:
        template_file: Excel模板文件
        raw_data_file: 原始数据文件
        academic_year: 学年
        semester: 学期
        class_id: 班级ID
    
    Returns:
        填充后的Excel文件
    """
    logger.info(f"开始Excel填充: academic_year={academic_year}, semester={semester}, class_id={class_id}")
    
    if not template_file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="模板文件必须是Excel格式(.xlsx, .xls)")
    
    temp_dir = tempfile.mkdtemp()
    template_path = None
    raw_data_path = None
    output_path = None
    
    try:
        template_path = os.path.join(temp_dir, "template.xlsx")
        with open(template_path, "wb") as f:
            shutil.copyfileobj(template_file.file, f)
        
        raw_data_path = os.path.join(temp_dir, "raw_data.txt")
        with open(raw_data_path, "wb") as f:
            shutil.copyfileobj(raw_data_file.file, f)
        
        with open(raw_data_path, "r", encoding="utf-8") as f:
            raw_data = f.read()
        
        output_path = os.path.join(temp_dir, f"filled_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
        
        service = get_excel_fill_service()
        result = await service.fill_excel_from_rag(
            template_path=template_path,
            output_path=output_path,
            raw_data=raw_data,
            academic_year=academic_year,
            semester=semester,
            class_id=class_id
        )
        
        if result.get("success"):
            return FileResponse(
                path=output_path,
                filename=f"综测成绩_{class_id or 'all'}_{academic_year or ''}.xlsx",
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "填充失败"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Excel填充失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"填充失败: {str(e)}")
    
    finally:
        pass


@router.post("/process-ocr")
async def process_ocr_result(request: OCRProcessRequest):
    """
    处理OCR识别结果
    
    Args:
        request: OCR处理请求
    
    Returns:
        处理结果，包含分类和分数
    """
    logger.info(f"处理OCR结果: student_id={request.student_id}")
    
    service = get_excel_fill_service()
    
    student_info = {}
    if request.student_id:
        student_info["student_id"] = request.student_id
    if request.student_name:
        student_info["student_name"] = request.student_name
    
    result = await service.process_ocr_result(
        ocr_text=request.ocr_text,
        student_info=student_info if student_info else None,
        academic_year=request.academic_year,
        semester=request.semester
    )
    
    return JSONResponse(content=result)


@router.post("/batch-process")
async def batch_process_students(request: BatchProcessRequest):
    """
    批量处理学生数据
    
    Args:
        request: 批量处理请求
    
    Returns:
        处理结果
    """
    logger.info(f"批量处理学生数据: count={len(request.students_data)}")
    
    service = get_excel_fill_service()
    result = await service.batch_process_students(
        students_data=request.students_data,
        academic_year=request.academic_year,
        semester=request.semester
    )
    
    return JSONResponse(content=result)


@router.get("/weight-config")
async def get_weight_config(
    academic_year: str = Query(..., description="学年"),
    semester: str = Query(..., description="学期")
):
    """
    获取权重配置
    
    Args:
        academic_year: 学年
        semester: 学期
    
    Returns:
        权重配置信息
    """
    logger.info(f"获取权重配置: academic_year={academic_year}, semester={semester}")
    
    rag_service = get_rag_comprehensive_service()
    result = await rag_service.get_weight_config(academic_year, semester)
    
    return JSONResponse(content=result)


@router.post("/analyze-certificate")
async def analyze_certificate(
    certificate_text: str = Form(..., description="证书OCR文本"),
    student_id: Optional[str] = Form(None, description="学号"),
    student_name: Optional[str] = Form(None, description="姓名")
):
    """
    分析证书并计算加分
    
    Args:
        certificate_text: 证书OCR文本
        student_id: 学号
        student_name: 姓名
    
    Returns:
        分析结果
    """
    logger.info(f"分析证书: student_id={student_id}")
    
    student_info = {}
    if student_id:
        student_info["student_id"] = student_id
    if student_name:
        student_info["student_name"] = student_name
    
    rag_service = get_rag_comprehensive_service()
    result = await rag_service.analyze_certificate(
        certificate_text=certificate_text,
        student_info=student_info if student_info else None
    )
    
    return JSONResponse(content=result)


@router.post("/retrieve-rules")
async def retrieve_rules(query: str = Form(..., description="查询问题")):
    """
    检索综测规则
    
    Args:
        query: 查询问题
    
    Returns:
        检索到的规则
    """
    logger.info(f"检索规则: query={query[:50]}...")
    
    rag_service = get_rag_comprehensive_service()
    result = await rag_service.retrieve_rules(query)
    
    return JSONResponse(content=result)


@router.post("/calculate-score")
async def calculate_single_score(
    student_id: str = Form(..., description="学号"),
    student_name: str = Form(..., description="姓名"),
    class_name: str = Form(..., description="班级"),
    academic_info: str = Form(..., description="学业成绩信息JSON"),
    certificate_info: str = Form("[]", description="证书信息JSON数组"),
    score_details: str = Form("[]", description="加减分明细JSON数组")
):
    """
    计算单个学生综测成绩
    
    Args:
        student_id: 学号
        student_name: 姓名
        class_name: 班级
        academic_info: 学业成绩信息JSON字符串
        certificate_info: 证书信息JSON数组字符串
        score_details: 加减分明细JSON数组字符串
    
    Returns:
        计算结果
    """
    logger.info(f"计算学生成绩: student_id={student_id}")
    
    import json
    
    try:
        academic_info_dict = json.loads(academic_info)
    except json.JSONDecodeError:
        academic_info_dict = {}
    
    try:
        certificate_info_list = json.loads(certificate_info)
    except json.JSONDecodeError:
        certificate_info_list = []
    
    try:
        score_details_list = json.loads(score_details)
    except json.JSONDecodeError:
        score_details_list = []
    
    rag_service = get_rag_comprehensive_service()
    result = await rag_service.calculate_student_score(
        student_id=student_id,
        student_name=student_name,
        class_name=class_name,
        academic_info=academic_info_dict,
        certificate_info=certificate_info_list,
        score_details=score_details_list
    )
    
    return JSONResponse(content=result)


@router.get("/template-columns")
async def get_template_columns():
    """获取模板列映射"""
    from app.services.excel_fill_service import ExcelFillService
    
    return JSONResponse(content={
        "columns": ExcelFillService.COLUMN_MAPPING,
        "header_row": ExcelFillService.HEADER_ROW
    })
