#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库连接管理器 - 统一管理Tortoise ORM连接
"""
from typing import Optional, Dict, Any
import os
from pathlib import Path

from tortoise import Tortoise
from tortoise.exceptions import ConfigurationError

from app.core.logger import logger
from config import settings


class DatabaseConnectionManager:
    """统一的数据库连接管理器"""
    
    _instance: Optional['DatabaseConnectionManager'] = None
    _initialized: bool = False
    
    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super(DatabaseConnectionManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化数据库连接管理器"""
        if not hasattr(self, 'db_url'):
            self.db_url = settings.DATABASE_URL
            self.tortoise_config = settings.TORTOISE_ORM
            logger.debug("数据库连接管理器初始化完成")
    
    async def init_connection(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        初始化数据库连接
        
        Args:
            config: 自定义配置，如果为None则使用默认配置
            
        Returns:
            bool: 初始化是否成功
        """
        if self._initialized:
            logger.debug("数据库连接已初始化，跳过重复初始化")
            return True
            
        try:
            # 使用自定义配置或默认配置
            db_config = config or self.tortoise_config
            
            # 确保数据目录存在
            await self._ensure_data_directory()
            
            # 初始化Tortoise ORM
            await Tortoise.init(config=db_config)
            
            # 生成数据库表结构
            await Tortoise.generate_schemas(safe=True)
            
            self._initialized = True
            logger.info("数据库连接初始化成功")
            return True
        except ConfigurationError as e:
            logger.error(f"数据库配置错误: {e}")
            return False
        except Exception as e:
            logger.error(f"数据库连接初始化失败: {e}", exc_info=True)
            return False
    
    async def close_connection(self) -> None:
        """关闭数据库连接"""
        if not self._initialized:
            logger.debug("数据库连接未初始化，无需关闭")
            return
            
        try:
            await Tortoise.close_connections()
            self._initialized = False
            logger.info("数据库连接已关闭")
        except Exception as e:
            logger.error(f"关闭数据库连接失败: {e}", exc_info=True)
    
    async def _ensure_data_directory(self) -> None:
        """确保数据库文件目录存在"""
        db_path = self.db_url.replace("sqlite:///", "").replace("sqlite://", "")
        
        # 处理Windows路径，确保正确解析
        if db_path.startswith("/") and len(db_path) > 2 and db_path[2] == ":":
            # 处理类似 /D:/path 的路径
            db_path = db_path[1:]
        
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            logger.info(f"创建数据目录: {db_dir}")
    
    def is_initialized(self) -> bool:
        """检查数据库连接是否已初始化"""
        return self._initialized
    
    async def reset_connection(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        重置数据库连接
        
        Args:
            config: 自定义配置，如果为None则使用默认配置
            
        Returns:
            bool: 重置是否成功
        """
        await self.close_connection()
        return await self.init_connection(config)


# 创建全局单例实例
db_connection_manager = DatabaseConnectionManager()


# 为了向后兼容，提供全局函数
async def init_database(config: Optional[Dict[str, Any]] = None) -> bool:
    """
    初始化数据库连接 - 全局函数
    
    Args:
        config: 自定义配置，如果为None则使用默认配置
        
    Returns:
        bool: 初始化是否成功
    """
    return await db_connection_manager.init_connection(config)


async def close_database() -> None:
    """关闭数据库连接 - 全局函数"""
    await db_connection_manager.close_connection()


def get_db_connection_manager() -> DatabaseConnectionManager:
    """获取数据库连接管理器实例"""
    return db_connection_manager