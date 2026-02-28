#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版日志配置模块
提供完整的日志记录功能，支持控制台和文件输出
"""
import os
import sys
import logging
import re
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler, RotatingFileHandler
from pathlib import Path
from typing import Dict, Any, Optional, Set
from functools import wraps
import time
import traceback
import json


SENSITIVE_KEYS: Set[str] = {
    'password', 'passwd', 'pwd', 'secret', 'token', 'api_key', 'apikey',
    'authorization', 'auth', 'credential', 'private_key', 'access_token',
    'refresh_token', 'session_id', 'cookie', 'csrf_token'
}


def mask_sensitive_data(data: Any, mask: str = '******') -> Any:
    """遮蔽敏感数据"""
    if isinstance(data, dict):
        return {
            key: mask if key.lower() in SENSITIVE_KEYS else mask_sensitive_data(value, mask)
            for key, value in data.items()
        }
    elif isinstance(data, list):
        return [mask_sensitive_data(item, mask) for item in data]
    elif isinstance(data, str):
        for key in SENSITIVE_KEYS:
            if key in data.lower():
                return mask
        return data
    return data


def sanitize_for_logging(data: Any, max_length: int = 1000) -> str:
    """清理数据用于日志记录"""
    try:
        masked_data = mask_sensitive_data(data)
        json_str = json.dumps(masked_data, ensure_ascii=False, default=str)
        if len(json_str) > max_length:
            return json_str[:max_length] + "...[truncated]"
        return json_str
    except Exception:
        return str(data)[:max_length]


class MillisecondFormatter(logging.Formatter):
    """包含毫秒的时间格式化器"""
    
    def formatTime(self, record, datefmt=None):
        import time as time_module
        ct = self.converter(record.created)
        if datefmt:
            s = time_module.strftime(datefmt, ct)
        else:
            s = time_module.strftime("%Y-%m-%d %H:%M:%S", ct)
        s = f"{s}.{int(record.created % 1 * 1000):03d}"
        return s


class ColoredConsoleFormatter(MillisecondFormatter):
    """彩色控制台格式化器"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # 青色
        'INFO': '\033[32m',      # 绿色
        'WARNING': '\033[33m',   # 黄色
        'ERROR': '\033[31m',     # 红色
        'CRITICAL': '\033[35m',  # 紫色
    }
    RESET = '\033[0m'
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


class DetailedFileFormatter(MillisecondFormatter):
    """详细文件格式化器"""
    
    def format(self, record):
        record.extra_info = getattr(record, 'extra_info', '')
        return super().format(record)


class SensitiveDataFilter(logging.Filter):
    """敏感数据过滤器"""
    
    SENSITIVE_PATTERNS = [
        (re.compile(r'(password["\s:=]+)["\']?[^"\s,}]+', re.IGNORECASE), r'\1******'),
        (re.compile(r'(token["\s:=]+)["\']?[^"\s,}]+', re.IGNORECASE), r'\1******'),
        (re.compile(r'(secret["\s:=]+)["\']?[^"\s,}]+', re.IGNORECASE), r'\1******'),
        (re.compile(r'(api_key["\s:=]+)["\']?[^"\s,}]+', re.IGNORECASE), r'\1******'),
        (re.compile(r'Bearer\s+[A-Za-z0-9\-._~+/]+=*', re.IGNORECASE), 'Bearer ******'),
    ]
    
    def filter(self, record):
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            for pattern, replacement in self.SENSITIVE_PATTERNS:
                record.msg = pattern.sub(replacement, record.msg)
        return True


class EnhancedLogger:
    """增强版日志记录器"""
    
    _loggers: Dict[str, logging.Logger] = {}
    _initialized = False
    
    @classmethod
    def setup(
        cls,
        log_dir: str = "logs",
        app_name: str = "app",
        console_level: int = logging.INFO,
        file_level: int = logging.DEBUG,
        max_file_size: int = 100 * 1024 * 1024,
        backup_count: int = 30,
        enable_console: bool = True,
        enable_file: bool = True
    ) -> None:
        """设置日志配置"""
        if cls._initialized:
            return
        
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        root_logger.handlers.clear()
        
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(console_level)
            console_format = ColoredConsoleFormatter(
                fmt="%(asctime)s [%(levelname)s] %(name)s.%(funcName)s: %(message)s"
            )
            console_handler.setFormatter(console_format)
            console_handler.addFilter(SensitiveDataFilter())
            root_logger.addHandler(console_handler)
        
        if enable_file:
            log_file = log_path / f"{app_name}.log"
            file_handler = RotatingFileHandler(
                filename=str(log_file),
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(file_level)
            file_format = DetailedFileFormatter(
                fmt="%(asctime)s [%(levelname)s] %(name)s.%(funcName)s:%(lineno)d - %(message)s"
            )
            file_handler.setFormatter(file_format)
            file_handler.addFilter(SensitiveDataFilter())
            root_logger.addHandler(file_handler)
            
            error_file = log_path / f"{app_name}_error.log"
            error_handler = RotatingFileHandler(
                filename=str(error_file),
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(file_format)
            error_handler.addFilter(SensitiveDataFilter())
            root_logger.addHandler(error_handler)
        
        cls._initialized = True
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """获取日志记录器"""
        if not cls._initialized:
            cls.setup()
        
        if name not in cls._loggers:
            cls._loggers[name] = logging.getLogger(name)
        
        return cls._loggers[name]


def get_logger(name: str = __name__) -> logging.Logger:
    """获取日志记录器"""
    return EnhancedLogger.get_logger(name)


def log_function_call(logger: logging.Logger = None, level: int = logging.INFO):
    """函数调用日志装饰器"""
    def decorator(func):
        nonlocal logger
        if logger is None:
            logger = get_logger(func.__module__)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            func_name = func.__qualname__
            logger.log(level, f"[进入函数] {func_name}, 参数: args={sanitize_for_logging(args)}, kwargs={sanitize_for_logging(kwargs)}")
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                elapsed = (time.time() - start_time) * 1000
                logger.log(level, f"[退出函数] {func_name}, 耗时: {elapsed:.2f}ms, 返回: {sanitize_for_logging(result)[:500]}")
                return result
            except Exception as e:
                elapsed = (time.time() - start_time) * 1000
                logger.error(f"[函数异常] {func_name}, 耗时: {elapsed:.2f}ms, 异常: {type(e).__name__}: {str(e)}\n{traceback.format_exc()}")
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            func_name = func.__qualname__
            logger.log(level, f"[进入函数] {func_name}, 参数: args={sanitize_for_logging(args)}, kwargs={sanitize_for_logging(kwargs)}")
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = (time.time() - start_time) * 1000
                logger.log(level, f"[退出函数] {func_name}, 耗时: {elapsed:.2f}ms, 返回: {sanitize_for_logging(result)[:500]}")
                return result
            except Exception as e:
                elapsed = (time.time() - start_time) * 1000
                logger.error(f"[函数异常] {func_name}, 耗时: {elapsed:.2f}ms, 异常: {type(e).__name__}: {str(e)}\n{traceback.format_exc()}")
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


class APILogMiddleware:
    """API日志中间件基类"""
    
    def __init__(self, logger_name: str = "api"):
        self.logger = get_logger(logger_name)
    
    def log_request(self, method: str, path: str, headers: dict, query_params: dict, body: Any = None):
        """记录请求日志"""
        self.logger.info(
            f"[API请求] {method} {path} | "
            f"查询参数: {sanitize_for_logging(query_params)} | "
            f"请求头: {sanitize_for_logging(dict(headers))} | "
            f"请求体: {sanitize_for_logging(body)}"
        )
    
    def log_response(self, method: str, path: str, status_code: int, elapsed_ms: float, response_summary: str = None):
        """记录响应日志"""
        level = logging.INFO if status_code < 400 else logging.WARNING if status_code < 500 else logging.ERROR
        self.logger.log(
            level,
            f"[API响应] {method} {path} | 状态码: {status_code} | 耗时: {elapsed_ms:.2f}ms"
            f"{f' | 响应摘要: {response_summary[:200]}' if response_summary else ''}"
        )
    
    def log_error(self, method: str, path: str, error: Exception, extra_info: dict = None):
        """记录错误日志"""
        self.logger.error(
            f"[API错误] {method} {path} | 异常类型: {type(error).__name__} | "
            f"异常信息: {str(error)} | 额外信息: {sanitize_for_logging(extra_info)}\n"
            f"堆栈跟踪:\n{traceback.format_exc()}"
        )
    
    def log_business_operation(self, operation: str, details: dict, result: str = None):
        """记录业务操作日志"""
        self.logger.info(
            f"[业务操作] {operation} | 详情: {sanitize_for_logging(details)}"
            f"{f' | 结果: {result}' if result else ''}"
        )
    
    def log_variable(self, var_name: str, var_value: Any, context: str = ""):
        """记录变量日志"""
        self.logger.debug(
            f"[变量记录] {context} | 变量名: {var_name} | 值: {sanitize_for_logging(var_value)}"
        )
    
    def log_branch(self, branch_name: str, condition_result: bool, context: str = ""):
        """记录分支日志"""
        self.logger.info(
            f"[分支判断] {context} | 分支: {branch_name} | 条件结果: {condition_result}"
        )


def setup_logging(
    log_dir: str = "logs",
    app_name: str = "app",
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG
) -> None:
    """初始化日志配置"""
    EnhancedLogger.setup(
        log_dir=log_dir,
        app_name=app_name,
        console_level=console_level,
        file_level=file_level
    )


class ContextLogger:
    """上下文日志记录器"""
    
    def __init__(self, name: str, context_id: str = None):
        self.logger = get_logger(name)
        self.context_id = context_id or datetime.now().strftime("%Y%m%d%H%M%S%f")
    
    def _format_msg(self, msg: str) -> str:
        return f"[{self.context_id}] {msg}"
    
    def info(self, msg: str, *args, **kwargs):
        self.logger.info(self._format_msg(msg), *args, **kwargs)
    
    def debug(self, msg: str, *args, **kwargs):
        self.logger.debug(self._format_msg(msg), *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        self.logger.warning(self._format_msg(msg), *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs):
        self.logger.error(self._format_msg(msg), *args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs):
        self.logger.critical(self._format_msg(msg), *args, **kwargs)


def create_context_logger(name: str, context_id: str = None) -> ContextLogger:
    """创建上下文日志记录器"""
    return ContextLogger(name, context_id)
