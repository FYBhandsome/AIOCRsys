#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存服务模块

提供高性能的内存缓存机制，支持：
- TTL过期策略
- LRU淘汰策略
- 缓存命中率统计
- 异步安全访问
"""

import threading
import time
from typing import Any, Dict, Optional, Callable, TypeVar, Generic
from datetime import datetime
from collections import OrderedDict
from dataclasses import dataclass, field
from functools import wraps
import hashlib
import json

from app.core.logger import logger

T = TypeVar('T')


@dataclass
class CacheEntry:
    """缓存条目"""
    value: Any
    created_at: float
    expires_at: Optional[float] = None
    access_count: int = 0
    last_accessed_at: float = 0.0
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    def touch(self) -> None:
        """更新访问信息"""
        self.access_count += 1
        self.last_accessed_at = time.time()


class CacheStats:
    """缓存统计信息"""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.expirations = 0
        self._lock = threading.Lock()
    
    def record_hit(self) -> None:
        with self._lock:
            self.hits += 1
    
    def record_miss(self) -> None:
        with self._lock:
            self.misses += 1
    
    def record_eviction(self) -> None:
        with self._lock:
            self.evictions += 1
    
    def record_expiration(self) -> None:
        with self._lock:
            self.expirations += 1
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "hits": self.hits,
                "misses": self.misses,
                "evictions": self.evictions,
                "expirations": self.expirations,
                "hit_rate": round(self.hit_rate, 4)
            }


class LRUCache:
    """LRU缓存实现
    
    线程安全的LRU缓存，支持TTL过期策略。
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: Optional[float] = 300.0):
        """初始化LRU缓存
        
        Args:
            max_size: 最大缓存条目数
            default_ttl: 默认TTL（秒），None表示永不过期
        """
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._stats = CacheStats()
        
        logger.info(f"LRU缓存已创建: max_size={max_size}, default_ttl={default_ttl}")
    
    def _generate_key(self, *args, **kwargs) -> str:
        """生成缓存键"""
        key_data = {
            "args": [str(a) for a in args],
            "kwargs": {k: str(v) for k, v in sorted(kwargs.items())}
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在或已过期则返回None
        """
        with self._lock:
            if key not in self._cache:
                self._stats.record_miss()
                return None
            
            entry = self._cache[key]
            
            if entry.is_expired():
                del self._cache[key]
                self._stats.record_expiration()
                self._stats.record_miss()
                return None
            
            self._cache.move_to_end(key)
            entry.touch()
            self._stats.record_hit()
            
            return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None使用默认TTL
        """
        with self._lock:
            effective_ttl = ttl if ttl is not None else self._default_ttl
            
            now = time.time()
            expires_at = now + effective_ttl if effective_ttl else None
            
            if key in self._cache:
                del self._cache[key]
            
            while len(self._cache) >= self._max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._stats.record_eviction()
            
            self._cache[key] = CacheEntry(
                value=value,
                created_at=now,
                expires_at=expires_at,
                access_count=0,
                last_accessed_at=now
            )
    
    def delete(self, key: str) -> bool:
        """删除缓存条目
        
        Args:
            key: 缓存键
            
        Returns:
            是否成功删除
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            logger.info("缓存已清空")
    
    def cleanup_expired(self) -> int:
        """清理过期条目
        
        Returns:
            清理的条目数
        """
        count = 0
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                del self._cache[key]
                self._stats.record_expiration()
                count += 1
        
        if count > 0:
            logger.debug(f"清理了 {count} 个过期缓存条目")
        
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self._lock:
            return {
                **self._stats.to_dict(),
                "size": len(self._cache),
                "max_size": self._max_size,
                "utilization": round(len(self._cache) / self._max_size, 4) if self._max_size > 0 else 0
            }


class CacheService:
    """缓存服务
    
    提供多种缓存实例，支持不同场景的缓存需求。
    """
    
    _instance: Optional['CacheService'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(CacheService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self._initialized = True
        self._caches: Dict[str, LRUCache] = {}
        self._global_stats = CacheStats()
        
        self._caches['comprehensive_score'] = LRUCache(max_size=500, default_ttl=600.0)
        self._caches['student_scores'] = LRUCache(max_size=1000, default_ttl=300.0)
        self._caches['class_rankings'] = LRUCache(max_size=200, default_ttl=300.0)
        self._caches['ocr_results'] = LRUCache(max_size=100, default_ttl=3600.0)
        self._caches['config'] = LRUCache(max_size=50, default_ttl=1800.0)
        
        self._start_cleanup_thread()
        
        logger.info("缓存服务已初始化")
    
    def _start_cleanup_thread(self) -> None:
        """启动后台清理线程"""
        def cleanup_loop():
            while True:
                try:
                    time.sleep(60)
                    for cache in self._caches.values():
                        cache.cleanup_expired()
                except Exception as e:
                    logger.error(f"缓存清理线程出错: {e}")
        
        thread = threading.Thread(target=cleanup_loop, daemon=True, name="CacheCleanup")
        thread.start()
    
    def get_cache(self, name: str) -> LRUCache:
        """获取指定名称的缓存实例
        
        Args:
            name: 缓存名称
            
        Returns:
            LRUCache实例
        """
        if name not in self._caches:
            self._caches[name] = LRUCache()
        return self._caches[name]
    
    def get(self, cache_name: str, key: str) -> Optional[Any]:
        """从指定缓存获取值"""
        cache = self.get_cache(cache_name)
        return cache.get(key)
    
    def set(self, cache_name: str, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """设置缓存值"""
        cache = self.get_cache(cache_name)
        cache.set(key, value, ttl)
    
    def delete(self, cache_name: str, key: str) -> bool:
        """删除缓存值"""
        cache = self.get_cache(cache_name)
        return cache.delete(key)
    
    def invalidate_student(self, student_id: str) -> None:
        """使学生的所有缓存失效"""
        self._caches['comprehensive_score'].delete(f"student_{student_id}")
        self._caches['student_scores'].delete(f"scores_{student_id}")
        logger.debug(f"已使学生 {student_id} 的缓存失效")
    
    def invalidate_class(self, class_id: str) -> None:
        """使班级的所有缓存失效"""
        self._caches['class_rankings'].delete(f"class_{class_id}")
        self._caches['comprehensive_score'].delete(f"class_scores_{class_id}")
        logger.debug(f"已使班级 {class_id} 的缓存失效")
    
    def get_all_stats(self) -> Dict[str, Any]:
        """获取所有缓存的统计信息"""
        return {
            name: cache.get_stats()
            for name, cache in self._caches.items()
        }
    
    def clear_all(self) -> None:
        """清空所有缓存"""
        for cache in self._caches.values():
            cache.clear()
        logger.info("所有缓存已清空")


_cache_service_instance: Optional[CacheService] = None
_cache_lock = threading.Lock()


def get_cache_service() -> CacheService:
    """获取缓存服务实例（单例模式）"""
    global _cache_service_instance
    
    if _cache_service_instance is None:
        with _cache_lock:
            if _cache_service_instance is None:
                _cache_service_instance = CacheService()
    
    return _cache_service_instance


def cached(cache_name: str, key_prefix: str = "", ttl: Optional[float] = None):
    """缓存装饰器
    
    用于缓存函数返回值。
    
    Args:
        cache_name: 缓存名称
        key_prefix: 键前缀
        ttl: 过期时间（秒）
    
    Example:
        @cached('comprehensive_score', 'student_', ttl=300)
        async def get_student_score(student_id: str):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache = get_cache_service().get_cache(cache_name)
            
            cache_key = f"{key_prefix}_{func.__name__}_{hashlib.md5(str((args, sorted(kwargs.items()))).encode()).hexdigest()}"
            
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return cached_result
            
            result = await func(*args, **kwargs)
            
            cache.set(cache_key, result, ttl)
            logger.debug(f"缓存设置: {cache_key}")
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache = get_cache_service().get_cache(cache_name)
            
            cache_key = f"{key_prefix}_{func.__name__}_{hashlib.md5(str((args, sorted(kwargs.items()))).encode()).hexdigest()}"
            
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return cached_result
            
            result = func(*args, **kwargs)
            
            cache.set(cache_key, result, ttl)
            logger.debug(f"缓存设置: {cache_key}")
            
            return result
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator
