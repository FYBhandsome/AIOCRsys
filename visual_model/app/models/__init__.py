#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据模型模块

统一导出所有数据模型。
"""

# Tortoise ORM 模型
from .tortoise_models import (
    User,
    Student as DBStudent,
    AcademicScore,
    ComprehensiveScore,
    ComprehensiveScoreConfig,
    File,
    Certificate
)

# Pydantic 模型 - 学生相关
from .student import (
    StudentCreate,
    StudentUpdate,
    StudentResponse,
    StudentProfile,
    ActivityCreate,
    ActivityResponse,
    ScoreRecordCreate,
    ScoreRecordResponse,
    StudentAnalysisResponse,
    ClassRankingItem
)

# Pydantic 模型 - 班级相关
from .class_ import (
    ClassCreate,
    ClassUpdate,
    ClassResponse,
    ClassProfile,
    ClassStudentListResponse,
    ClassStatisticsResponse
)

# Pydantic 模型 - 上传相关
from .upload import (
    FileUploadResponse,
    OCRResult,
    FileDeleteResponse
)

__all__ = [
    # Tortoise ORM 模型
    "User",
    "DBStudent",
    "AcademicScore",
    "ComprehensiveScore",
    "ComprehensiveScoreConfig",
    "File",
    "Certificate",
    
    # 学生Pydantic模型
    "StudentCreate",
    "StudentUpdate",
    "StudentResponse",
    "StudentProfile",
    "ActivityCreate",
    "ActivityResponse",
    "ScoreRecordCreate",
    "ScoreRecordResponse",
    "StudentAnalysisResponse",
    "ClassRankingItem",
    
    # 班级Pydantic模型
    "ClassCreate",
    "ClassUpdate",
    "ClassResponse",
    "ClassProfile",
    "ClassStudentListResponse",
    "ClassStatisticsResponse",
    
    # 上传Pydantic模型
    "FileUploadResponse",
    "OCRResult",
    "FileDeleteResponse"
]
