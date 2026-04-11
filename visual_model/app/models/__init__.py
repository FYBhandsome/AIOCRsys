#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据模型模块

统一导出所有数据模型。
"""

# Tortoise ORM 模型（数据库表）
from .tortoise_models import (
    User,
    Class as DBClass,
    ClassStudent,
    Student as DBStudent,
    AcademicScore,
    AcademicScoreHistory,
    ComprehensiveScore,
    ComprehensiveScoreConfig,
    ScoreDetail,
    ComprehensiveScoreHistory,
    File,
    FileMetadata,
    FileChunk,
    DownloadLog,
    FileAccessPermission,
    FileBackup,
    UploadRecord,
    Certificate,
    CertificateImage,
    CertificateBatch,
    SystemSetting,
    ChatHistory
)

# Pydantic 模型 - 学生相关
from .student import (
    Student,
    StudentCreate,
    StudentUpdate,
    StudentResponse,
    StudentProfile,
    Activity,
    ActivityCreate,
    ActivityUpdate,
    ActivityResponse,
    ScoreRecord,
    ScoreRecordCreate,
    ScoreRecordUpdate,
    ScoreRecordResponse,
    StudentAnalysisResponse,
    ClassRankingItem
)

# Pydantic 模型 - 班级相关
from .class_ import (
    Class,
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

# Pydantic 模型 - 认证相关
from .auth import (
    UserRole,
    Token,
    TokenData,
    UserLogin,
    UserCreate,
    UserUpdate,
    UserResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
    PasswordChange,
    EmailVerify
)

# Pydantic 模型 - API响应相关
from .response import (
    ApiResponse,
    PagedData,
    PagedResponse,
    ErrorResponse,
    ValidationErrorDetail,
    ValidationErrorResponse,
    ErrorCode,
    success_response,
    error_response,
    paged_response,
    validation_error_response
)

# Pydantic 模型 - 授权相关
from .license import (
    LicenseVerifyRequest,
    LicenseVerifyResponse,
    TokenResponse,
    SystemInfoResponse,
    NetworkStatusResponse,
    HealthCheckResponse,
    PersistentLicenseCheckResponse,
    PersistentLicenseSaveRequest,
    PersistentLicenseSaveResponse,
    StorageInfoResponse
)

__all__ = [
    # Tortoise ORM 模型（数据库表）
    "User",
    "DBClass",
    "ClassStudent",
    "DBStudent",
    "AcademicScore",
    "AcademicScoreHistory",
    "ComprehensiveScore",
    "ComprehensiveScoreConfig",
    "ScoreDetail",
    "ComprehensiveScoreHistory",
    "File",
    "FileMetadata",
    "FileChunk",
    "DownloadLog",
    "FileAccessPermission",
    "FileBackup",
    "UploadRecord",
    "Certificate",
    "CertificateImage",
    "CertificateBatch",
    "SystemSetting",
    "ChatHistory",
    
    # 学生Pydantic模型
    "Student",
    "StudentCreate",
    "StudentUpdate",
    "StudentResponse",
    "StudentProfile",
    "Activity",
    "ActivityCreate",
    "ActivityUpdate",
    "ActivityResponse",
    "ScoreRecord",
    "ScoreRecordCreate",
    "ScoreRecordUpdate",
    "ScoreRecordResponse",
    "StudentAnalysisResponse",
    "ClassRankingItem",
    
    # 班级Pydantic模型
    "Class",
    "ClassCreate",
    "ClassUpdate",
    "ClassResponse",
    "ClassProfile",
    "ClassStudentListResponse",
    "ClassStatisticsResponse",
    
    # 上传Pydantic模型
    "FileUploadResponse",
    "OCRResult",
    "FileDeleteResponse",
    
    # 认证Pydantic模型
    "UserRole",
    "Token",
    "TokenData",
    "UserLogin",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "PasswordResetRequest",
    "PasswordResetConfirm",
    "PasswordChange",
    "EmailVerify",
    
    # API响应Pydantic模型
    "ApiResponse",
    "PagedData",
    "PagedResponse",
    "ErrorResponse",
    "ValidationErrorDetail",
    "ValidationErrorResponse",
    "ErrorCode",
    "success_response",
    "error_response",
    "paged_response",
    "validation_error_response",
    
    # 授权Pydantic模型
    "LicenseVerifyRequest",
    "LicenseVerifyResponse",
    "TokenResponse",
    "SystemInfoResponse",
    "NetworkStatusResponse",
    "HealthCheckResponse",
    "PersistentLicenseCheckResponse",
    "PersistentLicenseSaveRequest",
    "PersistentLicenseSaveResponse",
    "StorageInfoResponse"
]
