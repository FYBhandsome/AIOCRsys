#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版日志配置模块 - 兼容层
==========================

此模块作为兼容层，所有日志功能由 shared_utils.unified_logger 提供。
保留此文件是为了向后兼容现有代码的导入语句。

使用方法:
    from app.core.enhanced_logger import get_logger, setup_logger
    
    setup_logger(name="visual_model")
    logger = get_logger(__name__)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared_utils.unified_logger import (
    setup_logging,
    get_logger,
    set_request_id,
    get_request_id,
    set_user_id,
    get_user_id,
    set_session_id,
    get_session_id,
    set_operation,
    get_operation,
    clear_context,
    mask_sensitive_data,
    mask_dict,
    LogContext,
    log_function_call,
    log_business_event,
    log_api_request,
    log_data_flow,
    log_branch_decision,
    LogLevel,
    UNIFIED_LOG_DIR,
    cleanup_old_logs,
    cleanup_root_log_files,
    get_service_log_dir,
)

logger = get_logger("visual_model")


def setup_logger(
    name: str = "visual_model",
    log_level: str = "INFO",
    log_dir: str = None,
    use_json: bool = False,
    use_color: bool = True,
    max_bytes: int = None,
    backup_count: int = None
):
    """
    设置日志记录器（兼容层函数）
    
    此函数保持向后兼容，内部调用统一的 setup_logging
    """
    return setup_logging(
        service_name=name,
        log_level=log_level,
        log_dir=Path(log_dir) if log_dir else None,
        enable_file=True,
        enable_async=True,
        max_bytes=max_bytes,
        backup_count=backup_count,
        enable_json=use_json,
    )


def get_log_context():
    """获取完整日志上下文"""
    from shared_utils.unified_logger import LogContext as _LogContext
    return _LogContext(
        request_id=get_request_id(),
        user_id=get_user_id(),
        session_id=get_session_id(),
        operation=get_operation()
    )


def sanitize_for_logging(data, max_length: int = 1000) -> str:
    """清理数据用于日志记录"""
    return mask_sensitive_data(data, max_length)


def create_context_logger(name: str, **context):
    """创建带上下文的日志记录器"""
    import logging
    log = logging.getLogger(name)
    return logging.LoggerAdapter(log, context)


class RequestContext:
    """请求上下文管理器"""
    
    def __init__(self, request_id: str = None, user_id: str = None, operation: str = None):
        self.request_id = request_id
        self.user_id = user_id
        self.operation = operation
        self._old_values = {}
    
    def __enter__(self):
        if self.request_id:
            self._old_values['request_id'] = get_request_id()
            set_request_id(self.request_id)
        if self.user_id:
            self._old_values['user_id'] = get_user_id()
            set_user_id(self.user_id)
        if self.operation:
            self._old_values['operation'] = get_operation()
            set_operation(self.operation)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        for key, old_value in self._old_values.items():
            if key == 'request_id':
                set_request_id(old_value)
            elif key == 'user_id':
                set_user_id(old_value)
            elif key == 'operation':
                set_operation(old_value)
        return False


def log_async_function_call(logger_instance=None, log_params: bool = True, log_result: bool = False, log_time: bool = True):
    """异步函数调用日志装饰器"""
    from functools import wraps
    import time
    import inspect
    
    def decorator(func):
        nonlocal logger_instance
        if logger_instance is None:
            logger_instance = get_logger(func.__module__)
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            func_name = func.__name__
            params = {}
            
            if log_params:
                sig = inspect.signature(func)
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                params = {k: mask_sensitive_data(str(v)[:100]) for k, v in bound.arguments.items()}
            
            logger_instance.debug(f"[{func_name}] 异步调用开始", extra={'extra_data': {'params': params}})
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration_ms = int((time.time() - start_time) * 1000)
                
                result_info = ""
                if log_result and result is not None:
                    result_info = f" -> {mask_sensitive_data(str(result)[:100])}"
                
                time_info = f" ({duration_ms}ms)" if log_time else ""
                logger_instance.debug(f"[{func_name}] 异步执行成功{result_info}{time_info}")
                return result
                
            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                logger_instance.error(
                    f"[{func_name}] 异步执行失败: {type(e).__name__}: {e} ({duration_ms}ms)",
                    exc_info=True
                )
                raise
        
        return wrapper
    return decorator


class APILogMiddleware:
    """API日志中间件辅助类"""
    
    def __init__(self, name: str = "API"):
        self.logger = get_logger(name)
    
    def log_request(self, method: str, path: str, headers: dict = None, 
                   query_params: dict = None, body = None):
        """记录请求日志"""
        log_data = {
            "type": "request",
            "method": method,
            "path": path,
        }
        
        if headers:
            log_data["headers"] = mask_dict(dict(headers))
        if query_params:
            log_data["query_params"] = query_params
        if body:
            log_data["body"] = sanitize_for_logging(body, max_length=500)
        
        self.logger.info(f"[请求] {method} {path}", extra={'extra_data': log_data})
    
    def log_response(self, method: str, path: str, status_code: int,
                    elapsed_ms: float, response_summary = None):
        """记录响应日志"""
        import logging
        log_data = {
            "type": "response",
            "method": method,
            "path": path,
            "status_code": status_code,
            "elapsed_ms": round(elapsed_ms, 2)
        }
        
        if response_summary:
            log_data["response_summary"] = sanitize_for_logging(response_summary, max_length=200)
        
        level = logging.INFO if status_code < 400 else logging.WARNING
        self.logger.log(level, f"[响应] {method} {path} -> {status_code} ({elapsed_ms:.2f}ms)", 
                       extra={'extra_data': log_data})
    
    def log_error(self, method: str, path: str, error: Exception, extra_info: dict = None):
        """记录错误日志"""
        log_data = {
            "type": "error",
            "method": method,
            "path": path,
            "error_type": type(error).__name__,
            "error_message": str(error)
        }
        
        if extra_info:
            log_data.update(extra_info)
        
        self.logger.error(f"[错误] {method} {path} -> {type(error).__name__}: {error}",
                         extra={'extra_data': log_data}, exc_info=True)


__all__ = [
    'logger',
    'get_logger',
    'setup_logger',
    'setup_logging',
    'set_request_id',
    'get_request_id',
    'set_user_id',
    'get_user_id',
    'set_session_id',
    'get_session_id',
    'set_operation',
    'get_operation',
    'clear_context',
    'get_log_context',
    'RequestContext',
    'log_function_call',
    'log_async_function_call',
    'log_business_event',
    'log_data_flow',
    'log_branch_decision',
    'LogLevel',
    'LogContext',
    'mask_sensitive_data',
    'sanitize_for_logging',
    'create_context_logger',
    'APILogMiddleware',
    'UNIFIED_LOG_DIR',
    'cleanup_old_logs',
    'cleanup_root_log_files',
    'get_service_log_dir',
]
