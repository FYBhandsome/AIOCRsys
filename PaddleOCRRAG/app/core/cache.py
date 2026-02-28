"""
缓存管理模块
提供内存缓存和Redis缓存支持
"""
import hashlib
import json
import time
from typing import Any, Dict, Optional, Callable, TypeVar, Generic
from functools import wraps
from datetime import datetime
import threading
from app.core.logger import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


class CacheItem:
    """缓存项"""
    
    def __init__(self, value: Any, ttl: int = 300):
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl
        self.expires_at = self.created_at + ttl if ttl > 0 else float('inf')
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        return time.time() > self.expires_at


class MemoryCache:
    """内存缓存实现"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        初始化内存缓存
        
        Args:
            max_size: 最大缓存数量
            default_ttl: 默认过期时间（秒）
        """
        self._cache: Dict[str, CacheItem] = {}
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._lock = threading.RLock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }
    
    def _generate_key(self, *args, **kwargs) -> str:
        """生成缓存键"""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self._lock:
            item = self._cache.get(key)
            if item is None:
                self._stats["misses"] += 1
                return None
            
            if item.is_expired():
                del self._cache[key]
                self._stats["misses"] += 1
                self._stats["evictions"] += 1
                return None
            
            self._stats["hits"] += 1
            return item.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值"""
        with self._lock:
            if len(self._cache) >= self._max_size and key not in self._cache:
                self._evict_expired()
                
                if len(self._cache) >= self._max_size:
                    oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].created_at)
                    del self._cache[oldest_key]
                    self._stats["evictions"] += 1
            
            self._cache[key] = CacheItem(value, ttl or self._default_ttl)
    
    def delete(self, key: str) -> bool:
        """删除缓存值"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()
    
    def _evict_expired(self) -> int:
        """清理过期缓存"""
        with self._lock:
            expired_keys = [k for k, v in self._cache.items() if v.is_expired()]
            for key in expired_keys:
                del self._cache[key]
                self._stats["evictions"] += 1
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0
            
            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "evictions": self._stats["evictions"],
                "hit_rate": f"{hit_rate:.2%}"
            }


class CacheManager:
    """缓存管理器"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CacheManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._caches: Dict[str, MemoryCache] = {}
        self._default_cache = MemoryCache()
        logger.info("缓存管理器初始化完成")
    
    def get_cache(self, name: str = "default", max_size: int = 1000, ttl: int = 300) -> MemoryCache:
        """获取或创建命名缓存"""
        if name not in self._caches:
            self._caches[name] = MemoryCache(max_size=max_size, default_ttl=ttl)
        return self._caches[name]
    
    def get(self, key: str, cache_name: str = "default") -> Optional[Any]:
        """获取缓存值"""
        cache = self._caches.get(cache_name, self._default_cache)
        return cache.get(key)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, cache_name: str = "default") -> None:
        """设置缓存值"""
        cache = self._caches.get(cache_name, self._default_cache)
        cache.set(key, value, ttl)
    
    def delete(self, key: str, cache_name: str = "default") -> bool:
        """删除缓存值"""
        cache = self._caches.get(cache_name, self._default_cache)
        return cache.delete(key)
    
    def clear(self, cache_name: str = "default") -> None:
        """清空缓存"""
        cache = self._caches.get(cache_name, self._default_cache)
        cache.clear()
    
    def clear_all(self) -> None:
        """清空所有缓存"""
        for cache in self._caches.values():
            cache.clear()
        self._default_cache.clear()
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有缓存统计"""
        stats = {"default": self._default_cache.get_stats()}
        for name, cache in self._caches.items():
            stats[name] = cache.get_stats()
        return stats


cache_manager = CacheManager()


def cached(
    ttl: int = 300,
    cache_name: str = "default",
    key_prefix: str = "",
    skip_cache_func: Optional[Callable] = None
):
    """
    缓存装饰器
    
    Args:
        ttl: 缓存过期时间（秒）
        cache_name: 缓存名称
        key_prefix: 键前缀
        skip_cache_func: 判断是否跳过缓存的函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if skip_cache_func and skip_cache_func(*args, **kwargs):
                return func(*args, **kwargs)
            
            cache = cache_manager.get_cache(cache_name)
            
            cache_key = f"{key_prefix}:{func.__name__}:{cache._generate_key(*args, **kwargs)}"
            
            result = cache.get(cache_key)
            if result is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return result
            
            logger.debug(f"缓存未命中: {cache_key}")
            result = func(*args, **kwargs)
            
            cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def async_cached(
    ttl: int = 300,
    cache_name: str = "default",
    key_prefix: str = "",
    skip_cache_func: Optional[Callable] = None
):
    """
    异步缓存装饰器
    
    Args:
        ttl: 缓存过期时间（秒）
        cache_name: 缓存名称
        key_prefix: 键前缀
        skip_cache_func: 判断是否跳过缓存的函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if skip_cache_func and skip_cache_func(*args, **kwargs):
                return await func(*args, **kwargs)
            
            cache = cache_manager.get_cache(cache_name)
            
            cache_key = f"{key_prefix}:{func.__name__}:{cache._generate_key(*args, **kwargs)}"
            
            result = cache.get(cache_key)
            if result is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return result
            
            logger.debug(f"缓存未命中: {cache_key}")
            result = await func(*args, **kwargs)
            
            cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator
