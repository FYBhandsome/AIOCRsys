"""
统一的异常处理模块
提供集中化的异常定义和处理机制 - 与visual_model保持一致
"""
from typing import Any, Dict, Optional
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from datetime import datetime

from app.core.api_response import (
    ApiResponse, ResponseCode, ResponseBuilder,
    api_response, error_response
)


class LLMException(Exception):
    """LLM相关异常"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


async def app_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """应用异常处理器 - 使用统一响应格式"""
    
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": str(exc.status_code),
                "message": exc.detail,
                "data": None,
                "errors": None,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    return JSONResponse(
        status_code=500,
        content={
            "code": ResponseCode.INTERNAL_ERROR,
            "message": "服务器内部错误",
            "data": None,
            "errors": [{"message": str(exc)}],
            "timestamp": datetime.now().isoformat()
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """HTTP异常处理器 - 使用统一响应格式"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": str(exc.status_code),
            "message": exc.detail,
            "data": None,
            "errors": None,
            "timestamp": datetime.now().isoformat()
        }
    )


async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """验证异常处理器 - 使用统一响应格式"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=422,
        content={
            "code": ResponseCode.VALIDATION_ERROR,
            "message": "请求参数验证失败",
            "data": None,
            "errors": errors,
            "timestamp": datetime.now().isoformat()
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """通用异常处理器 - 使用统一响应格式"""
    import logging
    logger = logging.getLogger(__name__)
    logger.exception(f"未处理的异常: {str(exc)}")
    
    return JSONResponse(
        status_code=500,
        content={
            "code": ResponseCode.INTERNAL_ERROR,
            "message": "服务器内部错误",
            "data": None,
            "errors": [{"message": str(exc)}],
            "timestamp": datetime.now().isoformat()
        }
    )


def register_exception_handlers(app):
    """
    注册所有异常处理器到FastAPI应用
    
    Args:
        app: FastAPI应用实例
    """
    from fastapi.exceptions import RequestValidationError
    
    app.add_exception_handler(Exception, app_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
