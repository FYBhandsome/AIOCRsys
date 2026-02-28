"""
统一的异常处理模块
提供集中化的异常定义和处理机制
"""
from typing import Any, Dict, Optional
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError


class AppException(Exception):
    """应用基础异常类"""
    
    def __init__(
        self,
        message: str,
        error_code: str = "APP_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class LLMException(AppException):
    """LLM相关异常"""
    
    def __init__(
        self,
        message: str = "LLM服务异常",
        error_code: str = "LLM_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, 503, details)


class VectorDBException(AppException):
    """向量数据库异常"""
    
    def __init__(
        self,
        message: str = "向量数据库异常",
        error_code: str = "VECTOR_DB_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, 503, details)


class DocumentNotFoundException(AppException):
    """文档未找到异常"""
    
    def __init__(
        self,
        message: str = "文档不存在",
        document_id: Optional[str] = None
    ):
        details = {"document_id": document_id} if document_id else {}
        super().__init__(message, "DOCUMENT_NOT_FOUND", 404, details)


class ConfigurationException(AppException):
    """配置异常"""
    
    def __init__(
        self,
        message: str = "配置错误",
        error_code: str = "CONFIG_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, 400, details)


class ValidationException(AppException):
    """验证异常"""
    
    def __init__(
        self,
        message: str = "数据验证失败",
        error_code: str = "VALIDATION_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, 422, details)


class AuthenticationException(AppException):
    """认证异常"""
    
    def __init__(
        self,
        message: str = "认证失败",
        error_code: str = "AUTH_ERROR"
    ):
        super().__init__(message, error_code, 401)


class AuthorizationException(AppException):
    """授权异常"""
    
    def __init__(
        self,
        message: str = "权限不足",
        error_code: str = "AUTHORIZATION_ERROR"
    ):
        super().__init__(message, error_code, 403)


class RateLimitException(AppException):
    """限流异常"""
    
    def __init__(
        self,
        message: str = "请求过于频繁",
        retry_after: int = 60
    ):
        super().__init__(message, "RATE_LIMIT_ERROR", 429, {"retry_after": retry_after})


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """应用异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """HTTP异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "HTTP_ERROR",
                "message": exc.detail,
                "details": {}
            }
        }
    )


async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """验证异常处理器"""
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
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "请求参数验证失败",
                "details": {"errors": errors}
            }
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """通用异常处理器"""
    import logging
    logger = logging.getLogger(__name__)
    logger.exception(f"未处理的异常: {str(exc)}")
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "服务器内部错误",
                "details": {}
            }
        }
    )


def register_exception_handlers(app):
    """
    注册所有异常处理器到FastAPI应用
    
    Args:
        app: FastAPI应用实例
    """
    from fastapi.exceptions import RequestValidationError
    
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
