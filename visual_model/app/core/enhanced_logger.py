#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版日志配置模块
支持：
- 分级日志管理 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- 请求追踪 (Request ID)
- 用户上下文
- 性能监控
- 敏感数据过滤
- 日志轮转与归档
- 结构化日志输出
- 终端彩色输出
- 业务流程追踪
"""
import logging
import os
import sys
import json
import traceback
import uuid
import contextvars
import time
import threading
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from functools import wraps
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum


class LogLevel(Enum):
    """日志级别枚举"""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


@dataclass
class LogContext:
    """日志上下文"""
    request_id: str = ""
    user_id: str = ""
    session_id: str = ""
    operation: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)


_request_id: contextvars.ContextVar[str] = contextvars.ContextVar('request_id', default='')
_user_id: contextvars.ContextVar[str] = contextvars.ContextVar('user_id', default='')
_session_id: contextvars.ContextVar[str] = contextvars.ContextVar('session_id', default='')
_operation: contextvars.ContextVar[str] = contextvars.ContextVar('operation', default='')


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


def set_operation(operation: str) -> None:
    """设置当前操作"""
    _operation.set(operation)


def get_operation() -> str:
    """获取当前操作"""
    return _operation.get()


def clear_context() -> None:
    """清除所有上下文变量"""
    _request_id.set('')
    _user_id.set('')
    _session_id.set('')
    _operation.set('')


def get_log_context() -> LogContext:
    """获取完整日志上下文"""
    return LogContext(
        request_id=_request_id.get(),
        user_id=_user_id.get(),
        session_id=_session_id.get(),
        operation=_operation.get()
    )


class ColorCodes:
    """终端颜色代码"""
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    DIM = '\033[2m'


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""
    
    LEVEL_COLORS = {
        logging.DEBUG: ColorCodes.CYAN,
        logging.INFO: ColorCodes.GREEN,
        logging.WARNING: ColorCodes.YELLOW,
        logging.ERROR: ColorCodes.RED,
        logging.CRITICAL: ColorCodes.RED + ColorCodes.BOLD,
    }
    
    def format(self, record: logging.LogRecord) -> str:
        request_id = get_request_id()
        user_id = get_user_id()
        operation = get_operation()
        
        context_parts = []
        if request_id:
            context_parts.append(f"rid={request_id[:8]}")
        if user_id:
            context_parts.append(f"uid={user_id}")
        if operation:
            context_parts.append(f"op={operation}")
        
        context_str = f" [{', '.join(context_parts)}]" if context_parts else ""
        
        color = self.LEVEL_COLORS.get(record.levelno, ColorCodes.WHITE)
        level_name = f"{color}{record.levelname:8s}{ColorCodes.RESET}"
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        timestamp_str = f"{ColorCodes.DIM}{timestamp}{ColorCodes.RESET}"
        
        message = record.getMessage()
        if context_str:
            message = f"{ColorCodes.CYAN}{context_str}{ColorCodes.RESET} {message}"
        
        formatted = f"{timestamp_str} | {level_name} | {record.name:20s} | {message}"
        
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"
        
        return formatted


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
        
        operation = get_operation()
        if operation:
            log_data["operation"] = operation
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        if hasattr(record, 'extra_data'):
            log_data["extra"] = record.extra_data
            
        return json.dumps(log_data, ensure_ascii=False)


class BusinessLogFormatter(logging.Formatter):
    """业务日志格式化器 - 突出关键业务信息"""
    
    def format(self, record: logging.LogRecord) -> str:
        request_id = get_request_id()
        user_id = get_user_id()
        operation = get_operation()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        prefix_parts = [f"[{timestamp}]"]
        
        if operation:
            prefix_parts.append(f"[{operation}]")
        
        if request_id:
            prefix_parts.append(f"[{request_id[:8]}]")
        
        prefix = "".join(prefix_parts)
        
        level_icons = {
            logging.DEBUG: "🔍",
            logging.INFO: "✅",
            logging.WARNING: "⚠️",
            logging.ERROR: "❌",
            logging.CRITICAL: "🔥",
        }
        icon = level_icons.get(record.levelno, "📝")
        
        message = record.getMessage()
        
        formatted = f"{prefix} {icon} {message}"
        
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"
        
        return formatted


def setup_logger(
    name: str = "app",
    log_level: str = "INFO",
    log_dir: str = None,
    use_json: bool = False,
    use_color: bool = True,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5
) -> logging.Logger:
    """设置日志记录器
    
    Args:
        name: 日志记录器名称
        log_level: 日志级别
        log_dir: 日志目录
        use_json: 是否使用JSON格式
        use_color: 是否使用彩色输出
        max_bytes: 单个日志文件最大字节数
        backup_count: 保留的日志文件数量
        
    Returns:
        配置好的日志记录器
    """
    if log_dir is None:
        log_dir = os.path.join(os.getcwd(), "logs")
    
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    try:
        os.environ["PYTHONIOENCODING"] = "utf-8"
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"Warning: Failed to set UTF-8 encoding: {e}")

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    if logger.handlers:
        return logger
    
    if use_json:
        formatter = JsonFormatter()
    elif use_color:
        formatter = ColoredFormatter()
    else:
        formatter = BusinessLogFormatter()
    
    log_file = os.path.join(log_dir, f"{name}.log")
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, log_level.upper()))
    file_handler.setFormatter(JsonFormatter() if not use_json else formatter)
    
    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(ColoredFormatter() if use_color else BusinessLogFormatter())
    
    error_log_file = os.path.join(log_dir, f"{name}_error.log")
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JsonFormatter())
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.addHandler(error_handler)
    
    return logger


def log_function_call(
    logger: logging.Logger,
    log_params: bool = True,
    log_result: bool = False,
    log_time: bool = True
):
    """函数调用日志装饰器
    
    Args:
        logger: 日志记录器
        log_params: 是否记录参数
        log_result: 是否记录结果
        log_time: 是否记录执行时间
    """
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
                params = {k: _sanitize_value(v) for k, v in bound.arguments.items()}
            
            logger.debug(f"[{func_name}] 调用开始", extra={'extra_data': {'params': params}})
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration_ms = int((time.time() - start_time) * 1000)
                
                result_info = ""
                if log_result and result is not None:
                    result_info = f" -> {_sanitize_value(result)[:100]}"
                
                time_info = f" ({duration_ms}ms)" if log_time else ""
                logger.debug(f"[{func_name}] 执行成功{result_info}{time_info}")
                return result
                
            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                logger.error(
                    f"[{func_name}] 执行失败: {type(e).__name__}: {e} ({duration_ms}ms)",
                    exc_info=True
                )
                raise
        
        return wrapper
    return decorator


def log_async_function_call(
    logger: logging.Logger,
    log_params: bool = True,
    log_result: bool = False,
    log_time: bool = True
):
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
                params = {k: _sanitize_value(v) for k, v in bound.arguments.items()}
            
            logger.debug(f"[{func_name}] 异步调用开始", extra={'extra_data': {'params': params}})
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration_ms = int((time.time() - start_time) * 1000)
                
                result_info = ""
                if log_result and result is not None:
                    result_info = f" -> {_sanitize_value(result)[:100]}"
                
                time_info = f" ({duration_ms}ms)" if log_time else ""
                logger.debug(f"[{func_name}] 异步执行成功{result_info}{time_info}")
                return result
                
            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                logger.error(
                    f"[{func_name}] 异步执行失败: {type(e).__name__}: {e} ({duration_ms}ms)",
                    exc_info=True
                )
                raise
        
        return wrapper
    return decorator


def _sanitize_value(value: Any, max_length: int = 100) -> str:
    """清理敏感数据"""
    sensitive_keys = {'password', 'token', 'secret', 'key', 'credential'}
    
    if isinstance(value, dict):
        sanitized = {}
        for k, v in value.items():
            if any(s in k.lower() for s in sensitive_keys):
                sanitized[k] = "***REDACTED***"
            else:
                sanitized[k] = _sanitize_value(v, max_length)
        return str(sanitized)[:max_length]
    elif isinstance(value, (list, tuple)):
        return str([_sanitize_value(v, max_length) for v in value])[:max_length]
    else:
        return str(value)[:max_length]


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
                _request_id.set(old_value)
            elif key == 'user_id':
                _user_id.set(old_value)
            elif key == 'operation':
                _operation.set(old_value)
        return False


default_logger = setup_logger("comprehensive-assessment")


def get_logger(name: str = None) -> logging.Logger:
    """获取日志记录器
    
    Args:
        name: 日志记录器名称，如果为None则返回默认logger
        
    Returns:
        logging.Logger: 日志记录器实例
    """
    if name is None:
        return default_logger
    return logging.getLogger(name)


def log_business_event(event_type: str, details: Dict[str, Any], logger: logging.Logger = None):
    """记录业务事件
    
    Args:
        event_type: 事件类型
        details: 事件详情
        logger: 日志记录器
    """
    if logger is None:
        logger = default_logger
    
    logger.info(
        f"[业务事件] {event_type}",
        extra={'extra_data': details}
    )


def log_data_flow(step: str, data: Any, logger: logging.Logger = None):
    """记录数据流
    
    Args:
        step: 处理步骤
        data: 数据内容
        logger: 日志记录器
    """
    if logger is None:
        logger = default_logger
    
    sanitized = _sanitize_value(data, max_length=500)
    logger.debug(f"[数据流] {step} | 数据: {sanitized}")


def log_branch_decision(branch_name: str, condition: bool, context: str = "", logger: logging.Logger = None):
    """记录分支判断
    
    Args:
        branch_name: 分支名称
        condition: 判断结果
        context: 上下文信息
        logger: 日志记录器
    """
    if logger is None:
        logger = default_logger
    
    logger.debug(f"[分支判断] {context} | 分支: {branch_name} | 结果: {condition}")
