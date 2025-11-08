#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
班级数据查询API路由

提供班级排名等查询功能（示例实现）。
"""

from typing import List

from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter(prefix="/class-data", tags=["班级数据查询"])


class ClassRankingItem(BaseModel):
    """班级排名项"""
    rank: int
    student_id: str
    name: str
    gpa: float
    total_score: float


@router.get("/rankings", response_model=List[ClassRankingItem])
async def get_class_rankings(limit: int = Query(20, ge=1, le=100)):
    """获取班级排名（示例实现）
    
    Args:
        limit: 返回的排名数量（1-100）
        
    Returns:
        排名列表
    """
    # 示例数据
    return [
        ClassRankingItem(
            rank=i,
            student_id=f"2023{i:03d}",
            name=f"学生{i}",
            gpa=round(4.0 - (i * 0.1), 2),
            total_score=round(95.0 - (i * 0.5), 2)
        )
        for i in range(1, min(limit + 1, 21))
    ]
