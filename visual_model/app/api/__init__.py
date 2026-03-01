#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API路由模块

统一注册所有API路由。
"""

from fastapi import APIRouter
from app.api import upload, class_
from app.api import auth, student, teacher, admin, license, ai, database, data_import, comprehensive_score, excel_fill, field_mapping, score_upload, certificate_upload, file_management
from app.api.frontend_logs import router as frontend_logs_router
from app.business.certificate_ocr_api import router as certificate_ocr_router

api_router = APIRouter()

api_router.include_router(auth.router)

api_router.include_router(license.router)

api_router.include_router(student.router)
api_router.include_router(teacher.router)
api_router.include_router(admin.router)

api_router.include_router(database.router)

api_router.include_router(ai.router)

api_router.include_router(data_import.router)

api_router.include_router(comprehensive_score.router)

api_router.include_router(excel_fill.router)

api_router.include_router(field_mapping.router)

api_router.include_router(score_upload.router)

api_router.include_router(certificate_upload.router)

api_router.include_router(file_management.router)

api_router.include_router(frontend_logs_router, tags=["前端日志"])

api_router.include_router(upload.router)
api_router.include_router(class_.router)
api_router.include_router(certificate_ocr_router, prefix="/business", tags=["证书OCR"])
