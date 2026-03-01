#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一API响应模型

提供标准化的API响应格式，确保前后端接口一致性。
"""
from typing import Generic, TypeVar, Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """统一API响应模型"""
    success: bool = Field(..., description="请求是否成功")
    message: str = Field(default="", description="响应消息")
    data: Optional[T] = Field(default=None, description="响应数据")
    error_code: Optional[str] = Field(default=None, description="错误代码")
    error_detail: Optional[str] = Field(default=None, description="错误详情")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="响应时间戳")
    request_id: Optional[str] = Field(default=None, description="请求ID")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "操作成功",
                "data": {"id": "123", "name": "示例"},
                "timestamp": "2024-01-01T12:00:00",
                "request_id": "req_abc123"
            }
        }


class PagedData(BaseModel, Generic[T]):
    """分页数据模型"""
    items: List[T] = Field(default_factory=list, description="数据列表")
    total: int = Field(default=0, description="总数量")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=20, description="每页数量")
    total_pages: int = Field(default=0, description="总页数")

    class Config:
        json_schema_extra = {
            "example": {
                "items": [{"id": "1", "name": "示例1"}, {"id": "2", "name": "示例2"}],
                "total": 100,
                "page": 1,
                "page_size": 20,
                "total_pages": 5
            }
        }


class PagedResponse(ApiResponse[PagedData[T]], Generic[T]):
    """分页响应模型"""
    pass


class ErrorResponse(BaseModel):
    """错误响应模型"""
    success: bool = Field(default=False, description="请求失败")
    error_code: str = Field(..., description="错误代码")
    message: str = Field(..., description="错误消息")
    detail: Optional[str] = Field(default=None, description="错误详情")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    request_id: Optional[str] = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error_code": "VALIDATION_ERROR",
                "message": "参数验证失败",
                "detail": "用户名长度必须在3-50个字符之间",
                "timestamp": "2024-01-01T12:00:00"
            }
        }


class ValidationErrorDetail(BaseModel):
    """验证错误详情"""
    field: str = Field(..., description="字段名")
    message: str = Field(..., description="错误消息")
    value: Optional[Any] = Field(default=None, description="实际值")


class ValidationErrorResponse(BaseModel):
    """验证错误响应"""
    success: bool = Field(default=False)
    error_code: str = Field(default="VALIDATION_ERROR")
    message: str = Field(default="参数验证失败")
    errors: List[ValidationErrorDetail] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class ErrorCode:
    """错误代码常量"""
    SUCCESS = "SUCCESS"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    DUPLICATE_ERROR = "DUPLICATE_ERROR"
    FILE_UPLOAD_ERROR = "FILE_UPLOAD_ERROR"
    OCR_ERROR = "OCR_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    RATE_LIMIT_ERROR = "RATE_LIMIT_ERROR"


def success_response(
    data: Any = None,
    message: str = "操作成功",
    request_id: str = None
) -> Dict[str, Any]:
    """生成成功响应
    
    Args:
        data: 响应数据
        message: 成功消息
        request_id: 请求ID
        
    Returns:
        标准格式的响应字典
    """
    response = {
        "success": True,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    if data is not None:
        response["data"] = data
    if request_id:
        response["request_id"] = request_id
    return response


def error_response(
    message: str,
    error_code: str = ErrorCode.UNKNOWN_ERROR,
    detail: str = None,
    request_id: str = None
) -> Dict[str, Any]:
    """生成错误响应
    
    Args:
        message: 错误消息
        error_code: 错误代码
        detail: 错误详情
        request_id: 请求ID
        
    Returns:
        标准格式的错误响应字典
    """
    response = {
        "success": False,
        "error_code": error_code,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    if detail:
        response["detail"] = detail
    if request_id:
        response["request_id"] = request_id
    return response


def paged_response(
    items: List[Any],
    total: int,
    page: int = 1,
    page_size: int = 20,
    message: str = "查询成功",
    request_id: str = None
) -> Dict[str, Any]:
    """生成分页响应
    
    Args:
        items: 数据列表
        total: 总数量
        page: 当前页码
        page_size: 每页数量
        message: 成功消息
        request_id: 请求ID
        
    Returns:
        标准格式的分页响应字典
    """
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    
    return success_response(
        data={
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        },
        message=message,
        request_id=request_id
    )


def validation_error_response(
    errors: List[Dict[str, Any]],
    message: str = "参数验证失败",
    request_id: str = None
) -> Dict[str, Any]:
    """生成验证错误响应
    
    Args:
        errors: 错误列表，每个元素包含field, message, value
        message: 错误消息
        request_id: 请求ID
        
    Returns:
        标准格式的验证错误响应字典
    """
    response = {
        "success": False,
        "error_code": ErrorCode.VALIDATION_ERROR,
        "message": message,
        "errors": errors,
        "timestamp": datetime.now().isoformat()
    }
    if request_id:
        response["request_id"] = request_id
    return response
