#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
线程池执行器管理器

统一管理异步执行器，用于在异步上下文-free环境中运行同步任务。
"""

from typing import Optional
from concurrent.futures import ThreadPoolExecutor
import atexit

from app.core.logger import logger
from config import settings


class ExecutorManager:
    """线程池执行器管理器 - 单例模式"""
    
    _instance: Optional['ExecutorManager'] = None
    _initialized: bool = False
    
    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super(ExecutorManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化执行器管理器"""
        if not hasattr(self, 'executor'):
            self.executor: Optional[ThreadPoolExecutor] = None
            self.max_workers = 2  # OCR任务CPU密集型，限制并发数
            logger.debug("执行器管理器初始化完成")
            # 注册退出时的清理函数
            atexit.register(self.cleanup)
    
    def get_executor(self) -> ThreadPoolExecutor:
        """获取线程池执行器实例
        
        Returns:
            ThreadPoolExecutor: 线程池执行器
        """
        if self.executor is None:
            self.executor = ThreadPoolExecutor(
                max_workers=self.max_workers,
                thread_name_prefix="ocr_worker"
            )
            logger.info(f"线程池执行器已创建，最大工作线程数: {self.max_workers}")
        return self.executor
    
    def cleanup(self) -> None:
        """清理线程池执行器
        
        关闭线程池，等待所有任务完成。
        """
        if self.executor is not None:
            logger.info("正在关闭线程池执行器...")
            self.executor.shutdown(wait=True)
            self.executor = None
            logger.info("线程池执行器已关闭")
    
    async def aclose(self) -> None:
        """异步关闭线程池执行器
        
        从FastAPI生命周期钩子调用。
        """
        self.cleanup()


# 创建全局单例实例
executor_manager = ExecutorManager()


def get_executor() -> ThreadPoolExecutor:
    """获取全局线程池执行器实例
    
    Returns:
        ThreadPoolExecutor: 线程池执行器
    """
    return executor_manager.get_executor()

