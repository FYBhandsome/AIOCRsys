#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一日志配置模块
================

功能描述:
    提供集中化的日志管理，支持多种输出格式、异步写入、日志轮转和敏感数据过滤。

特性:
    1. 分级日志管理 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    2. 请求追踪 (Request ID)
    3. 用户上下文
    4. 性能监控
    5. 敏感数据过滤
    6. 日志轮转与归档
    7. 结构化日志输出
    8. 异步日志写入
    9. 统一输出目录

使用方法:
    from shared_utils.unified_logger import get_logger, setup_logging
    
    setup_logging(service_name="visual_model", log_level="INFO")
    logger = get_logger(__name__)
    logger.info("操作成功", extra={"user_id": "123", "operation": "login"})

作者: 综测计算助手开发团队
版本: 1.0
"""

import logging
import logging.handlers
import sys
import os
import re
import json
import traceback
import uuid
import contextvars
import time
import threading
import asyncio
import atexit
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Callable
from functools import wraps
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
from queue import Queue, Empty


PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
UNIFIED_LOG_DIR = PROJECT_ROOT / "logs"

_log_lock = threading.Lock()
_logging_initialized = False
_async_handler = None

_request_id: contextvars.ContextVar[str] = contextvars.ContextVar('request_id', default='')
_user_id: contextvars.ContextVar[str] = contextvars.ContextVar('user_id', default='')
_session_id: contextvars.ContextVar[str] = contextvars.ContextVar('session_id', default='')
_operation: contextvars.ContextVar[str] = contextvars.ContextVar('operation', default='')


class LogLevel(Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


SENSITIVE_PATTERNS = [
    r'api[_-]?key',
    r'password',
    r'secret',
    r'token',
    r'credential',
    r'auth',
    r'private[_-]?key',
    r'access[_-]?key',
    r'authorization',
    r'cookie',
]

SENSITIVE_REPLACEMENT = "******"


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


def set_session_id(session_id: str) -> None:
    """设置当前会话ID"""
    _session_id.set(str(session_id) if session_id else '')


def get_session_id() -> str:
    """获取当前会话ID"""
    return _session_id.get()


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


def mask_sensitive_data(data: Any, max_length: int = 200) -> str:
    """过滤敏感数据"""
    if data is None:
        return "None"
    
    data_str = str(data)
    if len(data_str) > max_length:
        data_str = data_str[:max_length] + "..."
    
    for pattern in SENSITIVE_PATTERNS:
        if re.search(pattern, data_str, re.IGNORECASE):
            return SENSITIVE_REPLACEMENT
    
    return data_str


def mask_dict(data: Dict[str, Any], sensitive_keys: List[str] = None) -> Dict[str, Any]:
    """过滤字典中的敏感数据"""
    if not isinstance(data, dict):
        return data
    
    sensitive_keys = sensitive_keys or [
        'api_key', 'password', 'secret', 'token', 'api_secret',
        'authorization', 'cookie', 'private_key', 'access_key'
    ]
    result = {}
    
    for key, value in data.items():
        key_lower = key.lower()
        is_sensitive = any(sk in key_lower for sk in sensitive_keys)
        
        if is_sensitive:
            result[key] = SENSITIVE_REPLACEMENT
        elif isinstance(value, dict):
            result[key] = mask_dict(value, sensitive_keys)
        elif isinstance(value, str) and len(value) > 200:
            result[key] = value[:200] + "..."
        else:
            result[key] = value
    
    return result


class MillisecondFormatter(logging.Formatter):
    """支持毫秒级时间戳的格式化器"""
    
    def formatTime(self, record, datefmt=None):
        ct = datetime.fromtimestamp(record.created)
        if datefmt:
            s = ct.strftime(datefmt)
        else:
            s = ct.strftime("%Y-%m-%d %H:%M:%S")
        s = f"{s}.{int(record.created % 1 * 1000):03d}"
        return s


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
            "thread": record.threadName,
        }
        
        request_id = get_request_id()
        if request_id:
            log_data["request_id"] = request_id
        
        user_id = get_user_id()
        if user_id:
            log_data["user_id"] = user_id
        
        session_id = get_session_id()
        if session_id:
            log_data["session_id"] = session_id
        
        operation = get_operation()
        if operation:
            log_data["operation"] = operation
        
        if hasattr(record, 'params') and record.params:
            log_data["params"] = mask_dict(record.params) if isinstance(record.params, dict) else str(record.params)
        
        if hasattr(record, 'duration_ms'):
            log_data["duration_ms"] = record.duration_ms
        
        if hasattr(record, 'status'):
            log_data["status"] = record.status
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            log_data["exception_type"] = record.exc_info[0].__name__ if record.exc_info[0] else None
        
        if hasattr(record, 'extra_data'):
            log_data["extra"] = mask_dict(record.extra_data)
        
        return json.dumps(log_data, ensure_ascii=False)


class ColoredFormatter(MillisecondFormatter):
    """彩色控制台日志格式化器"""
    
    COLORS = {
        'DEBUG': '\033[36m',
        'INFO': '\033[32m',
        'WARNING': '\033[33m',
        'ERROR': '\033[31m',
        'CRITICAL': '\033[35m',
    }
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
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
        
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname:8s}{self.RESET}"
        
        original_msg = record.getMessage()
        if context_str:
            record.msg = f"{self.DIM}{context_str}{self.RESET} {original_msg}"
            record.args = ()
        
        return super().format(record)


class AsyncFileHandler(logging.Handler):
    """
    异步文件日志处理器
    
    使用后台线程异步写入日志，避免阻塞主线程。
    """
    
    def __init__(self, filename: Path, mode: str = 'a', encoding: str = 'utf-8'):
        super().__init__()
        self.filename = filename
        self.mode = mode
        self.encoding = encoding
        self.queue = Queue(maxsize=10000)
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="log_writer")
        self._stop_event = threading.Event()
        self._file = None
        self._write_thread = None
        self._buffer = []
        self._buffer_size = 100
        self._last_flush = time.time()
        self._flush_interval = 1.0
        
        self._ensure_dir()
        self._start_writer()
        atexit.register(self.close)
    
    def _ensure_dir(self):
        """确保日志目录存在"""
        try:
            self.filename.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            sys.stderr.write(f"[LOG ERROR] 无法创建日志目录: {e}\n")
    
    def _start_writer(self):
        """启动写入线程"""
        self._write_thread = threading.Thread(target=self._write_loop, daemon=True)
        self._write_thread.start()
    
    def _write_loop(self):
        """写入循环"""
        try:
            self._file = open(self.filename, self.mode, encoding=self.encoding)
        except Exception as e:
            sys.stderr.write(f"[LOG ERROR] 无法打开日志文件: {e}\n")
            return
        
        while not self._stop_event.is_set():
            try:
                record = self.queue.get(timeout=0.1)
                if record is None:
                    continue
                
                self._buffer.append(record)
                
                current_time = time.time()
                should_flush = (
                    len(self._buffer) >= self._buffer_size or
                    current_time - self._last_flush >= self._flush_interval
                )
                
                if should_flush:
                    self._flush_buffer()
                    
            except Empty:
                if self._buffer:
                    self._flush_buffer()
            except Exception as e:
                sys.stderr.write(f"[LOG ERROR] 日志写入错误: {e}\n")
        
        if self._buffer:
            self._flush_buffer()
        
        if self._file and not self._file.closed:
            try:
                self._file.close()
            except Exception:
                pass
    
    def _flush_buffer(self):
        """刷新缓冲区"""
        if not self._buffer or not self._file:
            return
        
        try:
            if self._file.closed:
                return
            for record in self._buffer:
                self._file.write(record + '\n')
            self._file.flush()
            self._buffer.clear()
            self._last_flush = time.time()
        except OSError as e:
            if e.errno == 9:
                pass
            else:
                sys.stderr.write(f"[LOG ERROR] 刷新日志缓冲区失败: {e}\n")
        except Exception as e:
            sys.stderr.write(f"[LOG ERROR] 刷新日志缓冲区失败: {e}\n")
    
    def emit(self, record: logging.LogRecord):
        """发送日志记录"""
        try:
            msg = self.format(record)
            if not self.queue.full():
                self.queue.put(msg)
            else:
                sys.stderr.write("[LOG WARNING] 日志队列已满，丢弃日志\n")
        except Exception as e:
            sys.stderr.write(f"[LOG ERROR] 日志发送失败: {e}\n")
    
    def close(self):
        """关闭处理器"""
        self._stop_event.set()
        if self._write_thread and self._write_thread.is_alive():
            self._write_thread.join(timeout=5)
        super().close()


class SafeRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """安全的日志文件处理器"""
    
    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0,
                 encoding=None, delay=False, errors=None):
        self._file_error_logged = False
        self._fallback_mode = False
        
        try:
            super().__init__(filename, mode, maxBytes, backupCount, encoding, delay, errors)
        except PermissionError:
            self._handle_file_error(f"无法打开日志文件 {filename}，权限被拒绝")
            self._fallback_mode = True
        except Exception as e:
            self._handle_file_error(f"日志文件处理器初始化失败: {e}")
            self._fallback_mode = True
    
    def _handle_file_error(self, error_msg: str):
        if not self._file_error_logged:
            sys.stderr.write(f"[LOG WARNING] {error_msg}\n")
            self._file_error_logged = True
    
    def emit(self, record):
        if self._fallback_mode:
            return
        
        try:
            with _log_lock:
                super().emit(record)
        except Exception as e:
            self._handle_file_error(f"日志写入错误: {e}")


def cleanup_old_logs(log_dir: Path, max_days: int = 30):
    """清理旧日志文件"""
    try:
        if not log_dir.exists():
            return
        
        cutoff_date = datetime.now() - timedelta(days=max_days)
        
        for log_file in log_dir.glob("*.log*"):
            try:
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    log_file.unlink()
            except Exception:
                pass
    except Exception:
        pass


def setup_logging(
    service_name: str = "app",
    log_level: str = "INFO",
    log_dir: Path = None,
    log_format: str = "console",
    enable_file: bool = True,
    enable_async: bool = True,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 10,
    enable_json: bool = False,
    use_subdir: bool = True
) -> logging.Logger:
    """
    配置应用日志
    
    Args:
        service_name: 服务名称，用于区分不同服务的日志
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: 日志目录，默认为项目根目录下的 logs 文件夹
        log_format: 日志格式 (console, json, simple)
        enable_file: 是否启用文件日志
        enable_async: 是否启用异步文件写入
        max_bytes: 单个日志文件最大大小
        backup_count: 保留的日志文件数量
        enable_json: 是否启用 JSON 格式日志
        use_subdir: 是否为每个服务创建子目录
        
    Returns:
        配置好的根日志器
    """
    global _logging_initialized, _async_handler
    
    if _logging_initialized:
        return logging.getLogger()
    
    if log_dir is None:
        if use_subdir:
            log_dir = UNIFIED_LOG_DIR / service_name
        else:
            log_dir = UNIFIED_LOG_DIR
    
    log_dir = Path(log_dir)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    root_logger.handlers.clear()
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    if enable_json or log_format == "json":
        console_handler.setFormatter(JsonFormatter())
    elif log_format == "console":
        console_formatter = ColoredFormatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(console_formatter)
    else:
        console_handler.setFormatter(MillisecondFormatter(
            fmt="%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))
    
    root_logger.addHandler(console_handler)
    
    if enable_file:
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            
            cleanup_old_logs(log_dir, max_days=30)
            
            today = datetime.now().strftime("%Y-%m-%d")
            log_file = log_dir / f"{service_name}_{today}.log"
            
            if enable_async:
                file_handler = AsyncFileHandler(log_file)
                file_handler.setLevel(logging.DEBUG)
                file_handler.setFormatter(MillisecondFormatter(
                    fmt="%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)s:%(lineno)d | %(funcName)s | %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S"
                ))
            else:
                file_handler = SafeRotatingFileHandler(
                    log_file,
                    maxBytes=max_bytes,
                    backupCount=backup_count,
                    encoding='utf-8',
                    delay=True
                )
                file_handler.setLevel(logging.DEBUG)
                file_handler.setFormatter(MillisecondFormatter(
                    fmt="%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)s:%(lineno)d | %(funcName)s | %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S"
                ))
            
            root_logger.addHandler(file_handler)
            
            error_log_file = log_dir / f"{service_name}_error_{today}.log"
            
            if enable_async:
                error_handler = AsyncFileHandler(error_log_file)
                error_handler.setLevel(logging.ERROR)
                error_handler.setFormatter(MillisecondFormatter(
                    fmt="%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)s:%(lineno)d | %(funcName)s | %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S"
                ))
            else:
                error_handler = SafeRotatingFileHandler(
                    error_log_file,
                    maxBytes=max_bytes,
                    backupCount=backup_count,
                    encoding='utf-8',
                    delay=True
                )
                error_handler.setLevel(logging.ERROR)
                error_handler.setFormatter(MillisecondFormatter(
                    fmt="%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)s:%(lineno)d | %(funcName)s | %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S"
                ))
            
            root_logger.addHandler(error_handler)
            
        except Exception as e:
            sys.stderr.write(f"[LOG WARNING] 日志文件初始化失败: {e}，仅使用控制台输出\n")
    
    for lib in ["httpx", "httpcore", "chromadb", "sentence_transformers",
                "urllib3", "requests", "werkzeug", "uvicorn", "fastapi"]:
        logging.getLogger(lib).setLevel(logging.WARNING)
    
    _logging_initialized = True
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志器"""
    return logging.getLogger(name)


class LogContext:
    """日志上下文管理器"""
    
    def __init__(
        self,
        logger: logging.Logger,
        operation: str,
        params: Dict[str, Any] = None,
        log_entry: bool = True,
        log_exit: bool = True
    ):
        self.logger = logger
        self.operation = operation
        self.params = mask_dict(params) if params else {}
        self.log_entry = log_entry
        self.log_exit = log_exit
        self.start_time = None
        self.status = "running"
    
    def __enter__(self):
        self.start_time = time.time()
        set_operation(self.operation)
        if self.log_entry:
            self.logger.info(
                f"[{self.operation}] 开始执行",
                extra={'params': self.params}
            )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = int((time.time() - self.start_time) * 1000)
        
        if exc_type is not None:
            self.status = "failed"
            if self.log_exit:
                self.logger.error(
                    f"[{self.operation}] 执行失败: {exc_val}",
                    extra={'params': self.params, 'duration_ms': duration_ms, 'status': 'failed'},
                    exc_info=True
                )
        else:
            self.status = "success"
            if self.log_exit:
                self.logger.info(
                    f"[{self.operation}] 执行成功",
                    extra={'params': self.params, 'duration_ms': duration_ms, 'status': 'success'}
                )
        
        set_operation('')
        return False


def log_function_call(logger: logging.Logger = None, level: str = "INFO"):
    """函数调用日志装饰器"""
    def decorator(func):
        nonlocal logger
        if logger is None:
            logger = get_logger(func.__module__)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            func_name = func.__name__
            logger.debug(f"[{func_name}] 调用开始")
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration_ms = int((time.time() - start_time) * 1000)
                getattr(logger, level.lower())(
                    f"[{func_name}] 执行成功",
                    extra={'duration_ms': duration_ms, 'status': 'success'}
                )
                return result
            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                logger.error(
                    f"[{func_name}] 执行失败: {type(e).__name__}: {e}",
                    extra={'duration_ms': duration_ms, 'status': 'failed'},
                    exc_info=True
                )
                raise
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            func_name = func.__name__
            logger.debug(f"[{func_name}] 调用开始")
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration_ms = int((time.time() - start_time) * 1000)
                getattr(logger, level.lower())(
                    f"[{func_name}] 执行成功",
                    extra={'duration_ms': duration_ms, 'status': 'success'}
                )
                return result
            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                logger.error(
                    f"[{func_name}] 执行失败: {type(e).__name__}: {e}",
                    extra={'duration_ms': duration_ms, 'status': 'failed'},
                    exc_info=True
                )
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def log_business_event(logger: logging.Logger, event_type: str, details: Dict[str, Any] = None):
    """记录业务事件"""
    logger.info(
        f"[业务事件] {event_type}",
        extra={'event_type': event_type, 'details': mask_dict(details or {})}
    )


def log_api_request(logger: logging.Logger, method: str, path: str, 
                    status_code: int, duration_ms: int, user_id: str = None):
    """记录API请求"""
    level = "INFO" if status_code < 400 else "WARNING" if status_code < 500 else "ERROR"
    getattr(logger, level.lower())(
        f"[API] {method} {path} -> {status_code}",
        extra={
            'method': method,
            'path': path,
            'status_code': status_code,
            'duration_ms': duration_ms,
            'user_id': user_id or get_user_id()
        }
    )


def log_data_flow(logger: logging.Logger, source: str, destination: str, 
                  data_type: str, record_count: int = None):
    """记录数据流向"""
    logger.info(
        f"[数据流] {source} -> {destination} ({data_type})",
        extra={
            'source': source,
            'destination': destination,
            'data_type': data_type,
            'record_count': record_count
        }
    )


def log_branch_decision(logger: logging.Logger, branch_name: str, 
                        condition: str, result: bool):
    """记录分支决策"""
    logger.debug(
        f"[分支决策] {branch_name}: {condition} -> {result}",
        extra={'branch': branch_name, 'condition': condition, 'result': result}
    )


__all__ = [
    'setup_logging',
    'get_logger',
    'set_request_id',
    'get_request_id',
    'set_user_id',
    'get_user_id',
    'set_session_id',
    'get_session_id',
    'set_operation',
    'get_operation',
    'clear_context',
    'mask_sensitive_data',
    'mask_dict',
    'LogContext',
    'log_function_call',
    'log_business_event',
    'log_api_request',
    'log_data_flow',
    'log_branch_decision',
    'LogLevel',
    'UNIFIED_LOG_DIR',
]
