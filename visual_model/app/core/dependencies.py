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
from app.core.api_entry import container

logger = get_logger(__name__)
T = TypeVar("T")



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
