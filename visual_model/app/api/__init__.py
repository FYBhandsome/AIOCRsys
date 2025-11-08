#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API路由模块

统一注册所有API路由。
"""

from fastapi import APIRouter
from app.api import upload, class_, class_data, student_data
from app.api import auth, student, teacher, admin, license, ai, database
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

# 原有路由（保持兼容）
api_router.include_router(upload.router)
api_router.include_router(class_.router)
api_router.include_router(class_data.router)
api_router.include_router(student_data.router)
api_router.include_router(certificate_ocr_router, prefix="/business", tags=["证书OCR"])
