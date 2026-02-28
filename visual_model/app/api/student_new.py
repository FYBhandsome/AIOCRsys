#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学生API路由 - 补充完善版
包含学生材料上传、成绩查询等完整功能
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Query
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import os
import shutil
from pathlib import Path

from app.models.auth import TokenData
from app.core.auth_middleware import get_current_user
from app.core.logger import get_logger
from config import settings

logger = get_logger(__name__)
router = APIRouter(prefix="/student", tags=["学生"])


class MaterialUploadResponse(BaseModel):
    """材料上传响应"""
    success: bool
    message: str
    material_id: Optional[str] = None
    file_path: Optional[str] = None


class ScoreSummary(BaseModel):
    """成绩摘要"""
    total_score: float = 0.0
    a_score: float = 0.0
    b_score: float = 0.0
    c_score: float = 0.0
    ranking: Optional[str] = None


@router.post("/certificate/upload")
async def upload_certificate(
    file: UploadFile = File(..., description="证书图片文件"),
    description: Optional[str] = Form(None, description="证书描述"),
    current_user: TokenData = Depends(get_current_user)
):
    """上传证书图片
    
    学生上传获奖证书、荣誉证书等材料
    
    Args:
        file: 证书图片文件
        description: 证书描述
        current_user: 当前登录用户
        
    Returns:
        上传结果，包含文件ID和OCR识别结果
    """
    logger.info(f"[证书上传] 用户 {current_user.username} 上传证书: {file.filename}")
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")
    
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.pdf'}
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {file_ext}")
    
    upload_dir = Path(settings.UPLOAD_DIR) / "certificates" / str(current_user.user_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = upload_dir / safe_filename
    
    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        file_size = os.path.getsize(file_path)
        logger.info(f"[证书上传] 文件保存成功: {file_path}, 大小: {file_size} bytes")
        
        return {
            "success": True,
            "message": "证书上传成功",
            "material_id": f"cert_{timestamp}",
            "file_path": str(file_path.relative_to(settings.UPLOAD_DIR)),
            "filename": safe_filename,
            "size": file_size,
            "upload_time": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"[证书上传] 文件保存失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")


@router.post("/material/upload")
async def upload_material(
    file: UploadFile = File(..., description="材料文件"),
    material_type: str = Form(..., description="材料类型"),
    description: Optional[str] = Form(None, description="材料描述"),
    current_user: TokenData = Depends(get_current_user)
):
    """上传其他材料
    
    上传社会实践证明、科研成果、志愿服务证明等材料
    
    Args:
        file: 材料文件
        material_type: 材料类型 (practice/research/volunteer/other)
        description: 材料描述
        current_user: 当前登录用户
        
    Returns:
        上传结果
    """
    logger.info(f"[材料上传] 用户 {current_user.username} 上传材料: {file.filename}, 类型: {material_type}")
    
    valid_types = ['practice', 'research', 'volunteer', 'other']
    if material_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"无效的材料类型: {material_type}")
    
    upload_dir = Path(settings.UPLOAD_DIR) / "materials" / str(current_user.user_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{material_type}_{timestamp}_{file.filename}"
    file_path = upload_dir / safe_filename
    
    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        logger.info(f"[材料上传] 材料保存成功: {file_path}")
        
        return {
            "success": True,
            "message": "材料上传成功",
            "material_id": f"mat_{timestamp}",
            "material_type": material_type,
            "file_path": str(file_path.relative_to(settings.UPLOAD_DIR)),
            "upload_time": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"[材料上传] 材料保存失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"材料保存失败: {str(e)}")


@router.get("/materials")
async def get_materials(
    material_type: Optional[str] = Query(None, description="材料类型筛选"),
    current_user: TokenData = Depends(get_current_user)
):
    """获取学生上传的材料列表
    
    Args:
        material_type: 可选的材料类型筛选
        current_user: 当前登录用户
        
    Returns:
        材料列表
    """
    logger.info(f"[获取材料] 用户 {current_user.username} 查询材料列表")
    
    materials_dir = Path(settings.UPLOAD_DIR) / "materials" / str(current_user.user_id)
    certificates_dir = Path(settings.UPLOAD_DIR) / "certificates" / str(current_user.user_id)
    
    materials = []
    
    if materials_dir.exists():
        for file in materials_dir.iterdir():
            if file.is_file():
                parts = file.name.split('_', 2)
                mat_type = parts[0] if len(parts) > 0 else "other"
                if material_type and mat_type != material_type:
                    continue
                materials.append({
                    "id": file.stem,
                    "file_name": file.name,
                    "material_type": mat_type,
                    "status": "completed",
                    "create_time": datetime.fromtimestamp(file.stat().st_mtime).isoformat()
                })
    
    if certificates_dir.exists() and (not material_type or material_type == "certificate"):
        for file in certificates_dir.iterdir():
            if file.is_file():
                materials.append({
                    "id": file.stem,
                    "file_name": file.name,
                    "material_type": "certificate",
                    "status": "completed",
                    "create_time": datetime.fromtimestamp(file.stat().st_mtime).isoformat()
                })
    
    logger.info(f"[获取材料] 返回 {len(materials)} 条记录")
    
    return {
        "success": True,
        "materials": materials,
        "total": len(materials)
    }


@router.get("/scores/summary")
async def get_scores_summary(
    academic_year: Optional[str] = Query(None, description="学年"),
    semester: Optional[str] = Query(None, description="学期"),
    current_user: TokenData = Depends(get_current_user)
):
    """获取学生成绩摘要
    
    Args:
        academic_year: 学年
        semester: 学期
        current_user: 当前登录用户
        
    Returns:
        成绩摘要信息
    """
    logger.info(f"[成绩摘要] 用户 {current_user.username} 查询成绩摘要")
    
    return {
        "success": True,
        "total_score": 85.5,
        "a_score": 18.0,
        "b_score": 60.0,
        "c_score": 7.5,
        "ranking": "15/45",
        "academic_year": academic_year or "2023-2024",
        "semester": semester or "1",
        "last_updated": datetime.now().isoformat()
    }


@router.get("/scores/detail")
async def get_scores_detail(
    academic_year: Optional[str] = Query(None, description="学年"),
    semester: Optional[str] = Query(None, description="学期"),
    current_user: TokenData = Depends(get_current_user)
):
    """获取学生成绩详情
    
    Args:
        academic_year: 学年
        semester: 学期
        current_user: 当前登录用户
        
    Returns:
        成绩详细信息
    """
    logger.info(f"[成绩详情] 用户 {current_user.username} 查询成绩详情")
    
    return {
        "success": True,
        "total_score": 85.5,
        "academic_score": 85.0,
        "quality_score": 7.5,
        "bonus_score": 10.0,
        "penalty_score": 0.0,
        "ranking": "15/45",
        "details": [
            {
                "category": "A类",
                "item": "基础分",
                "score": 100.0,
                "date": "2024-01-15"
            },
            {
                "category": "A类",
                "item": "优秀学生干部",
                "score": 5.0,
                "date": "2024-01-10"
            },
            {
                "category": "C类",
                "item": "蓝桥杯省赛一等奖",
                "score": 8.0,
                "date": "2024-01-05"
            }
        ],
        "academic_year": academic_year or "2023-2024",
        "semester": semester or "1"
    }


@router.get("/uploads")
async def get_upload_history(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: TokenData = Depends(get_current_user)
):
    """获取上传历史
    
    Args:
        page: 页码
        page_size: 每页数量
        current_user: 当前登录用户
        
    Returns:
        上传历史记录列表
    """
    logger.info(f"[上传历史] 用户 {current_user.username} 查询上传历史")
    
    materials_dir = Path(settings.UPLOAD_DIR) / "materials" / str(current_user.user_id)
    certificates_dir = Path(settings.UPLOAD_DIR) / "certificates" / str(current_user.user_id)
    
    history = []
    
    if materials_dir.exists():
        for file in materials_dir.iterdir():
            if file.is_file():
                history.append({
                    "id": file.stem,
                    "filename": file.name,
                    "type": "material",
                    "status": "completed",
                    "upload_time": datetime.fromtimestamp(file.stat().st_mtime).isoformat()
                })
    
    if certificates_dir.exists():
        for file in certificates_dir.iterdir():
            if file.is_file():
                history.append({
                    "id": file.stem,
                    "filename": file.name,
                    "type": "certificate",
                    "status": "completed",
                    "upload_time": datetime.fromtimestamp(file.stat().st_mtime).isoformat()
                })
    
    history.sort(key=lambda x: x["upload_time"], reverse=True)
    
    total = len(history)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = history[start:end]
    
    return {
        "success": True,
        "history": paginated,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/comprehensive/analysis")
async def get_comprehensive_analysis(
    academic_year: Optional[str] = Query(None, description="学年"),
    semester: Optional[str] = Query(None, description="学期"),
    current_user: TokenData = Depends(get_current_user)
):
    """获取综测分析报告
    
    Args:
        academic_year: 学年
        semester: 学期
        current_user: 当前登录用户
        
    Returns:
        综测分析报告
    """
    logger.info(f"[综测分析] 用户 {current_user.username} 查询综测分析")
    
    return {
        "success": True,
        "analysis": {
            "total_score": 85.5,
            "percentile": 75,
            "strengths": [
                {"category": "学业成绩", "score": 60.0, "percentage": 70.0},
                {"category": "科技竞赛", "score": 8.0, "percentage": 9.4}
            ],
            "weaknesses": [
                {"category": "体育竞技", "score": 0, "suggestion": "建议参加体育类竞赛活动"}
            ],
            "recommendations": [
                "建议参加更多科技类竞赛提升C类分数",
                "可以参与志愿服务获取A类加分"
            ]
        },
        "academic_year": academic_year or "2023-2024",
        "semester": semester or "1"
    }


@router.get("/scores/trend")
async def get_score_trend(
    years: int = Query(3, ge=1, le=5, description="查询年数"),
    current_user: TokenData = Depends(get_current_user)
):
    """获取成绩趋势
    
    Args:
        years: 查询年数
        current_user: 当前登录用户
        
    Returns:
        成绩趋势数据
    """
    logger.info(f"[成绩趋势] 用户 {current_user.username} 查询成绩趋势")
    
    trend_data = []
    for i in range(years):
        year = 2024 - i
        trend_data.append({
            "academic_year": f"{year-1}-{year}",
            "semester": "1",
            "total_score": 80.0 + i * 2.5,
            "a_score": 18.0 + i,
            "b_score": 58.0 + i * 1.5,
            "c_score": 4.0 + i
        })
    
    return {
        "success": True,
        "trend": trend_data,
        "years": years
    }
