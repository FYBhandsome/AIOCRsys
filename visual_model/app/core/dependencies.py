#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖注入配置模块
配置服务层和数据访问层的依赖注入
"""
from typing import Any, Callable, Dict, Optional, Type, TypeVar
from functools import lru_cache

from fastapi import Depends

from app.core.logger import get_logger
from app.core.base_repository import (
    BaseRepository,
    StudentRepository,
    AcademicScoreRepository,
    ComprehensiveScoreRepository,
    CertificateRepository,
    FileMetadataRepository,
    get_student_repository,
    get_academic_score_repository,
    get_comprehensive_score_repository,
    get_certificate_repository,
    get_file_metadata_repository
)
from app.core.base_service import (
    BaseService,
    StudentService,
    AcademicScoreService,
    ComprehensiveScoreService,
    CertificateService,
    FileService,
    get_student_service,
    get_academic_score_service,
    get_comprehensive_score_service,
    get_certificate_service,
    get_file_service
)
from app.core.api_entry import DependencyContainer, container

logger = get_logger(__name__)
T = TypeVar("T")


class ServiceRegistry:
    """服务注册中心"""
    
    _services: Dict[str, Any] = {}
    _initialized = False
    
    @classmethod
    def register(cls, name: str, factory: Callable):
        """注册服务工厂"""
        cls._services[name] = factory
        logger.debug(f"注册服务工厂: {name}")
    
    @classmethod
    def get(cls, name: str) -> Any:
        """获取服务实例"""
        if name not in cls._services:
            raise ValueError(f"服务未注册: {name}")
        
        factory = cls._services[name]
        return factory()
    
    @classmethod
    def initialize(cls):
        """初始化所有服务"""
        if cls._initialized:
            return
        
        cls.register("student_repository", get_student_repository)
        cls.register("academic_score_repository", get_academic_score_repository)
        cls.register("comprehensive_score_repository", get_comprehensive_score_repository)
        cls.register("certificate_repository", get_certificate_repository)
        cls.register("file_metadata_repository", get_file_metadata_repository)
        
        cls.register("student_service", get_student_service)
        cls.register("academic_score_service", get_academic_score_service)
        cls.register("comprehensive_score_service", get_comprehensive_score_service)
        cls.register("certificate_service", get_certificate_service)
        cls.register("file_service", get_file_service)
        
        for name, factory in cls._services.items():
            container.register_factory(name, factory)
        
        cls._initialized = True
        logger.info("服务注册完成")


def get_repository(repo_type: Type[BaseRepository]) -> BaseRepository:
    """获取仓储实例"""
    repo_map = {
        StudentRepository: get_student_repository,
        AcademicScoreRepository: get_academic_score_repository,
        ComprehensiveScoreRepository: get_comprehensive_score_repository,
        CertificateRepository: get_certificate_repository,
        FileMetadataRepository: get_file_metadata_repository,
    }
    
    factory = repo_map.get(repo_type)
    if not factory:
        raise ValueError(f"未知的仓储类型: {repo_type}")
    
    return factory()


def get_service(service_type: Type[BaseService]) -> BaseService:
    """获取服务实例"""
    service_map = {
        StudentService: get_student_service,
        AcademicScoreService: get_academic_score_service,
        ComprehensiveScoreService: get_comprehensive_score_service,
        CertificateService: get_certificate_service,
        FileService: get_file_service,
    }
    
    factory = service_map.get(service_type)
    if not factory:
        raise ValueError(f"未知的服务类型: {service_type}")
    
    return factory()


def inject_repository(repo_type: Type[BaseRepository]):
    """仓储依赖注入装饰器"""
    def dependency():
        return get_repository(repo_type)
    return Depends(dependency)


def inject_service(service_type: Type[BaseService]):
    """服务依赖注入装饰器"""
    def dependency():
        return get_service(service_type)
    return Depends(dependency)


class DatabaseSession:
    """数据库会话管理"""
    
    def __init__(self):
        self._session = None
    
    async def __aenter__(self):
        from app.core.db_connection import get_db_connection_manager
        db_manager = get_db_connection_manager()
        await db_manager.init_connection()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        from app.core.db_connection import get_db_connection_manager
        db_manager = get_db_connection_manager()
        await db_manager.close_connection()


async def get_db_session() -> DatabaseSession:
    """获取数据库会话依赖"""
    async with DatabaseSession() as session:
        yield session


class CacheManager:
    """缓存管理器"""
    
    _instance = None
    _cache: Dict[str, Any] = {}
    _ttl: Dict[str, float] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get(self, key: str) -> Optional[Any]:
        import time
        if key in self._cache:
            if key in self._ttl and self._ttl[key] < time.time():
                del self._cache[key]
                del self._ttl[key]
                return None
            return self._cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: int = 300):
        import time
        self._cache[key] = value
        self._ttl[key] = time.time() + ttl
    
    def delete(self, key: str):
        if key in self._cache:
            del self._cache[key]
        if key in self._ttl:
            del self._ttl[key]
    
    def clear(self):
        self._cache.clear()
        self._ttl.clear()


@lru_cache()
def get_cache_manager() -> CacheManager:
    """获取缓存管理器"""
    return CacheManager()


def cached(ttl: int = 300):
    """缓存装饰器"""
    def decorator(func):
        import functools
        import asyncio
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache_manager()
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            result = cache.get(cache_key)
            if result is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return result
            
            result = await func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            logger.debug(f"缓存设置: {cache_key}")
            
            return result
        
        return wrapper
    
    return decorator


def init_dependencies():
    """初始化依赖注入"""
    ServiceRegistry.initialize()
    logger.info("依赖注入初始化完成")
