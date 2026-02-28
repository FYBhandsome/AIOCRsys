#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综测成绩API路由
"""

from fastapi import APIRouter, HTTPException, Query, Body
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from app.services.comprehensive_score_service import get_comprehensive_score_service
from app.models.tortoise_models import (
    Student, Class, ComprehensiveScore, ComprehensiveScoreConfig, ScoreDetail
)
from app.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/comprehensive-score", tags=["综测成绩"])


class ScoreDetailCreate(BaseModel):
    student_id: str
    academic_year: str
    semester: str
    category_type: str
    item_name: str
    score: float
    description: Optional[str] = None
    certificate_id: Optional[int] = None


class ConfigCreate(BaseModel):
    name: str
    description: Optional[str] = None
    a_weight: float = 20.0
    b_weight: float = 70.0
    c_weight: float = 10.0
    academic_score_field: str = "weighted_average"
    academic_score_scale: float = 1.0
    is_default: bool = False


@router.post("/calculate/student/{student_id}")
async def calculate_student_score(
    student_id: str,
    academic_year: str = Query(..., description="学年，如2024-2025"),
    semester: str = Query(..., description="学期，如1或2"),
    config_id: Optional[int] = Query(None, description="配置ID")
):
    """计算单个学生的综测成绩"""
    service = get_comprehensive_score_service()
    result = await service.calculate_student_score(
        student_id, academic_year, semester, config_id
    )
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result.get('message', '计算失败'))
    
    return JSONResponse(content=result)


@router.post("/calculate/class/{class_id}")
async def calculate_class_scores(
    class_id: str,
    academic_year: str = Query(..., description="学年"),
    semester: str = Query(..., description="学期"),
    config_id: Optional[int] = Query(None, description="配置ID")
):
    """计算班级所有学生的综测成绩"""
    service = get_comprehensive_score_service()
    result = await service.calculate_class_scores(
        class_id, academic_year, semester, config_id
    )
    
    return JSONResponse(content=result)


@router.get("/student/{student_id}")
async def get_student_score(
    student_id: str,
    academic_year: str = Query(..., description="学年"),
    semester: str = Query(..., description="学期")
):
    """获取学生综测成绩"""
    service = get_comprehensive_score_service()
    result = await service.get_student_score_details(student_id, academic_year, semester)
    
    return JSONResponse(content=result)


@router.get("/class/{class_id}/ranking")
async def get_class_ranking(
    class_id: str,
    academic_year: str = Query(..., description="学年"),
    semester: str = Query(..., description="学期")
):
    """获取班级排名"""
    scores = await ComprehensiveScore.filter(
        student__class_name=class_id,
        academic_year=academic_year,
        semester=semester
    ).order_by('-total_score').all()
    
    rankings = []
    for rank, score in enumerate(scores, 1):
        student = await Student.get(id=score.student_id)
        rankings.append({
            'rank': rank,
            'student_id': score.student_id,
            'student_name': student.name,
            'a_total_score': score.a_total_score,
            'b_total_score': score.b_total_score,
            'c_total_score': score.c_total_score,
            'total_score': score.total_score
        })
    
    return JSONResponse(content={
        'class_id': class_id,
        'academic_year': academic_year,
        'semester': semester,
        'total_count': len(rankings),
        'rankings': rankings
    })


@router.post("/detail")
async def add_score_detail(detail: ScoreDetailCreate):
    """添加加减分明细"""
    if detail.category_type not in ['A1', 'A2', 'A3', 'C1', 'C2', 'C3', 'C4']:
        raise HTTPException(status_code=400, detail="无效的类别类型")
    
    service = get_comprehensive_score_service()
    result = await service.add_score_detail(
        student_id=detail.student_id,
        academic_year=detail.academic_year,
        semester=detail.semester,
        category_type=detail.category_type,
        item_name=detail.item_name,
        score=detail.score,
        description=detail.description,
        certificate_id=detail.certificate_id
    )
    
    return JSONResponse(content={
        'success': True,
        'id': result.id,
        'message': '添加成功'
    })


@router.delete("/detail/{detail_id}")
async def delete_score_detail(detail_id: int):
    """删除加减分明细"""
    detail = await ScoreDetail.get_or_none(id=detail_id)
    if not detail:
        raise HTTPException(status_code=404, detail="明细不存在")
    
    await detail.delete()
    return JSONResponse(content={'success': True, 'message': '删除成功'})


@router.get("/config/list")
async def list_configs():
    """获取综测配置列表"""
    configs = await ComprehensiveScoreConfig.filter(is_active=True).all()
    
    return JSONResponse(content={
        'configs': [{
            'id': c.id,
            'name': c.name,
            'description': c.description,
            'a_weight': c.a_weight,
            'b_weight': c.b_weight,
            'c_weight': c.c_weight,
            'academic_score_field': c.academic_score_field,
            'academic_score_scale': c.academic_score_scale,
            'is_default': c.is_default
        } for c in configs]
    })


@router.post("/config")
async def create_config(config: ConfigCreate):
    """创建综测配置"""
    total_weight = config.a_weight + config.b_weight + config.c_weight
    if abs(total_weight - 100.0) > 0.01:
        raise HTTPException(status_code=400, detail="权重总和必须为100%")
    
    if config.is_default:
        await ComprehensiveScoreConfig.filter(is_default=True).update(is_default=False)
    
    new_config = await ComprehensiveScoreConfig.create(
        name=config.name,
        description=config.description,
        a_weight=config.a_weight,
        b_weight=config.b_weight,
        c_weight=config.c_weight,
        academic_score_field=config.academic_score_field,
        academic_score_scale=config.academic_score_scale,
        is_default=config.is_default,
        is_active=True
    )
    
    return JSONResponse(content={
        'success': True,
        'id': new_config.id,
        'message': '配置创建成功'
    })


@router.put("/config/{config_id}")
async def update_config(config_id: int, config: ConfigCreate):
    """更新综测配置"""
    existing = await ComprehensiveScoreConfig.get_or_none(id=config_id)
    if not existing:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    total_weight = config.a_weight + config.b_weight + config.c_weight
    if abs(total_weight - 100.0) > 0.01:
        raise HTTPException(status_code=400, detail="权重总和必须为100%")
    
    if config.is_default and not existing.is_default:
        await ComprehensiveScoreConfig.filter(is_default=True).update(is_default=False)
    
    existing.name = config.name
    existing.description = config.description
    existing.a_weight = config.a_weight
    existing.b_weight = config.b_weight
    existing.c_weight = config.c_weight
    existing.academic_score_field = config.academic_score_field
    existing.academic_score_scale = config.academic_score_scale
    existing.is_default = config.is_default
    await existing.save()
    
    return JSONResponse(content={'success': True, 'message': '配置更新成功'})


@router.get("/classes")
async def list_classes():
    """获取班级列表"""
    classes = await Class.all()
    
    return JSONResponse(content={
        'classes': [{
            'id': c.id,
            'name': c.name,
            'grade': c.grade,
            'major': c.major,
            'college': c.college,
            'student_count': c.student_count
        } for c in classes]
    })


@router.get("/class/{class_id}/stats")
async def get_class_stats(
    class_id: str,
    academic_year: str = Query(..., description="学年"),
    semester: str = Query(..., description="学期")
):
    """获取班级统计信息"""
    scores = await ComprehensiveScore.filter(
        student__class_name=class_id,
        academic_year=academic_year,
        semester=semester
    ).all()
    
    if not scores:
        return JSONResponse(content={
            'class_id': class_id,
            'total_students': 0,
            'stats': None
        })
    
    total_scores = [s.total_score for s in scores]
    avg_score = sum(total_scores) / len(total_scores)
    max_score = max(total_scores)
    min_score = min(total_scores)
    
    return JSONResponse(content={
        'class_id': class_id,
        'academic_year': academic_year,
        'semester': semester,
        'total_students': len(scores),
        'stats': {
            'average': round(avg_score, 2),
            'max': round(max_score, 2),
            'min': round(min_score, 2),
            'a_average': round(sum(s.a_total_score for s in scores) / len(scores), 2),
            'b_average': round(sum(s.b_total_score for s in scores) / len(scores), 2),
            'c_average': round(sum(s.c_total_score for s in scores) / len(scores), 2)
        }
    })
