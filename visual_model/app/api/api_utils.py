#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API工具函数 - 增强版

提供统一的错误处理、响应封装、参数验证等公共功能。
"""
from typing import Callable, TypeVar, Any, Dict, List, Optional
from functools import wraps
from datetime import datetime
import uuid

from fastapi import HTTPException, status
from fastapi.responses import JSONResponse

from app.core.logger import get_logger, set_request_id, get_request_id
from app.core.data_tracer import trace_api_call, trace_data_flow, DataTracer
from app.core.exceptions import (
    StudentNotFoundException,
    ClassNotFoundException,
    FileUploadException,
    ValidationException,
    DatabaseException
)
from app.models.response import (
    success_response,
    error_response,
    paged_response,
    ErrorCode
)

logger = get_logger(__name__)
T = TypeVar('T')


def generate_request_id() -> str:
    """生成请求ID"""
    return f"req_{uuid.uuid4().hex[:12]}"


def handle_api_errors(operation_name: str, enable_trace: bool = True):
    """API错误处理装饰器
    
    统一处理API异常，减少重复的try-except代码。
    自动生成请求ID并记录日志。
    支持详细的数据追踪打印。
    
    Args:
        operation_name: 操作名称，用于日志记录
        enable_trace: 是否启用数据追踪打印
        
    Usage:
        @handle_api_errors("创建学生")
        async def create_student(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request_id = generate_request_id()
            set_request_id(request_id)
            
            if enable_trace:
                print(f"\n{'='*60}")
                print(f"[API追踪] {operation_name}")
                print(f"{'='*60}")
                print(f"请求ID: {request_id}")
                print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
                print(f"函数: {func.__name__}")
                if kwargs:
                    safe_kwargs = {k: '***' if 'password' in k.lower() or 'token' in k.lower() else v for k, v in kwargs.items()}
                    print(f"参数: {safe_kwargs}")
            
            try:
                logger.info(f"[{request_id}] {operation_name} - 开始执行")
                result = await func(*args, **kwargs)
                
                if isinstance(result, dict):
                    if "request_id" not in result:
                        result["request_id"] = request_id
                    if "success" not in result:
                        result["success"] = True
                
                if enable_trace:
                    print(f"\n[响应结果]")
                    print(f"  状态: 成功")
                    if isinstance(result, dict):
                        result_preview = str(result)[:500]
                        print(f"  数据: {result_preview}")
                    print(f"{'='*60}\n")
                
                logger.info(f"[{request_id}] {operation_name} - 执行成功")
                return result
                
            except HTTPException as e:
                logger.warning(f"[{request_id}] {operation_name} - HTTP异常: {e.detail}")
                if enable_trace:
                    print(f"\n[响应结果]")
                    print(f"  状态: HTTP异常")
                    print(f"  状态码: {e.status_code}")
                    print(f"  详情: {e.detail}")
                    print(f"{'='*60}\n")
                raise
                
            except ValidationException as e:
                logger.warning(f"[{request_id}] {operation_name} - 验证异常: {e.detail}")
                if enable_trace:
                    print(f"\n[响应结果]")
                    print(f"  状态: 验证异常")
                    print(f"  详情: {e.detail}")
                    print(f"{'='*60}\n")
                raise
                
            except (StudentNotFoundException, ClassNotFoundException) as e:
                logger.warning(f"[{request_id}] {operation_name} - 资源未找到: {e.detail}")
                if enable_trace:
                    print(f"\n[响应结果]")
                    print(f"  状态: 资源未找到")
                    print(f"  详情: {e.detail}")
                    print(f"{'='*60}\n")
                raise
                
            except FileUploadException as e:
                logger.warning(f"[{request_id}] {operation_name} - 文件上传异常: {e.detail}")
                if enable_trace:
                    print(f"\n[响应结果]")
                    print(f"  状态: 文件上传异常")
                    print(f"  详情: {e.detail}")
                    print(f"{'='*60}\n")
                raise
                
            except DatabaseException as e:
                logger.error(f"[{request_id}] {operation_name} - 数据库异常: {e.detail}")
                if enable_trace:
                    print(f"\n[响应结果]")
                    print(f"  状态: 数据库异常")
                    print(f"  详情: {e.detail}")
                    print(f"{'='*60}\n")
                raise
                
            except ValueError as e:
                logger.warning(f"[{request_id}] {operation_name} - 参数错误: {e}")
                if enable_trace:
                    print(f"\n[响应结果]")
                    print(f"  状态: 参数错误")
                    print(f"  详情: {str(e)}")
                    print(f"{'='*60}\n")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
                
            except Exception as e:
                logger.error(f"[{request_id}] {operation_name} - 未处理异常: {e}", exc_info=True)
                if enable_trace:
                    print(f"\n[响应结果]")
                    print(f"  状态: 未处理异常")
                    print(f"  异常类型: {type(e).__name__}")
                    print(f"  详情: {str(e)}")
                    print(f"{'='*60}\n")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"{operation_name}失败: {str(e)}"
                )
                
        return wrapper
    return decorator


def api_response(func: Callable) -> Callable:
    """API响应封装装饰器
    
    自动将返回值包装为标准响应格式
    
    Usage:
        @api_response
        async def get_user(user_id: str):
            return {"id": user_id, "name": "张三"}
            
        # 返回: {"success": True, "message": "操作成功", "data": {"id": ..., "name": ...}}
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        result = await func(*args, **kwargs)
        
        if isinstance(result, dict):
            if "success" in result:
                return result
            return success_response(data=result)
        
        if isinstance(result, list):
            return success_response(data=result)
            
        if result is None:
            return success_response(message="操作成功")
            
        return success_response(data=result)
    
    return wrapper


def validate_pagination(page: int, page_size: int, max_page_size: int = 100) -> tuple:
    """验证分页参数
    
    Args:
        page: 页码
        page_size: 每页数量
        max_page_size: 最大每页数量
        
    Returns:
        验证后的 (page, page_size)
        
    Raises:
        ValidationException: 参数无效时
    """
    if page < 1:
        raise ValidationException("页码必须大于0")
    
    if page_size < 1:
        raise ValidationException("每页数量必须大于0")
    
    if page_size > max_page_size:
        raise ValidationException(f"每页数量不能超过{max_page_size}")
    
    return page, page_size


def validate_id(item_id: str, field_name: str = "ID") -> str:
    """验证ID参数
    
    Args:
        item_id: ID值
        field_name: 字段名称
        
    Returns:
        验证后的ID
        
    Raises:
        ValidationException: ID无效时
    """
    if not item_id:
        raise ValidationException(f"{field_name}不能为空")
    
    if not isinstance(item_id, str):
        item_id = str(item_id)
    
    item_id = item_id.strip()
    
    if not item_id:
        raise ValidationException(f"{field_name}不能为空")
    
    return item_id


def validate_required(value: Any, field_name: str) -> Any:
    """验证必填字段
    
    Args:
        value: 字段值
        field_name: 字段名称
        
    Returns:
        验证后的值
        
    Raises:
        ValidationException: 字段为空时
    """
    if value is None:
        raise ValidationException(f"{field_name}不能为空")
    
    if isinstance(value, str) and not value.strip():
        raise ValidationException(f"{field_name}不能为空")
    
    return value


def validate_length(value: str, field_name: str, min_len: int = None, max_len: int = None) -> str:
    """验证字符串长度
    
    Args:
        value: 字符串值
        field_name: 字段名称
        min_len: 最小长度
        max_len: 最大长度
        
    Returns:
        验证后的字符串
        
    Raises:
        ValidationException: 长度不符合要求时
    """
    if not isinstance(value, str):
        value = str(value)
    
    length = len(value)
    
    if min_len is not None and length < min_len:
        raise ValidationException(f"{field_name}长度不能少于{min_len}个字符")
    
    if max_len is not None and length > max_len:
        raise ValidationException(f"{field_name}长度不能超过{max_len}个字符")
    
    return value


def validate_range(value: float, field_name: str, min_val: float = None, max_val: float = None) -> float:
    """验证数值范围
    
    Args:
        value: 数值
        field_name: 字段名称
        min_val: 最小值
        max_val: 最大值
        
    Returns:
        验证后的数值
        
    Raises:
        ValidationException: 数值不符合要求时
    """
    if min_val is not None and value < min_val:
        raise ValidationException(f"{field_name}不能小于{min_val}")
    
    if max_val is not None and value > max_val:
        raise ValidationException(f"{field_name}不能大于{max_val}")
    
    return value


def validate_in_list(value: Any, field_name: str, allowed_values: List[Any]) -> Any:
    """验证值是否在允许列表中
    
    Args:
        value: 值
        field_name: 字段名称
        allowed_values: 允许的值列表
        
    Returns:
        验证后的值
        
    Raises:
        ValidationException: 值不在允许列表中时
    """
    if value not in allowed_values:
        raise ValidationException(f"{field_name}必须是以下值之一: {', '.join(map(str, allowed_values))}")
    
    return value


class PaginationHelper:
    """分页助手类"""
    
    def __init__(self, page: int = 1, page_size: int = 20, max_page_size: int = 100):
        self.page, self.page_size = validate_pagination(page, page_size, max_page_size)
        self.offset = (self.page - 1) * self.page_size
    
    def get_offset_limit(self) -> tuple:
        """获取offset和limit"""
        return self.offset, self.page_size
    
    def get_paged_result(self, items: List[Any], total: int) -> Dict[str, Any]:
        """生成分页结果"""
        return paged_response(
            items=items,
            total=total,
            page=self.page,
            page_size=self.page_size
        )


class RequestContext:
    """请求上下文"""
    
    def __init__(self, request_id: str = None, user_id: str = None, operation: str = None):
        self.request_id = request_id or generate_request_id()
        self.user_id = user_id
        self.operation = operation
        self.start_time = datetime.now()
    
    def log_info(self, message: str):
        """记录信息日志"""
        logger.info(f"[{self.request_id}] {message}")
    
    def log_error(self, message: str, exc_info: bool = False):
        """记录错误日志"""
        logger.error(f"[{self.request_id}] {message}", exc_info=exc_info)
    
    def elapsed_ms(self) -> int:
        """计算耗时（毫秒）"""
        return int((datetime.now() - self.start_time).total_seconds() * 1000)


def create_context(operation: str, user_id: str = None) -> RequestContext:
    """创建请求上下文"""
    return RequestContext(operation=operation, user_id=user_id)


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
