#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自定义异常处理模块
"""

from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.logger import logger


# ============================================================================
# 业务异常
# ============================================================================

class FileUploadException(HTTPException):
    """文件上传异常"""
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class OCRProcessingException(HTTPException):
    """OCR处理异常"""
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)


class StudentNotFoundException(HTTPException):
    """学生未找到异常"""
    def __init__(self, student_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"学生不存在: {student_id}"
        )


class ClassNotFoundException(HTTPException):
    """班级未找到异常"""
    def __init__(self, class_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"班级不存在: {class_id}"
        )


class ValidationException(HTTPException):
    """验证异常"""
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


class DatabaseException(HTTPException):
    """数据库异常"""
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)


# ============================================================================
# 全局异常处理器
# ============================================================================

async def validation_exception_handler(request, exc: RequestValidationError):
    """验证异常处理"""
    logger.warning(f"验证失败: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()}
    )


async def http_exception_handler(request, exc: HTTPException):
    """HTTP异常处理"""
    logger.error(f"HTTP异常: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


async def general_exception_handler(request, exc: Exception):
    """通用异常处理"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "服务器内部错误"}
    )
