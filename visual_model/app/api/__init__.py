#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API路由模块

统一注册所有API路由。
"""

from fastapi import APIRouter
from app.api import upload, class_
from app.api import auth, student, teacher, admin, license, ai, database, data_import, comprehensive_score, excel_fill, field_mapping, score_upload, certificate_upload, file_management
from app.business.certificate_ocr_api import router as certificate_ocr_router

# 创建主路由器
api_router = APIRouter()

# 认证路由（不需要认证）
api_router.include_router(auth.router)

# 授权验证路由（不需要认证）
api_router.include_router(license.router)

# 角色相关路由（需要认证）
api_router.include_router(student.router)
api_router.include_router(teacher.router)
api_router.include_router(admin.router)

# 数据库管理路由（仅限管理员）
api_router.include_router(database.router)

# AI助手路由（需要认证）
api_router.include_router(ai.router)

# 数据导入路由（需要认证）
api_router.include_router(data_import.router)

# 综测成绩路由（需要认证）
api_router.include_router(comprehensive_score.router)

# Excel填充路由（需要认证）
api_router.include_router(excel_fill.router)

# 字段映射路由（需要认证）
api_router.include_router(field_mapping.router)

# 成绩上传路由（需要认证）
api_router.include_router(score_upload.router)

# 证书上传路由（需要认证）
api_router.include_router(certificate_upload.router)

# 文件管理路由（需要认证）
api_router.include_router(file_management.router)

# 原有路由（保持兼容）
api_router.include_router(upload.router)
api_router.include_router(class_.router)
api_router.include_router(certificate_ocr_router, prefix="/business", tags=["证书OCR"])
