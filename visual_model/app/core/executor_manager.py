#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
线程池执行器管理器

统一管理异步执行器，用于在异步上下文-free环境中运行同步任务。
优化版本：支持动态调整、任务队列监控和优雅关闭。
"""

from typing import Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, Future
import atexit
import threading
import time
from datetime import datetime
from collections import deque

from app.core.logger import logger
from config import settings


class ExecutorManager:
    """线程池执行器管理器 - 单例模式
    
    功能:
    - 统一管理线程池执行器
    - 动态调整线程池大小
    - 任务队列监控
    - 优雅关闭
    """
    
    _instance: Optional['ExecutorManager'] = None
    _initialized: bool = False
    
    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super(ExecutorManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化执行器管理器"""
        if hasattr(self, 'executor'):
            return
        
        self.executor: Optional[ThreadPoolExecutor] = None
        self._lock = threading.Lock()
        self._max_workers = getattr(settings, 'OCR_CPU_THREADS', 4)
        self._active_tasks: Dict[str, Future] = {}
        self._task_counter = 0
        self._stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "total_time_ms": 0,
            "created_at": datetime.now().isoformat()
        }
        self._task_history: deque = deque(maxlen=100)
        
        logger.debug("执行器管理器初始化完成")
        atexit.register(self.cleanup)
    
    def get_executor(self) -> ThreadPoolExecutor:
        """获取线程池执行器实例
        
        Returns:
            ThreadPoolExecutor: 线程池执行器
        """
        with self._lock:
            if self.executor is None:
                self.executor = ThreadPoolExecutor(
                    max_workers=self._max_workers,
                    thread_name_prefix="ocr_worker"
                )
                logger.info(f"线程池执行器已创建，最大工作线程数: {self._max_workers}")
            return self.executor
    
    def is_shutdown(self) -> bool:
        """检查执行器是否已关闭"""
        with self._lock:
            return self.executor is None
    
    def reset(self) -> None:
        """重置执行器（用于测试）"""
        with self._lock:
            if self.executor is not None:
                try:
                    self.executor.shutdown(wait=False, cancel_futures=True)
                except Exception as e:
                    logger.warning(f"关闭旧执行器时出错: {e}")
            self.executor = None
            self._active_tasks.clear()
            logger.info("执行器已重置")
    
    def submit_task(self, fn, *args, **kwargs) -> Future:
        """提交任务到线程池
        
        Args:
            fn: 要执行的函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            Future: 任务Future对象
        """
        executor = self.get_executor()
        
        with self._lock:
            self._task_counter += 1
            task_id = f"task_{self._task_counter}"
            self._stats["total_tasks"] += 1
        
        start_time = time.time()
        
        def wrapped_fn(*a, **kw):
            try:
                result = fn(*a, **kw)
                elapsed_ms = (time.time() - start_time) * 1000
                
                with self._lock:
                    self._stats["completed_tasks"] += 1
                    self._stats["total_time_ms"] += elapsed_ms
                    self._task_history.append({
                        "task_id": task_id,
                        "status": "completed",
                        "duration_ms": elapsed_ms,
                        "timestamp": datetime.now().isoformat()
                    })
                
                return result
            except Exception as e:
                elapsed_ms = (time.time() - start_time) * 1000
                
                with self._lock:
                    self._stats["failed_tasks"] += 1
                    self._task_history.append({
                        "task_id": task_id,
                        "status": "failed",
                        "error": str(e),
                        "duration_ms": elapsed_ms,
                        "timestamp": datetime.now().isoformat()
                    })
                
                raise
        
        future = executor.submit(wrapped_fn, *args, **kwargs)
        
        with self._lock:
            self._active_tasks[task_id] = future
        
        def cleanup_task(f):
            with self._lock:
                if task_id in self._active_tasks:
                    del self._active_tasks[task_id]
        
        future.add_done_callback(cleanup_task)
        
        return future
    
    def resize(self, max_workers: int) -> bool:
        """调整线程池大小
        
        注意：Python的ThreadPoolExecutor不支持动态调整大小，
        此方法会创建新的线程池。
        
        Args:
            max_workers: 新的最大工作线程数
            
        Returns:
            是否调整成功
        """
        if max_workers < 1:
            logger.warning(f"无效的线程池大小: {max_workers}")
            return False
        
        with self._lock:
            old_workers = self._max_workers
            
            if self.executor is not None:
                logger.info(f"正在调整线程池大小: {old_workers} -> {max_workers}")
                
                old_executor = self.executor
                self.executor = ThreadPoolExecutor(
                    max_workers=max_workers,
                    thread_name_prefix="ocr_worker"
                )
                self._max_workers = max_workers
                
                old_executor.shutdown(wait=False)
                logger.info(f"线程池大小已调整: {old_workers} -> {max_workers}")
            else:
                self._max_workers = max_workers
                logger.info(f"线程池最大工作线程数已设置: {max_workers}")
            
            return True
    
    def get_status(self) -> Dict[str, Any]:
        """获取执行器状态"""
        with self._lock:
            active_count = len(self._active_tasks)
            avg_time = (
                self._stats["total_time_ms"] / self._stats["completed_tasks"]
                if self._stats["completed_tasks"] > 0 else 0
            )
            
            return {
                "initialized": self.executor is not None,
                "max_workers": self._max_workers,
                "active_tasks": active_count,
                "stats": {
                    **self._stats,
                    "avg_time_ms": round(avg_time, 2)
                },
                "recent_tasks": list(self._task_history)[-10:]
            }
    
    def cleanup(self) -> None:
        """清理线程池执行器
        
        关闭线程池，等待所有任务完成。
        """
        with self._lock:
            if self.executor is not None:
                try:
                    logger.info("正在关闭线程池执行器...")
                except ValueError:
                    pass
                
                active_count = len(self._active_tasks)
                if active_count > 0:
                    try:
                        logger.info(f"等待 {active_count} 个活动任务完成...")
                    except ValueError:
                        pass
                
                self.executor.shutdown(wait=True, cancel_futures=False)
                self.executor = None
                self._active_tasks.clear()
                
                try:
                    logger.info("线程池执行器已关闭")
                except ValueError:
                    pass
    
    async def aclose(self) -> None:
        """异步关闭线程池执行器
        
        从FastAPI生命周期钩子调用。
        """
        self.cleanup()


executor_manager = ExecutorManager()


def get_executor() -> ThreadPoolExecutor:
    """获取全局线程池执行器实例
    
    Returns:
        ThreadPoolExecutor: 线程池执行器
    """
    return executor_manager.get_executor()


def submit_task(fn, *args, **kwargs) -> Future:
    """提交任务到线程池的便捷函数
    
    Args:
        fn: 要执行的函数
        *args: 位置参数
        **kwargs: 关键字参数
        
    Returns:
        Future: 任务Future对象
    """
    return executor_manager.submit_task(fn, *args, **kwargs)


def get_executor_status() -> Dict[str, Any]:
    """获取执行器状态的便捷函数
    
    Returns:
        执行器状态字典
    """
    return executor_manager.get_status()


def reset_executor() -> None:
    """重置执行器（用于测试）"""
    executor_manager.reset()


def is_executor_shutdown() -> bool:
    """检查执行器是否已关闭"""
    return executor_manager.is_shutdown()
