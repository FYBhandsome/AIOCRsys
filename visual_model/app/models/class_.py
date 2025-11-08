#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
班级相关数据模型 - 重构版本
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

# ============================================================================
# 基础模型
# ============================================================================

class BaseClassModel(BaseModel):
    """班级基础模型"""
    class Config:
        from_attributes = True

# ============================================================================
# 班级模型
# ============================================================================

class Class(BaseClassModel):
    """班级模型"""
    id: str
    name: str
    grade: str
    major: Optional[str] = None
    college: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class ClassCreate(BaseClassModel):
    """创建班级模型"""
    id: str
    name: str
    grade: str
    major: Optional[str] = None
    college: Optional[str] = None
    description: Optional[str] = None

class ClassUpdate(BaseClassModel):
    """更新班级模型"""
    name: Optional[str] = None
    grade: Optional[str] = None
    major: Optional[str] = None
    college: Optional[str] = None
    description: Optional[str] = None

class ClassResponse(BaseClassModel):
    """班级响应模型"""
    id: str
    name: str
    grade: str
    major: Optional[str] = None
    college: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

# ============================================================================
# 班级学生相关模型
# ============================================================================

class ClassProfile(BaseClassModel):
    """班级档案模型"""
    id: str
    name: str
    grade: str
    major: Optional[str] = None
    college: Optional[str] = None
    description: Optional[str] = None
    student_count: int
    created_at: datetime
    updated_at: datetime

class ClassStudentListResponse(BaseClassModel):
    """班级学生列表响应模型"""
    class_id: str
    class_name: str
    students: List[Dict[str, Any]]
    total: int
    skip: int
    limit: int

class ClassStatisticsResponse(BaseClassModel):
    """班级统计响应模型"""
    class_id: str
    class_name: str
    student_count: int
    average_score: float
    top_student: Dict[str, Any]
    subject_averages: Dict[str, float]
    updated_at: datetime

# ============================================================================
# 班级统计相关模型
# ============================================================================

class ClassStatsResponse(BaseClassModel):
    """班级统计响应模型"""
    class_id: str
    class_name: str
    student_count: int
    average_score: float
    top_student: Dict[str, Any]
    subject_averages: Dict[str, float]
    updated_at: datetime