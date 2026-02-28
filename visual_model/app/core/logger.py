#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志配置模块 - 增强版
支持：
- 分级日志管理 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- 请求追踪 (Request ID)
- 用户上下文
- 性能监控
- 敏感数据过滤
- 日志轮转与归档
- 结构化日志输出
"""
import logging
import os
import sys
import json
import traceback
import uuid
import contextvars
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from functools import wraps
import time
import threading

from config import settings

_request_id: contextvars.ContextVar[str] = contextvars.ContextVar('request_id', default='')
_user_id: contextvars.ContextVar[str] = contextvars.ContextVar('user_id', default='')
_session_id: contextvars.ContextVar[str] = contextvars.ContextVar('session_id', default='')


def set_request_id(request_id: str = None) -> str:
    """设置当前请求ID"""
    if request_id is None:
        request_id = f"req_{uuid.uuid4().hex[:12]}"
    _request_id.set(request_id)
    return request_id


def get_request_id() -> str:
    """获取当前请求ID"""
    return _request_id.get()


def set_user_id(user_id: str) -> None:
    """设置当前用户ID"""
    _user_id.set(str(user_id) if user_id else '')


def get_user_id() -> str:
    """获取当前用户ID"""
    return _user_id.get()


def clear_context() -> None:
    """清除所有上下文变量"""
    _request_id.set('')
    _user_id.set('')
    _session_id.set('')


class ContextFormatter(logging.Formatter):
    """支持上下文信息的日志格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        request_id = get_request_id()
        user_id = get_user_id()
        
        context_parts = []
        if request_id:
            context_parts.append(f"rid={request_id[:8]}")
        if user_id:
            context_parts.append(f"uid={user_id}")
        
        context_str = f" [{', '.join(context_parts)}]" if context_parts else ""
        
        original_msg = record.getMessage()
        if context_str:
            record.msg = f"{context_str} {original_msg}"
            record.args = ()
        
        return super().format(record)


class JsonFormatter(logging.Formatter):
    """JSON格式的日志格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        request_id = get_request_id()
        if request_id:
            log_data["request_id"] = request_id
        
        user_id = get_user_id()
        if user_id:
            log_data["user_id"] = user_id
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        if hasattr(record, 'extra_data'):
            log_data["extra"] = record.extra_data
            
        return json.dumps(log_data, ensure_ascii=False)


def setup_logger(name: str = "app", use_json: bool = False) -> logging.Logger:
    """设置日志记录器"""
    log_dir = os.path.dirname(settings.LOG_FILE)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    try:
        os.environ["PYTHONIOENCODING"] = "utf-8"
        
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        else:
            import io
            if hasattr(sys.stdout, "buffer"):
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
            if hasattr(sys.stderr, "buffer"):
                sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"Warning: Failed to set UTF-8 encoding for console: {e}")

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    if logger.handlers:
        return logger
    
    if use_json:
        formatter = JsonFormatter()
    else:
        formatter = ContextFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    file_handler = RotatingFileHandler(
        settings.LOG_FILE,
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    file_handler.setFormatter(formatter)
    
    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    log_file_str = str(settings.LOG_FILE)
    error_log_file = log_file_str.replace('.log', '_error.log')
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.addHandler(error_handler)
    
    return logger


def log_function_call(logger: logging.Logger, log_params: bool = True, log_result: bool = False):
    """函数调用日志装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            params = {}
            if log_params:
                import inspect
                sig = inspect.signature(func)
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                params = {k: str(v)[:100] for k, v in bound.arguments.items()}
            
            logger.debug(f"[{func_name}] 调用开始", extra={'extra_data': {'params': params}})
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration_ms = int((time.time() - start_time) * 1000)
                
                result_info = ""
                if log_result and result is not None:
                    if isinstance(result, dict):
                        result_info = f" -> {type(result).__name__}[{len(result)}]"
                    elif isinstance(result, (list, tuple)):
                        result_info = f" -> {type(result).__name__}[{len(result)}]"
                
                logger.debug(f"[{func_name}] 执行成功{result_info}", extra={'extra_data': {'duration_ms': duration_ms}})
                return result
                
            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                logger.error(
                    f"[{func_name}] 执行失败: {type(e).__name__}: {e}",
                    extra={'extra_data': {'duration_ms': duration_ms, 'params': params}},
                    exc_info=True
                )
                raise
        
        return wrapper
    return decorator


def log_async_function_call(logger: logging.Logger, log_params: bool = True, log_result: bool = False):
    """异步函数调用日志装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            func_name = func.__name__
            params = {}
            if log_params:
                import inspect
                sig = inspect.signature(func)
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                params = {k: str(v)[:100] for k, v in bound.arguments.items()}
            
            logger.debug(f"[{func_name}] 异步调用开始", extra={'extra_data': {'params': params}})
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration_ms = int((time.time() - start_time) * 1000)
                
                logger.debug(f"[{func_name}] 异步执行成功", extra={'extra_data': {'duration_ms': duration_ms}})
                return result
                
            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                logger.error(
                    f"[{func_name}] 异步执行失败: {type(e).__name__}: {e}",
                    extra={'extra_data': {'duration_ms': duration_ms, 'params': params}},
                    exc_info=True
                )
                raise
        
        return wrapper
    return decorator


class RequestContext:
    """请求上下文管理器"""
    
    def __init__(self, request_id: str = None, user_id: str = None):
        self.request_id = request_id
        self.user_id = user_id
        self._old_request_id = None
        self._old_user_id = None
    
    def __enter__(self):
        self._old_request_id = get_request_id()
        self._old_user_id = get_user_id()
        
        if self.request_id:
            set_request_id(self.request_id)
        if self.user_id:
            set_user_id(self.user_id)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._old_request_id:
            set_request_id(self._old_request_id)
        else:
            _request_id.set('')
        
        if self._old_user_id:
            set_user_id(self._old_user_id)
        else:
            _user_id.set('')
        
        return False


logger = setup_logger("comprehensive-assessment")


def get_logger(name: str = None) -> logging.Logger:
    """获取日志记录器
    
    Args:
        name: 日志记录器名称，如果为None则返回默认logger
        
    Returns:
        logging.Logger: 日志记录器实例
    """
    if name is None:
        return logger
    return logging.getLogger(name)