#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API工具函数

提供统一的错误处理、响应封装等公共功能。
"""

from typing import Callable, TypeVar, Any
from functools import wraps

from app.core.logger import logger
from app.core.exceptions import (
    StudentNotFoundException,
    ClassNotFoundException,
    FileUploadException
)

T = TypeVar('T')


def handle_api_errors(operation_name: str):
    """API错误处理装饰器
    
    统一处理API异常，减少重复的try-except代码。
    
    Args:
        operation_name: 操作名称，用于日志记录
        
    Usage:
        @handle_api_errors("创建学生")
        async def create_student(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except (StudentNotFoundException, ClassNotFoundException) as e:
                # 这些异常直接抛出，由FastAPI处理
                raise
            except FileUploadException as e:
                # 文件上传异常也直接抛出
                raise
            except Exception as e:
                # 其他异常记录日志并包装为FileUploadException
                logger.error(f"{operation_name}失败: {e}", exc_info=True)
                raise FileUploadException(f"{operation_name}失败: {str(e)}")
        return wrapper
    return decorator


def success_response(message: str, data: Any = None) -> dict:
    """统一成功响应格式
    
    Args:
        message: 成功消息
        data: 响应数据（可选）
        
    Returns:
        标准格式的响应字典
    """
    response = {"success": True, "message": message}
    if data is not None:
        response["data"] = data
    return response


async def validate_exists(service_func: Callable, item_id: str, 
                         not_found_exception: type) -> Any:
    """验证资源是否存在
    
    Args:
        service_func: 服务函数
        item_id: 资源ID
        not_found_exception: 未找到时抛出的异常类
        
    Returns:
        资源对象
        
    Raises:
        not_found_exception: 资源不存在时
    """
    item = await service_func(item_id)
    if not item:
        raise not_found_exception(item_id)
    return item

