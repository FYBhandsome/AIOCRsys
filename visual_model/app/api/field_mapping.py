#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字段映射API路由
处理成绩单与综测表之间的数据映射和填充
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
import os
import tempfile
import shutil
from datetime import datetime

from app.services.field_mapping_service import get_field_mapping_service
from app.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/field-mapping", tags=["字段映射"])


class MappingPreviewRequest(BaseModel):
    """映射预览请求"""
    source_file: str
    template_file: str


@router.post("/process")
async def process_and_fill(
    source_file: UploadFile = File(..., description="学生成绩单文件"),
    template_file: UploadFile = File(..., description="综测计算表模板"),
    academic_year: Optional[str] = Form(None, description="学年"),
    semester: Optional[str] = Form(None, description="学期"),
    output_dir: Optional[str] = Form(None, description="输出目录")
):
    """
    处理成绩单并填充综测计算表
    
    Args:
        source_file: 学生成绩单Excel文件
        template_file: 综测计算表模板Excel文件
        academic_year: 学年
        semester: 学期
        output_dir: 输出目录
    
    Returns:
        处理结果和输出文件路径
    """
    logger.info(f"开始处理: academic_year={academic_year}, semester={semester}")
    
    if not source_file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="成绩单文件必须是Excel格式")
    
    if not template_file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="模板文件必须是Excel格式")
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        source_path = os.path.join(temp_dir, "source.xlsx")
        with open(source_path, "wb") as f:
            shutil.copyfileobj(source_file.file, f)
        
        template_path = os.path.join(temp_dir, "template.xlsx")
        with open(template_path, "wb") as f:
            shutil.copyfileobj(template_file.file, f)
        
        if not output_dir:
            output_dir = os.path.join(temp_dir, "output")
        
        service = get_field_mapping_service()
        result = await service.process_and_fill(
            source_file=source_path,
            template_file=template_path,
            output_dir=output_dir,
            academic_year=academic_year,
            semester=semester
        )
        
        if result.get("success"):
            output_file = result.get("output_file")
            
            return JSONResponse(content={
                "success": True,
                "output_file": output_file,
                "processed": result.get("processed", 0),
                "failed": result.get("failed", 0),
                "results": result.get("results", []),
                "weight_config": result.get("weight_config", {}),
                "message": f"处理完成：成功{result.get('processed', 0)}人，失败{result.get('failed', 0)}人"
            })
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "处理失败"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"处理失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")
    
    finally:
        pass


@router.post("/download")
async def process_and_download(
    source_file: UploadFile = File(..., description="学生成绩单文件"),
    template_file: UploadFile = File(..., description="综测计算表模板"),
    academic_year: Optional[str] = Form(None, description="学年"),
    semester: Optional[str] = Form(None, description="学期")
):
    """
    处理成绩单并下载填充后的综测计算表
    
    Args:
        source_file: 学生成绩单Excel文件
        template_file: 综测计算表模板Excel文件
        academic_year: 学年
        semester: 学期
    
    Returns:
        填充后的Excel文件
    """
    logger.info(f"开始处理并下载: academic_year={academic_year}, semester={semester}")
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        source_path = os.path.join(temp_dir, "source.xlsx")
        with open(source_path, "wb") as f:
            shutil.copyfileobj(source_file.file, f)
        
        template_path = os.path.join(temp_dir, "template.xlsx")
        with open(template_path, "wb") as f:
            shutil.copyfileobj(template_file.file, f)
        
        output_dir = temp_dir
        
        service = get_field_mapping_service()
        result = await service.process_and_fill(
            source_file=source_path,
            template_file=template_path,
            output_dir=output_dir,
            academic_year=academic_year,
            semester=semester
        )
        
        if result.get("success"):
            output_file = result.get("output_file")
            
            return FileResponse(
                path=output_file,
                filename=f"综测成绩_{academic_year or '未知'}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "处理失败"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"处理失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@router.get("/source-fields")
async def get_source_fields():
    """获取源数据字段映射"""
    from app.services.field_mapping_service import FieldMappingService
    
    return JSONResponse(content={
        "fields": FieldMappingService.SOURCE_FIELDS,
        "description": "学生成绩单字段映射"
    })


@router.get("/target-fields")
async def get_target_fields():
    """获取目标字段映射"""
    from app.services.field_mapping_service import FieldMappingService
    
    return JSONResponse(content={
        "fields": FieldMappingService.TARGET_FIELDS,
        "description": "综测计算表字段映射"
    })


@router.post("/preview-source")
async def preview_source_data(
    file: UploadFile = File(..., description="学生成绩单文件"),
    rows: int = Form(10, description="预览行数")
):
    """
    预览源数据
    
    Args:
        file: 学生成绩单文件
        rows: 预览行数
    
    Returns:
        数据预览
    """
    import pandas as pd
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="文件必须是Excel格式")
    
    temp_file = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_path = temp_file.name
        
        df = pd.read_excel(temp_path, sheet_name=0, header=0, nrows=rows)
        
        return JSONResponse(content={
            "columns": list(df.columns),
            "row_count": len(df),
            "data": df.to_dict(orient='records')
        })
        
    except Exception as e:
        logger.error(f"预览失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"预览失败: {str(e)}")
    
    finally:
        if temp_file and os.path.exists(temp_path):
            os.unlink(temp_path)
