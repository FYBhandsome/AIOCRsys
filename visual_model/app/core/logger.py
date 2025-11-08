#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志配置模块
"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from config import settings


def setup_logger(name: str = "app") -> logging.Logger:
    """设置日志记录器"""
    # 创建日志目录
    log_dir = os.path.dirname(settings.LOG_FILE)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    # 在 Windows 终端强制使用 UTF-8，避免中文/emoji 编码报错
    try:
        # 设置环境变量
        os.environ["PYTHONIOENCODING"] = "utf-8"
        
        # 重新配置标准输出和标准错误
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        else:
            # 兼容旧版本 Python
            import io
            if hasattr(sys.stdout, "buffer"):
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
            if hasattr(sys.stderr, "buffer"):
                sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception as e:
        # 不影响文件日志，但记录警告
        print(f"Warning: Failed to set UTF-8 encoding for console: {e}")

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    if logger.handlers:
        return logger
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 文件处理器
    file_handler = RotatingFileHandler(
        settings.LOG_FILE,
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    file_handler.setFormatter(formatter)
    
    # 控制台处理器
    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


# 全局日志实例
logger = setup_logger("comprehensive-assessment")