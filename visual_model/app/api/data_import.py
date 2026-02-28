#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据导入API路由
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional
import os
import tempfile
import shutil

from app.services.data_import_service import get_data_import_service
from app.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/data-import", tags=["数据导入"])


@router.post("/excel")
async def import_excel_data(
    file: UploadFile = File(...),
    academic_year: Optional[str] = Form(None),
    semester: Optional[str] = Form(None),
    class_id: Optional[str] = Form(None)
):
    """
    导入综测Excel数据
    
    Args:
        file: Excel文件
        academic_year: 学年，如 "2024-2025"
        semester: 学期，如 "1" 或 "2"
        class_id: 班级ID，如 "230521"
    
    Returns:
        导入结果统计
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="只支持Excel文件格式(.xlsx, .xls)")
    
    temp_file = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_path = temp_file.name
        
        import_service = get_data_import_service()
        result = await import_service.import_from_excel(
            file_path=temp_path,
            academic_year=academic_year,
            semester=semester,
            class_id=class_id
        )
        
        return JSONResponse(content=result)
    
    except Exception as e:
        logger.error(f"导入Excel数据失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")
    
    finally:
        if temp_file and os.path.exists(temp_path):
            os.unlink(temp_path)


@router.get("/template")
async def get_import_template():
    """获取导入模板信息"""
    import_service = get_data_import_service()
    template = await import_service.get_import_template()
    return JSONResponse(content=template)


@router.post("/preview")
async def preview_excel_data(
    file: UploadFile = File(...),
    rows: int = Form(10)
):
    """
    预览Excel数据
    
    Args:
        file: Excel文件
        rows: 预览行数
    
    Returns:
        数据预览
    """
    import pandas as pd
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="只支持Excel文件格式(.xlsx, .xls)")
    
    temp_file = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_path = temp_file.name
        
        xl = pd.ExcelFile(temp_path)
        preview_data = {
            'sheets': xl.sheet_names,
            'data': {}
        }
        
        for sheet_name in xl.sheet_names:
            df = pd.read_excel(xl, sheet_name=sheet_name, header=2, nrows=rows)
            preview_data['data'][sheet_name] = {
                'columns': list(df.columns),
                'row_count': len(df),
                'sample': df.head(rows).to_dict(orient='records')
            }
        
        return JSONResponse(content=preview_data)
    
    except Exception as e:
        logger.error(f"预览Excel数据失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"预览失败: {str(e)}")
    
    finally:
        if temp_file and os.path.exists(temp_path):
            os.unlink(temp_path)
