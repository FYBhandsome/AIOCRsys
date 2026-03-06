#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API接口规范模块 - 统一响应格式
定义统一的请求/响应格式、状态码、错误处理机制
与visual_model保持一致
"""
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union
from datetime import datetime
from pydantic import BaseModel, Field
from fastapi import status
from fastapi.responses import JSONResponse


class ResponseCode(str, Enum):
    """API响应状态码枚举"""
    
    # 成功状态码 (2xx)
    SUCCESS = "200"
    CREATED = "201"
    ACCEPTED = "202"
    NO_CONTENT = "204"
    
    # 客户端错误 (4xx)
    BAD_REQUEST = "400"
    UNAUTHORIZED = "401"
    FORBIDDEN = "403"
    NOT_FOUND = "404"
    METHOD_NOT_ALLOWED = "405"
    CONFLICT = "409"
    UNPROCESSABLE_ENTITY = "422"
    TOO_MANY_REQUESTS = "429"
    
    # 服务端错误 (5xx)
    INTERNAL_ERROR = "500"
    NOT_IMPLEMENTED = "501"
    BAD_GATEWAY = "502"
    SERVICE_UNAVAILABLE = "503"
    GATEWAY_TIMEOUT = "504"
    
    # 业务错误码 (1xxx)
    BUSINESS_ERROR = "1000"
    VALIDATION_ERROR = "1001"
    DATA_NOT_FOUND = "1002"
    DATA_ALREADY_EXISTS = "1003"
    OPERATION_FAILED = "1004"
    PERMISSION_DENIED = "1005"
    
    # 数据库错误码 (2xxx)
    DATABASE_ERROR = "2000"
    DATABASE_CONNECTION_ERROR = "2001"
    DATABASE_QUERY_ERROR = "2002"
    
    # 文件错误码 (3xxx)
    FILE_UPLOAD_ERROR = "3000"
    FILE_NOT_FOUND = "3001"
    FILE_TYPE_NOT_ALLOWED = "3002"
    FILE_SIZE_EXCEEDED = "3003"
    
    # 认证错误码 (4xxx)
    AUTH_ERROR = "4000"
    TOKEN_EXPIRED = "4001"
    TOKEN_INVALID = "4002"
    LOGIN_FAILED = "4003"
    ACCOUNT_DISABLED = "4004"


class ErrorCode(str, Enum):
    """详细错误码枚举"""
    
    # 通用错误
    UNKNOWN_ERROR = "ERR_0000"
    INVALID_PARAMETER = "ERR_0001"
    MISSING_PARAMETER = "ERR_0002"
    PARAMETER_TYPE_ERROR = "ERR_0003"
    
    # 用户相关
    USER_NOT_FOUND = "ERR_1001"
    USER_ALREADY_EXISTS = "ERR_1002"
    PASSWORD_MISMATCH = "ERR_1003"
    ACCOUNT_LOCKED = "ERR_1004"
    
    # 学生相关
    STUDENT_NOT_FOUND = "ERR_2001"
    STUDENT_ALREADY_EXISTS = "ERR_2002"
    INVALID_STUDENT_ID = "ERR_2003"
    
    # 成绩相关
    SCORE_NOT_FOUND = "ERR_3001"
    SCORE_CALCULATION_ERROR = "ERR_3002"
    INVALID_SCORE_DATA = "ERR_3003"
    
    # 文件相关
    FILE_READ_ERROR = "ERR_4001"
    FILE_WRITE_ERROR = "ERR_4002"
    FILE_DELETE_ERROR = "ERR_4003"
    
    # RAG相关
    RAG_CONNECTION_ERROR = "ERR_5001"
    RAG_QUERY_ERROR = "ERR_5002"
    RAG_RESPONSE_ERROR = "ERR_5003"


T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一API响应模型"""
    
    code: str = Field(default=ResponseCode.SUCCESS, description="响应状态码")
    message: str = Field(default="操作成功", description="响应消息")
    data: Optional[T] = Field(default=None, description="响应数据")
    errors: Optional[List[Dict[str, Any]]] = Field(default=None, description="错误详情列表")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="响应时间戳")
    request_id: Optional[str] = Field(default=None, description="请求ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "200",
                "message": "操作成功",
                "data": {"id": 1, "name": "示例"},
                "errors": None,
                "timestamp": "2024-01-01T12:00:00",
                "request_id": "req_123456"
            }
        }


class PagedResponse(BaseModel, Generic[T]):
    """分页响应模型"""
    
    items: List[T] = Field(default_factory=list, description="数据列表")
    total: int = Field(default=0, description="总记录数")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=20, description="每页大小")
    total_pages: int = Field(default=0, description="总页数")
    has_next: bool = Field(default=False, description="是否有下一页")
    has_prev: bool = Field(default=False, description="是否有上一页")


class ErrorDetail(BaseModel):
    """错误详情模型"""
    
    field: Optional[str] = Field(default=None, description="错误字段")
    message: str = Field(description="错误消息")
    code: Optional[str] = Field(default=None, description="错误码")
    value: Optional[Any] = Field(default=None, description="错误值")


class ApiException(Exception):
    """API异常基类"""
    
    def __init__(
        self,
        code: str = ResponseCode.INTERNAL_ERROR,
        message: str = "服务器内部错误",
        errors: List[Dict[str, Any]] = None,
        http_status: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        self.code = code
        self.message = message
        self.errors = errors or []
        self.http_status = http_status
        super().__init__(message)


class BadRequestException(ApiException):
    """400 错误请求异常"""
    
    def __init__(self, message: str = "请求参数错误", errors: List[Dict] = None):
        super().__init__(
            code=ResponseCode.BAD_REQUEST,
            message=message,
            errors=errors,
            http_status=status.HTTP_400_BAD_REQUEST
        )


class UnauthorizedException(ApiException):
    """401 未授权异常"""
    
    def __init__(self, message: str = "未授权访问"):
        super().__init__(
            code=ResponseCode.UNAUTHORIZED,
            message=message,
            http_status=status.HTTP_401_UNAUTHORIZED
        )


class ForbiddenException(ApiException):
    """403 禁止访问异常"""
    
    def __init__(self, message: str = "禁止访问"):
        super().__init__(
            code=ResponseCode.FORBIDDEN,
            message=message,
            http_status=status.HTTP_403_FORBIDDEN
        )


class NotFoundException(ApiException):
    """404 资源不存在异常"""
    
    def __init__(self, message: str = "资源不存在"):
        super().__init__(
            code=ResponseCode.NOT_FOUND,
            message=message,
            http_status=status.HTTP_404_NOT_FOUND
        )


class ValidationException(ApiException):
    """422 验证失败异常"""
    
    def __init__(self, message: str = "数据验证失败", errors: List[Dict] = None):
        super().__init__(
            code=ResponseCode.VALIDATION_ERROR,
            message=message,
            errors=errors,
            http_status=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


class BusinessException(ApiException):
    """业务逻辑异常"""
    
    def __init__(self, message: str, code: str = ResponseCode.BUSINESS_ERROR):
        super().__init__(
            code=code,
            message=message,
            http_status=status.HTTP_400_BAD_REQUEST
        )


class DatabaseException(ApiException):
    """数据库异常"""
    
    def __init__(self, message: str = "数据库操作失败"):
        super().__init__(
            code=ResponseCode.DATABASE_ERROR,
            message=message,
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class FileException(ApiException):
    """文件操作异常"""
    
    def __init__(self, message: str, code: str = ResponseCode.FILE_UPLOAD_ERROR):
        super().__init__(
            code=code,
            message=message,
            http_status=status.HTTP_400_BAD_REQUEST
        )


class ResponseBuilder:
    """响应构建器"""
    
    @staticmethod
    def success(
        data: Any = None,
        message: str = "操作成功",
        request_id: str = None
    ) -> Dict[str, Any]:
        """构建成功响应"""
        return {
            "code": ResponseCode.SUCCESS,
            "message": message,
            "data": data,
            "errors": None,
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id
        }
    
    @staticmethod
    def created(
        data: Any = None,
        message: str = "创建成功",
        request_id: str = None
    ) -> Dict[str, Any]:
        """构建创建成功响应"""
        return {
            "code": ResponseCode.CREATED,
            "message": message,
            "data": data,
            "errors": None,
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id
        }
    
    @staticmethod
    def error(
        message: str = "操作失败",
        code: str = ResponseCode.INTERNAL_ERROR,
        errors: List[Dict] = None,
        request_id: str = None
    ) -> Dict[str, Any]:
        """构建错误响应"""
        return {
            "code": code,
            "message": message,
            "data": None,
            "errors": errors,
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id
        }
    
    @staticmethod
    def paged(
        items: List[Any],
        total: int,
        page: int = 1,
        page_size: int = 20,
        message: str = "查询成功"
    ) -> Dict[str, Any]:
        """构建分页响应"""
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        
        return {
            "code": ResponseCode.SUCCESS,
            "message": message,
            "data": {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            },
            "errors": None,
            "timestamp": datetime.now().isoformat()
        }


def api_response(
    data: Any = None,
    message: str = "操作成功",
    code: str = ResponseCode.SUCCESS,
    status_code: int = status.HTTP_200_OK
) -> JSONResponse:
    """创建API响应"""
    return JSONResponse(
        status_code=status_code,
        content={
            "code": code,
            "message": message,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    )


def error_response(
    message: str,
    code: str = ResponseCode.INTERNAL_ERROR,
    errors: List[Dict] = None,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
) -> JSONResponse:
    """创建错误响应"""
    return JSONResponse(
        status_code=status_code,
        content={
            "code": code,
            "message": message,
            "data": None,
            "errors": errors,
            "timestamp": datetime.now().isoformat()
        }
    )
