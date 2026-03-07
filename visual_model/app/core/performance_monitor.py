#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能监控装饰器模块

提供函数级别的性能监控功能：
- 执行时间统计
- 调用次数统计
- 异常追踪
- 内存使用监控
"""

import asyncio
import functools
import time
import threading
from typing import Any, Callable, Dict, Optional, TypeVar, ParamSpec
from datetime import datetime
from dataclasses import dataclass, field
from collections import defaultdict

from app.core.logger import logger

P = ParamSpec('P')
T = TypeVar('T')


@dataclass
class FunctionStats:
    """函数统计信息"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_time_ms: float = 0.0
    min_time_ms: float = float('inf')
    max_time_ms: float = 0.0
    last_call_time: Optional[datetime] = None
    last_error: Optional[str] = None
    
    @property
    def avg_time_ms(self) -> float:
        if self.successful_calls == 0:
            return 0.0
        return self.total_time_ms / self.successful_calls
    
    @property
    def success_rate(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.successful_calls / self.total_calls
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "total_time_ms": round(self.total_time_ms, 2),
            "avg_time_ms": round(self.avg_time_ms, 2),
            "min_time_ms": round(self.min_time_ms, 2) if self.min_time_ms != float('inf') else 0,
            "max_time_ms": round(self.max_time_ms, 2),
            "success_rate": round(self.success_rate, 4),
            "last_call_time": self.last_call_time.isoformat() if self.last_call_time else None,
            "last_error": self.last_error
        }


class PerformanceMonitor:
    """性能监控器
    
    收集和汇总函数执行性能数据。
    """
    
    _instance: Optional['PerformanceMonitor'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(PerformanceMonitor, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self._initialized = True
        self._stats: Dict[str, FunctionStats] = defaultdict(FunctionStats)
        self._stats_lock = threading.Lock()
        self._start_time = datetime.now()
        
        logger.info("性能监控器已初始化")
    
    def record_call(
        self,
        function_name: str,
        duration_ms: float,
        success: bool,
        error: Optional[str] = None
    ) -> None:
        """记录函数调用
        
        Args:
            function_name: 函数名
            duration_ms: 执行时间（毫秒）
            success: 是否成功
            error: 错误信息（如果失败）
        """
        with self._stats_lock:
            stats = self._stats[function_name]
            stats.total_calls += 1
            stats.last_call_time = datetime.now()
            
            if success:
                stats.successful_calls += 1
                stats.total_time_ms += duration_ms
                stats.min_time_ms = min(stats.min_time_ms, duration_ms)
                stats.max_time_ms = max(stats.max_time_ms, duration_ms)
            else:
                stats.failed_calls += 1
                stats.last_error = error
    
    def get_stats(self, function_name: Optional[str] = None) -> Dict[str, Any]:
        """获取统计信息
        
        Args:
            function_name: 函数名，如果为None则返回所有统计
            
        Returns:
            统计信息字典
        """
        with self._stats_lock:
            if function_name:
                return self._stats.get(function_name, FunctionStats()).to_dict()
            
            return {
                name: stats.to_dict()
                for name, stats in self._stats.items()
            }
    
    def get_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        with self._stats_lock:
            total_calls = sum(s.total_calls for s in self._stats.values())
            total_time = sum(s.total_time_ms for s in self._stats.values())
            total_errors = sum(s.failed_calls for s in self._stats.values())
            
            slowest_functions = sorted(
                [(name, stats.avg_time_ms) for name, stats in self._stats.items()],
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            most_called_functions = sorted(
                [(name, stats.total_calls) for name, stats in self._stats.items()],
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            return {
                "uptime": str(datetime.now() - self._start_time),
                "total_functions_tracked": len(self._stats),
                "total_calls": total_calls,
                "total_time_ms": round(total_time, 2),
                "total_errors": total_errors,
                "error_rate": round(total_errors / total_calls, 4) if total_calls > 0 else 0,
                "slowest_functions": [
                    {"name": name, "avg_time_ms": round(avg_time, 2)}
                    for name, avg_time in slowest_functions
                ],
                "most_called_functions": [
                    {"name": name, "calls": calls}
                    for name, calls in most_called_functions
                ]
            }
    
    def reset(self) -> None:
        """重置所有统计"""
        with self._stats_lock:
            self._stats.clear()
            self._start_time = datetime.now()
        logger.info("性能监控统计已重置")


_performance_monitor_instance: Optional[PerformanceMonitor] = None
_monitor_lock = threading.Lock()


def get_performance_monitor() -> PerformanceMonitor:
    """获取性能监控器实例"""
    global _performance_monitor_instance
    
    if _performance_monitor_instance is None:
        with _monitor_lock:
            if _performance_monitor_instance is None:
                _performance_monitor_instance = PerformanceMonitor()
    
    return _performance_monitor_instance


def monitor_performance(
    name: Optional[str] = None,
    log_threshold_ms: float = 1000.0,
    log_slow: bool = True
):
    """性能监控装饰器
    
    自动记录函数执行时间、调用次数和异常。
    
    Args:
        name: 函数名称（默认使用函数原名）
        log_threshold_ms: 慢函数日志阈值（毫秒）
        log_slow: 是否记录慢函数日志
    
    Example:
        @monitor_performance(log_threshold_ms=500)
        async def calculate_score(student_id: str):
            ...
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        function_name = name or f"{func.__module__}.{func.__name__}"
        monitor = get_performance_monitor()
        
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            start_time = time.time()
            error_msg = None
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                error_msg = str(e)
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                success = error_msg is None
                
                monitor.record_call(function_name, duration_ms, success, error_msg)
                
                if log_slow and duration_ms > log_threshold_ms:
                    logger.warning(
                        f"慢函数警告: {function_name} 耗时 {duration_ms:.2f}ms "
                        f"(阈值: {log_threshold_ms}ms)"
                    )
                
                logger.debug(
                    f"函数 {function_name} 执行完成: "
                    f"耗时={duration_ms:.2f}ms, 成功={success}"
                )
        
        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            start_time = time.time()
            error_msg = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                error_msg = str(e)
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                success = error_msg is None
                
                monitor.record_call(function_name, duration_ms, success, error_msg)
                
                if log_slow and duration_ms > log_threshold_ms:
                    logger.warning(
                        f"慢函数警告: {function_name} 耗时 {duration_ms:.2f}ms "
                        f"(阈值: {log_threshold_ms}ms)"
                    )
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def timed(name: Optional[str] = None):
    """简化的计时装饰器
    
    仅记录执行时间，不进行详细统计。
    
    Args:
        name: 函数名称
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        function_name = name or func.__name__
        
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            start = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                logger.debug(f"{function_name} 耗时: {(time.time() - start)*1000:.2f}ms")
        
        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            start = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                logger.debug(f"{function_name} 耗时: {(time.time() - start)*1000:.2f}ms")
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


class PerformanceContext:
    """性能监控上下文管理器
    
    用于监控代码块的执行时间。
    
    Example:
        with PerformanceContext("数据处理"):
            # 执行代码
            pass
    """
    
    def __init__(self, name: str, log_threshold_ms: float = 1000.0):
        self.name = name
        self.log_threshold_ms = log_threshold_ms
        self.start_time: Optional[float] = None
        self.duration_ms: float = 0.0
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.duration_ms = (time.time() - self.start_time) * 1000
        
        monitor = get_performance_monitor()
        success = exc_type is None
        error_msg = str(exc_val) if exc_val else None
        
        monitor.record_call(self.name, self.duration_ms, success, error_msg)
        
        if self.duration_ms > self.log_threshold_ms:
            logger.warning(
                f"慢操作警告: {self.name} 耗时 {self.duration_ms:.2f}ms"
            )
        
        return False
    
    async def __aenter__(self):
        self.start_time = time.time()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.duration_ms = (time.time() - self.start_time) * 1000
        
        monitor = get_performance_monitor()
        success = exc_type is None
        error_msg = str(exc_val) if exc_val else None
        
        monitor.record_call(self.name, self.duration_ms, success, error_msg)
        
        if self.duration_ms > self.log_threshold_ms:
            logger.warning(
                f"慢操作警告: {self.name} 耗时 {self.duration_ms:.2f}ms"
            )
        
        return False
