#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学生相关数据模型 - 重构版本
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

# ============================================================================
# 基础模型
# ============================================================================

class BaseStudentModel(BaseModel):
    """学生基础模型"""
    class Config:
        from_attributes = True

# ============================================================================
# 学生模型
# ============================================================================

class Student(BaseStudentModel):
    """学生模型"""
    id: str
    name: str
    class_name: str
    grade: str
    major: Optional[str] = None
    college: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class StudentCreate(BaseStudentModel):
    """创建学生模型"""
    id: str
    name: str
    class_name: str
    grade: str
    major: Optional[str] = None
    college: Optional[str] = None

class StudentUpdate(BaseStudentModel):
    """更新学生模型"""
    name: Optional[str] = None
    class_name: Optional[str] = None
    grade: Optional[str] = None
    major: Optional[str] = None
    college: Optional[str] = None

class StudentResponse(BaseStudentModel):
    """学生响应模型"""
    id: str
    name: str
    class_name: str
    grade: str
    major: Optional[str] = None
    college: Optional[str] = None
    created_at: datetime
    updated_at: datetime

# ============================================================================
# 活动模型
# ============================================================================

class Activity(BaseStudentModel):
    """活动模型"""
    id: str
    student_id: str
    name: str
    type: str
    date: datetime
    location: Optional[str] = None
    description: Optional[str] = None
    score: Optional[float] = None
    created_at: datetime
    updated_at: datetime

class ActivityCreate(BaseStudentModel):
    """创建活动模型"""
    student_id: Optional[str] = None  # 将在API中设置
    name: str
    type: str
    date: datetime
    location: Optional[str] = None
    description: Optional[str] = None
    score: Optional[float] = None

class ActivityUpdate(BaseStudentModel):
    """更新活动模型"""
    name: Optional[str] = None
    type: Optional[str] = None
    date: Optional[datetime] = None
    location: Optional[str] = None
    description: Optional[str] = None
    score: Optional[float] = None

class ActivityResponse(BaseStudentModel):
    """活动响应模型"""
    id: str
    student_id: str
    name: str
    type: str
    date: datetime
    location: Optional[str] = None
    description: Optional[str] = None
    score: Optional[float] = None
    created_at: datetime
    updated_at: datetime

# ============================================================================
# 分数记录模型
# ============================================================================

class ScoreRecord(BaseStudentModel):
    """分数记录模型"""
    id: str
    student_id: str
    subject: str
    score: float
    max_score: float
    exam_date: datetime
    exam_type: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class ScoreRecordCreate(BaseStudentModel):
    """创建分数记录模型"""
    student_id: Optional[str] = None  # 将在API中设置
    subject: str
    score: float
    max_score: float
    exam_date: datetime
    exam_type: Optional[str] = None

class ScoreRecordUpdate(BaseStudentModel):
    """更新分数记录模型"""
    subject: Optional[str] = None
    score: Optional[float] = None
    max_score: Optional[float] = None
    exam_date: Optional[datetime] = None
    exam_type: Optional[str] = None

class ScoreRecordResponse(BaseStudentModel):
    """分数记录响应模型"""
    id: str
    student_id: str
    subject: str
    score: float
    max_score: float
    exam_date: datetime
    exam_type: Optional[str] = None
    created_at: datetime
    updated_at: datetime

# ============================================================================
# 班级排名模型
# ============================================================================

class ClassRankingItem(BaseStudentModel):
    """班级排名项模型"""
    rank: int
    student_id: str
    student_name: str
    total_score: float
    gpa: Optional[float] = None

class ClassRankingResponse(BaseStudentModel):
    """班级排名响应模型"""
    class_id: str
    class_name: str
    ranking: List[ClassRankingItem]
    updated_at: datetime

# ============================================================================
# 学生分析模型
# ============================================================================

class StudentProfile(BaseStudentModel):
    """学生档案模型"""
    id: str
    name: str
    class_name: str
    grade: str
    major: Optional[str] = None
    college: Optional[str] = None
    comprehensive_score: Optional[float] = None
    dormitory: Optional[str] = None
    physical_test_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime

class StudentAnalysis(BaseStudentModel):
    """学生分析模型"""
    student_id: str
    total_score: float
    rank: int
    gpa: float
    recent_activities: List[Dict[str, Any]]
    score_trend: List[Dict[str, Any]]
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    updated_at: datetime

class StudentRanking(BaseStudentModel):
    """学生排名模型"""
    rank: int
    student_id: str
    student_name: str
    total_score: float
    gpa: Optional[float] = None

class StudentAnalysisResponse(BaseStudentModel):
    """学生分析响应模型"""
    student_id: str
    total_score: float
    rank: int
    gpa: float
    recent_activities: List[Dict[str, Any]]
    score_trend: List[Dict[str, Any]]
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    updated_at: datetime