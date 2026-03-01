"""
统一的日志配置模块
提供集中化的日志管理，支持多种输出格式、日志轮转和敏感数据过滤

特性:
- 分级日志管理 (DEBUG, INFO, WARNING, ERROR, CRITICAL/FATAL)
- 请求追踪 (Request ID)
- 用户上下文
- 性能监控
- 敏感数据过滤
- 日志轮转与归档
- 结构化日志输出
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
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Callable
from functools import wraps
from dataclasses import dataclass, field
from enum import Enum
import time
import threading
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
UNIFIED_LOG_DIR = PROJECT_ROOT / "logs" / "rag"


class LogLevel(Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    FATAL = "FATAL"


SENSITIVE_PATTERNS = [
    r'api[_-]?key',
    r'password',
    r'secret',
    r'token',
    r'credential',
    r'auth',
    r'private[_-]?key',
    r'access[_-]?key',
]

SENSITIVE_REPLACEMENT = "******"

_log_lock = threading.Lock()

_request_id: contextvars.ContextVar[str] = contextvars.ContextVar('request_id', default='')
_user_id: contextvars.ContextVar[str] = contextvars.ContextVar('user_id', default='')
_session_id: contextvars.ContextVar[str] = contextvars.ContextVar('session_id', default='')


def set_request_id(request_id: str = None) -> str:
    """设置当前请求ID
    
    Args:
        request_id: 请求ID，如果为None则自动生成
        
    Returns:
        设置的请求ID
    """
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


def clear_context() -> None:
    """清除所有上下文变量"""
    _request_id.set('')
    _user_id.set('')
    _session_id.set('')


def mask_sensitive_data(data: Any, max_length: int = 100) -> str:
    """过滤敏感数据
    
    Args:
        data: 要过滤的数据
        max_length: 最大显示长度
        
    Returns:
        过滤后的字符串
    """
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
    """过滤字典中的敏感数据
    
    Args:
        data: 要过滤的字典
        sensitive_keys: 敏感键名列表
        
    Returns:
        过滤后的字典
    """
    if not isinstance(data, dict):
        return data
    
    sensitive_keys = sensitive_keys or ['api_key', 'password', 'secret', 'token', 'api_secret']
    result = {}
    
    for key, value in data.items():
        if key.lower() in [k.lower() for k in sensitive_keys]:
            result[key] = SENSITIVE_REPLACEMENT
        elif isinstance(value, dict):
            result[key] = mask_dict(value, sensitive_keys)
        elif isinstance(value, str) and len(value) > 100:
            result[key] = value[:100] + "..."
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
    """JSON格式的日志格式化器，支持请求追踪和上下文信息"""
    
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
        
        if hasattr(record, 'operation'):
            log_data["operation"] = record.operation
            
        return json.dumps(log_data, ensure_ascii=False)


class ColoredFormatter(MillisecondFormatter):
    """彩色控制台日志格式化器，支持请求追踪和上下文信息"""
    
    COLORS = {
        'DEBUG': '\033[36m',
        'INFO': '\033[32m',
        'WARNING': '\033[33m',
        'ERROR': '\033[31m',
        'CRITICAL': '\033[35m',
        'FATAL': '\033[35m',
    }
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    def format(self, record: logging.LogRecord) -> str:
        request_id = get_request_id()
        user_id = get_user_id()
        
        context_parts = []
        if request_id:
            context_parts.append(f"rid={request_id[:8]}")
        if user_id:
            context_parts.append(f"uid={user_id}")
        
        context_str = f" [{', '.join(context_parts)}]" if context_parts else ""
        
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname:8s}{self.RESET}"
        
        original_msg = record.getMessage()
        if context_str:
            record.msg = f"{self.DIM}{context_str}{self.RESET} {original_msg}"
            record.args = ()
        
        if hasattr(record, 'status'):
            status = record.status
            if status == 'success':
                record.status = f"\033[32m[SUCCESS]\033[0m"
            elif status == 'failed':
                record.status = f"\033[31m[FAILED]\033[0m"
            else:
                record.status = f"\033[33m[{status.upper()}]\033[0m"
        
        return super().format(record)


class SafeRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """安全的日志文件处理器，支持错误恢复和降级"""
    
    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0, 
                 encoding=None, delay=False, errors=None):
        self._file_error_logged = False
        self._fallback_mode = False
        self._last_error_time = 0
        self._error_count = 0
        self._max_errors = 5
        self._error_cooldown = 60
        
        try:
            super().__init__(filename, mode, maxBytes, backupCount, encoding, delay, errors)
        except PermissionError:
            self._handle_file_error(f"无法打开日志文件 {filename}，权限被拒绝")
            self._fallback_mode = True
        except Exception as e:
            self._handle_file_error(f"日志文件处理器初始化失败: {e}")
            self._fallback_mode = True
    
    def _handle_file_error(self, error_msg: str):
        """处理文件错误"""
        current_time = time.time()
        
        if current_time - self._last_error_time > self._error_cooldown:
            self._error_count = 0
        
        self._error_count += 1
        self._last_error_time = current_time
        
        if self._error_count >= self._max_errors:
            self._fallback_mode = True
        
        if not self._file_error_logged:
            sys.stderr.write(f"[LOG WARNING] {error_msg}\n")
            self._file_error_logged = True
    
    def emit(self, record):
        """安全地发送日志记录"""
        if self._fallback_mode:
            return
        
        try:
            with _log_lock:
                super().emit(record)
        except PermissionError:
            self._handle_file_error("日志文件权限错误，跳过文件写入")
        except Exception as e:
            self._handle_file_error(f"日志写入错误: {e}")
    
    def shouldRollover(self, record):
        """安全地检查是否需要轮转"""
        if self._fallback_mode:
            return False
        
        try:
            return super().shouldRollover(record)
        except Exception:
            return False
    
    def doRollover(self):
        """安全地执行轮转"""
        if self._fallback_mode:
            return
        
        try:
            with _log_lock:
                super().doRollover()
        except PermissionError:
            self._handle_file_error("日志轮转权限错误")
            self._fallback_mode = True
        except Exception as e:
            self._handle_file_error(f"日志轮转错误: {e}")


class LogConfig:
    """日志配置"""
    
    DEFAULT_LOG_DIR = str(UNIFIED_LOG_DIR)
    DEFAULT_LOG_LEVEL = "INFO"
    DEFAULT_MAX_BYTES = 10 * 1024 * 1024
    DEFAULT_BACKUP_COUNT = 10
    
    LOG_LEVELS = {
        'dev': 'DEBUG',
        'development': 'DEBUG',
        'test': 'INFO',
        'testing': 'INFO',
        'prod': 'WARNING',
        'production': 'WARNING',
    }
    
    @classmethod
    def get_log_level(cls, env: str = None) -> str:
        """根据环境获取日志级别"""
        env = env or os.getenv('APP_ENV', 'development')
        return cls.LOG_LEVELS.get(env.lower(), cls.DEFAULT_LOG_LEVEL)


def cleanup_old_logs(log_dir: str, max_days: int = 30):
    """清理旧日志文件
    
    Args:
        log_dir: 日志目录
        max_days: 保留天数
    """
    try:
        log_path = Path(log_dir)
        if not log_path.exists():
            return
        
        cutoff_date = datetime.now() - timedelta(days=max_days)
        
        for log_file in log_path.glob("*.log*"):
            try:
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    log_file.unlink()
            except Exception:
                pass
    except Exception:
        pass


def setup_logging(
    log_level: str = None,
    log_dir: str = None,
    log_format: str = "console",
    enable_file: bool = True,
    max_bytes: int = None,
    backup_count: int = None,
    env: str = None
) -> logging.Logger:
    """配置应用日志
    
    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: 日志目录
        log_format: 日志格式 (console, json, simple)
        enable_file: 是否启用文件日志
        max_bytes: 单个日志文件最大大小
        backup_count: 保留的日志文件数量
        
    Returns:
        配置好的根日志器
    """
    if log_level is None:
        log_level = LogConfig.get_log_level(env)
    
    if log_dir is None:
        log_dir = LogConfig.DEFAULT_LOG_DIR
    
    if max_bytes is None:
        max_bytes = LogConfig.DEFAULT_MAX_BYTES
    
    if backup_count is None:
        backup_count = LogConfig.DEFAULT_BACKUP_COUNT
    
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    root_logger.handlers.clear()
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    if log_format == "json":
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
        file_handlers_added = False
        
        try:
            log_path = Path(log_dir)
            log_path.mkdir(parents=True, exist_ok=True)
            
            cleanup_old_logs(log_dir, max_days=30)
            
            today = datetime.now().strftime("%Y-%m-%d")
            log_file = log_path / f"app_{today}.log"
            
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
            
            error_log_file = log_path / f"error_{today}.log"
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
            
            file_handlers_added = True
            
        except PermissionError as e:
            sys.stderr.write(f"[LOG WARNING] 无法创建日志文件目录: {e}，仅使用控制台输出\n")
        except Exception as e:
            sys.stderr.write(f"[LOG WARNING] 日志文件初始化失败: {e}，仅使用控制台输出\n")
        
        if not file_handlers_added:
            sys.stderr.write("[LOG INFO] 日志将仅输出到控制台\n")
    
    for lib in ["httpx", "httpcore", "chromadb", "sentence_transformers", 
                "urllib3", "requests", "werkzeug"]:
        logging.getLogger(lib).setLevel(logging.WARNING)
    
    return root_logger


_logging_initialized = False

def ensure_logging_initialized():
    """确保日志系统已初始化"""
    global _logging_initialized
    if not _logging_initialized:
        setup_logging()
        _logging_initialized = True


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志器
    
    Args:
        name: 日志器名称
        
    Returns:
        日志器实例
    """
    ensure_logging_initialized()
    return logging.getLogger(name)


class LogContext:
    """日志上下文管理器，用于记录函数执行"""
    
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
        
        return False
    
    def log(self, level: str, message: str, **kwargs):
        """记录日志"""
        log_func = getattr(self.logger, level.lower(), self.logger.info)
        log_func(f"[{self.operation}] {message}", extra={'params': kwargs})


def log_function(
    logger: logging.Logger = None,
    level: str = "INFO",
    log_params: bool = True,
    log_result: bool = False
):
    """函数日志装饰器
    
    Args:
        logger: 日志器实例
        level: 日志级别
        log_params: 是否记录参数
        log_result: 是否记录返回值
    """
    def decorator(func):
        nonlocal logger
        if logger is None:
            logger = get_logger(func.__module__)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            
            params = {}
            if log_params:
                import inspect
                sig = inspect.signature(func)
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                params = mask_dict(dict(bound.arguments))
            
            logger.debug(f"[{func_name}] 调用开始", extra={'params': params})
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration_ms = int((time.time() - start_time) * 1000)
                
                result_info = ""
                if log_result and result is not None:
                    if isinstance(result, dict):
                        result_info = f" -> {mask_dict(result)}"
                    elif isinstance(result, (list, tuple)):
                        result_info = f" -> {type(result).__name__}[{len(result)}]"
                    else:
                        result_info = f" -> {type(result).__name__}"
                
                getattr(logger, level.lower())(
                    f"[{func_name}] 执行成功{result_info}",
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
        
        return wrapper
    return decorator


class RAGLogger:
    """RAG系统专用日志器"""
    
    def __init__(self, name: str = "rag"):
        self.logger = get_logger(name)
    
    def log_query(self, query: str, intent: Dict[str, Any] = None):
        """记录查询日志"""
        self.logger.info(
            f"收到查询请求",
            extra={
                'params': {
                    'query': query[:100] + "..." if len(query) > 100 else query,
                    'intent': intent
                }
            }
        )
    
    def log_retrieval(
        self,
        query: str,
        filter_conditions: Dict[str, Any],
        result_count: int,
        duration_ms: int
    ):
        """记录检索日志"""
        self.logger.info(
            f"检索完成: 返回{result_count}条结果",
            extra={
                'params': {
                    'query': query[:50] if len(query) > 50 else query,
                    'filter': filter_conditions
                },
                'duration_ms': duration_ms,
                'result_count': result_count,
                'status': 'success'
            }
        )
    
    def log_rerank(
        self,
        input_count: int,
        output_count: int,
        top_score: float,
        duration_ms: int
    ):
        """记录重排日志"""
        self.logger.debug(
            f"重排完成: {input_count} -> {output_count}条, 最高分: {top_score:.3f}",
            extra={
                'duration_ms': duration_ms,
                'input_count': input_count,
                'output_count': output_count,
                'top_score': top_score
            }
        )
    
    def log_competition_match(
        self,
        input_name: str,
        matched_name: str,
        match_score: float,
        competition_type: str = None
    ):
        """记录竞赛匹配日志"""
        self.logger.info(
            f"竞赛名称匹配: '{input_name}' -> '{matched_name}' (分数: {match_score:.1f})",
            extra={
                'params': {
                    'input': input_name,
                    'matched': matched_name,
                    'type': competition_type
                },
                'match_score': match_score
            }
        )
    
    def log_document_load(
        self,
        source: str,
        doc_count: int,
        chunk_count: int,
        duration_ms: int
    ):
        """记录文档加载日志"""
        self.logger.info(
            f"文档加载完成: {doc_count}个文档, {chunk_count}个chunk",
            extra={
                'params': {'source': source},
                'duration_ms': duration_ms,
                'doc_count': doc_count,
                'chunk_count': chunk_count,
                'status': 'success'
            }
        )
    
    def log_error(
        self,
        operation: str,
        error: Exception,
        context: Dict[str, Any] = None
    ):
        """记录错误日志"""
        self.logger.error(
            f"[{operation}] 发生错误: {type(error).__name__}: {error}",
            extra={
                'params': mask_dict(context) if context else {},
                'status': 'failed'
            },
            exc_info=True
        )
    
    def log_performance(
        self,
        operation: str,
        duration_ms: int,
        details: Dict[str, Any] = None
    ):
        """记录性能日志"""
        level = logging.WARNING if duration_ms > 1000 else logging.DEBUG
        self.logger.log(
            level,
            f"[{operation}] 耗时: {duration_ms}ms",
            extra={
                'duration_ms': duration_ms,
                'params': details
            }
        )


class _RAGLoggerProxy:
    """RAGLogger延迟代理，避免模块导入时的循环依赖"""
    _instance = None
    
    def __getattr__(self, name):
        if self._instance is None:
            self._instance = RAGLogger()
        return getattr(self._instance, name)


rag_logger = _RAGLoggerProxy()


@dataclass
class PerformanceMetric:
    """性能指标数据类"""
    operation: str
    duration_ms: int
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = True
    details: Dict[str, Any] = field(default_factory=dict)


class PerformanceMonitor:
    """性能监控器，用于收集和分析性能指标"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._metrics: List[PerformanceMetric] = []
        self._metrics_lock = threading.Lock()
        self._max_metrics = 10000
        self._initialized = True
        self.logger = get_logger("performance_monitor")
    
    def record(self, operation: str, duration_ms: int, success: bool = True, details: Dict[str, Any] = None):
        """记录性能指标
        
        Args:
            operation: 操作名称
            duration_ms: 耗时（毫秒）
            success: 是否成功
            details: 详细信息
        """
        metric = PerformanceMetric(
            operation=operation,
            duration_ms=duration_ms,
            success=success,
            details=details or {}
        )
        
        with self._metrics_lock:
            self._metrics.append(metric)
            if len(self._metrics) > self._max_metrics:
                self._metrics = self._metrics[-self._max_metrics:]
    
    def get_stats(self, operation: str = None, last_n: int = 100) -> Dict[str, Any]:
        """获取性能统计
        
        Args:
            operation: 操作名称（可选，为None时统计所有操作）
            last_n: 最近N条记录
            
        Returns:
            统计信息字典
        """
        with self._metrics_lock:
            metrics = self._metrics[-last_n:] if last_n else self._metrics.copy()
        
        if operation:
            metrics = [m for m in metrics if m.operation == operation]
        
        if not metrics:
            return {"error": "没有找到匹配的性能指标"}
        
        durations = [m.duration_ms for m in metrics]
        success_count = sum(1 for m in metrics if m.success)
        
        return {
            "operation": operation or "all",
            "count": len(metrics),
            "success_rate": success_count / len(metrics) * 100 if metrics else 0,
            "avg_duration_ms": sum(durations) / len(durations),
            "min_duration_ms": min(durations),
            "max_duration_ms": max(durations),
            "p50_duration_ms": sorted(durations)[len(durations) // 2],
            "p95_duration_ms": sorted(durations)[int(len(durations) * 0.95)] if len(durations) > 1 else durations[0],
            "p99_duration_ms": sorted(durations)[int(len(durations) * 0.99)] if len(durations) > 1 else durations[0],
        }
    
    def get_slow_operations(self, threshold_ms: int = 1000, last_n: int = 50) -> List[Dict[str, Any]]:
        """获取慢操作列表
        
        Args:
            threshold_ms: 慢操作阈值（毫秒）
            last_n: 最近N条记录
            
        Returns:
            慢操作列表
        """
        with self._metrics_lock:
            metrics = self._metrics[-last_n:] if last_n else self._metrics.copy()
        
        slow_ops = [
            {
                "operation": m.operation,
                "duration_ms": m.duration_ms,
                "timestamp": m.timestamp.isoformat(),
                "success": m.success,
                "details": m.details
            }
            for m in metrics if m.duration_ms >= threshold_ms
        ]
        
        return sorted(slow_ops, key=lambda x: x["duration_ms"], reverse=True)
    
    def get_operations_summary(self) -> Dict[str, Dict[str, Any]]:
        """获取所有操作的摘要
        
        Returns:
            操作摘要字典
        """
        with self._metrics_lock:
            metrics = self._metrics.copy()
        
        operations = defaultdict(list)
        for m in metrics:
            operations[m.operation].append(m)
        
        summary = {}
        for op, op_metrics in operations.items():
            durations = [m.duration_ms for m in op_metrics]
            success_count = sum(1 for m in op_metrics if m.success)
            
            summary[op] = {
                "count": len(op_metrics),
                "success_rate": success_count / len(op_metrics) * 100 if op_metrics else 0,
                "avg_duration_ms": sum(durations) / len(durations),
                "max_duration_ms": max(durations),
                "min_duration_ms": min(durations),
            }
        
        return summary
    
    def clear(self):
        """清空性能指标"""
        with self._metrics_lock:
            self._metrics.clear()


performance_monitor = PerformanceMonitor()


class LogAnalyzer:
    """日志分析器，用于查询和分析日志文件"""
    
    def __init__(self, log_dir: str = None):
        self.log_dir = Path(log_dir or LogConfig.DEFAULT_LOG_DIR)
        self.logger = get_logger("log_analyzer")
    
    def search_logs(
        self,
        keyword: str = None,
        level: str = None,
        start_time: datetime = None,
        end_time: datetime = None,
        request_id: str = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """搜索日志
        
        Args:
            keyword: 关键词
            level: 日志级别
            start_time: 开始时间
            end_time: 结束时间
            request_id: 请求ID
            limit: 返回数量限制
            
        Returns:
            匹配的日志列表
        """
        results = []
        
        log_files = list(self.log_dir.glob("*.log"))
        if not log_files:
            return results
        
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if len(results) >= limit:
                            break
                        
                        parsed = self._parse_log_line(line)
                        if not parsed:
                            continue
                        
                        if keyword and keyword.lower() not in parsed.get("message", "").lower():
                            continue
                        
                        if level and parsed.get("level") != level.upper():
                            continue
                        
                        if request_id and parsed.get("request_id") != request_id:
                            continue
                        
                        if start_time or end_time:
                            log_time = parsed.get("timestamp")
                            if log_time:
                                try:
                                    log_dt = datetime.strptime(log_time[:19], "%Y-%m-%d %H:%M:%S")
                                    if start_time and log_dt < start_time:
                                        continue
                                    if end_time and log_dt > end_time:
                                        continue
                                except ValueError:
                                    pass
                        
                        parsed["file"] = str(log_file.name)
                        results.append(parsed)
                        
            except Exception as e:
                self.logger.warning(f"读取日志文件失败: {log_file}, {e}")
                continue
        
        return results
    
    def _parse_log_line(self, line: str) -> Optional[Dict[str, Any]]:
        """解析日志行
        
        Args:
            line: 日志行
            
        Returns:
            解析后的字典
        """
        line = line.strip()
        if not line:
            return None
        
        if line.startswith('{'):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                pass
        
        import re
        pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)\s*\|\s*(\w+)\s*\|\s*([^:]+):(\d+)\s*\|\s*(\w+)\s*\|\s*(.*)'
        match = re.match(pattern, line)
        
        if match:
            return {
                "timestamp": match.group(1),
                "level": match.group(2).strip(),
                "logger": match.group(3).strip(),
                "line": match.group(4),
                "function": match.group(5),
                "message": match.group(6)
            }
        
        return {"message": line}
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """获取错误摘要
        
        Args:
            hours: 最近N小时
            
        Returns:
            错误摘要字典
        """
        start_time = datetime.now() - timedelta(hours=hours)
        
        errors = self.search_logs(
            level="ERROR",
            start_time=start_time,
            limit=1000
        )
        
        errors.extend(self.search_logs(
            level="CRITICAL",
            start_time=start_time,
            limit=1000
        ))
        
        error_by_type = defaultdict(int)
        error_by_logger = defaultdict(int)
        error_by_message = defaultdict(int)
        
        for error in errors:
            error_by_type[error.get("level", "UNKNOWN")] += 1
            error_by_logger[error.get("logger", "unknown")] += 1
            
            msg = error.get("message", "")[:100]
            error_by_message[msg] += 1
        
        return {
            "total_errors": len(errors),
            "time_range_hours": hours,
            "by_type": dict(error_by_type),
            "by_logger": dict(error_by_logger),
            "top_messages": dict(sorted(error_by_message.items(), key=lambda x: x[1], reverse=True)[:10])
        }
    
    def get_request_trace(self, request_id: str) -> List[Dict[str, Any]]:
        """获取请求追踪日志
        
        Args:
            request_id: 请求ID
            
        Returns:
            该请求的所有日志
        """
        return self.search_logs(request_id=request_id, limit=500)


log_analyzer = LogAnalyzer()


def track_performance(operation: str):
    """性能追踪装饰器
    
    Args:
        operation: 操作名称
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise
            finally:
                duration_ms = int((time.time() - start_time) * 1000)
                performance_monitor.record(operation, duration_ms, success)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise
            finally:
                duration_ms = int((time.time() - start_time) * 1000)
                performance_monitor.record(operation, duration_ms, success)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    
    return decorator


class RequestContext:
    """请求上下文管理器，自动设置和清理请求上下文"""
    
    def __init__(self, request_id: str = None, user_id: str = None, session_id: str = None):
        self.request_id = request_id
        self.user_id = user_id
        self.session_id = session_id
        self._old_request_id = None
        self._old_user_id = None
        self._old_session_id = None
    
    def __enter__(self):
        self._old_request_id = get_request_id()
        self._old_user_id = get_user_id()
        self._old_session_id = get_session_id()
        
        if self.request_id:
            set_request_id(self.request_id)
        if self.user_id:
            set_user_id(self.user_id)
        if self.session_id:
            set_session_id(self.session_id)
        
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
        
        if self._old_session_id:
            set_session_id(self._old_session_id)
        else:
            _session_id.set('')
        
        return False
