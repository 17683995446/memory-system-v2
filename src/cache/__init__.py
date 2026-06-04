"""
性能优化与缓存系统
基于第一性原理：确定性、最小化、可观测
"""

from typing import Dict, Any, Optional, Generic, TypeVar, Callable
from collections import OrderedDict
from dataclasses import dataclass, field
from functools import wraps
import time
import hashlib
import json
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class CacheConfig:
    """缓存配置"""
    max_size: int = 1000
    ttl_seconds: int = 3600
    enable_stats: bool = True
    cleanup_interval: int = 300
    max_memory_mb: int = 100


@dataclass
class CacheEntry(Generic[T]):
    """缓存条目"""
    key: str
    value: T
    created_at: float
    last_accessed: float
    access_count: int = 0
    size_bytes: int = 0
    
    def is_expired(self, ttl: float) -> bool:
        """检查是否过期"""
        return time.time() - self.created_at > ttl


class LRUCache(Generic[T]):
    """LRU缓存实现"""
    
    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self._cache: OrderedDict[str, CacheEntry[T]] = OrderedDict()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'evictions': 0,
            'expirations': 0
        }
        self._total_size = 0
        self._last_cleanup = time.time()
    
    def get(self, key: str) -> Optional[T]:
        """获取缓存值"""
        if key not in self._cache:
            self._stats['misses'] += 1
            return None
        
        entry = self._cache[key]
        
        if entry.is_expired(self.config.ttl_seconds):
            self._stats['expirations'] += 1
            self._remove(key)
            return None
        
        self._stats['hits'] += 1
        entry.access_count += 1
        entry.last_accessed = time.time()
        
        self._cache.move_to_end(key)
        
        self._maybe_cleanup()
        
        return entry.value
    
    def set(self, key: str, value: T, ttl: Optional[float] = None) -> bool:
        """设置缓存值"""
        if key in self._cache:
            old_entry = self._cache[key]
            self._total_size -= old_entry.size_bytes
        
        try:
            size_bytes = self._calculate_size(value)
        except Exception:
            size_bytes = 100
        
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=time.time(),
            last_accessed=time.time(),
            access_count=0,
            size_bytes=size_bytes
        )
        
        # 先检查max_size限制，驱逐超出限制的条目
        if len(self._cache) >= self.config.max_size and key not in self._cache:
            self._evict_until_fit(size_bytes)
        
        # 再检查内存限制
        if self._total_size + size_bytes > self.config.max_memory_mb * 1024 * 1024:
            self._evict_until_fit(size_bytes)
        
        self._cache[key] = entry
        self._cache.move_to_end(key)
        self._total_size += size_bytes
        
        self._stats['sets'] += 1
        
        self._maybe_cleanup()
        
        return True
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        if key in self._cache:
            self._remove(key)
            return True
        return False
    
    def clear(self) -> int:
        """清空缓存"""
        count = len(self._cache)
        self._cache.clear()
        self._total_size = 0
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计"""
        total = self._stats['hits'] + self._stats['misses']
        hit_rate = (self._stats['hits'] / total * 100) if total > 0 else 0
        
        return {
            'hits': self._stats['hits'],
            'misses': self._stats['misses'],
            'sets': self._stats['sets'],
            'evictions': self._stats['evictions'],
            'expirations': self._stats['expirations'],
            'hit_rate': hit_rate,
            'size': len(self._cache),
            'total_size_bytes': self._total_size,
            'max_size': self.config.max_size
        }
    
    def _remove(self, key: str):
        """移除条目"""
        if key in self._cache:
            entry = self._cache.pop(key)
            self._total_size -= entry.size_bytes
    
    def _evict_until_fit(self, needed_bytes: int):
        """驱逐直到有足够空间"""
        while (
            self._total_size + needed_bytes > self.config.max_memory_mb * 1024 * 1024
            or len(self._cache) >= self.config.max_size
        ):
            if not self._cache:
                break
            oldest_key = next(iter(self._cache))
            self._remove(oldest_key)
            self._stats['evictions'] += 1
    
    def _maybe_cleanup(self):
        """按需清理"""
        now = time.time()
        if now - self._last_cleanup < self.config.cleanup_interval:
            return
        
        self._last_cleanup = now
        
        expired_keys = [
            key for key, entry in list(self._cache.items())
            if entry.is_expired(self.config.ttl_seconds)
        ]
        
        for key in expired_keys:
            self._remove(key)
            self._stats['expirations'] += 1
    
    def _calculate_size(self, value: Any) -> int:
        """估算值大小"""
        try:
            return len(json.dumps(value, default=str).encode('utf-8'))
        except Exception:
            return 100


class MultiLevelCache:
    """多级缓存系统"""
    
    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        
        self.l1_cache = LRUCache[Any](self._layer_config("l1", 500, 300))
        self.l2_cache = LRUCache[Any](self._layer_config("l2", 2000, 1800))
        
        self._layer_stats = {
            'l1': {},
            'l2': {}
        }
    
    def _layer_config(self, layer: str, max_size: int, ttl: int) -> CacheConfig:
        """获取层级配置"""
        return CacheConfig(
            max_size=max_size,
            ttl_seconds=ttl,
            enable_stats=True
        )
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取缓存（L1 -> L2），支持默认值"""
        value = self.l1_cache.get(key)
        if value is not None:
            self._layer_stats['l1'] = self.l1_cache.get_stats()
            return value
        
        value = self.l2_cache.get(key)
        if value is not None:
            self.l1_cache.set(key, value)
            self._layer_stats['l2'] = self.l2_cache.get_stats()
            return value
        
        self._layer_stats['l1'] = self.l1_cache.get_stats()
        self._layer_stats['l2'] = self.l2_cache.get_stats()
        return default
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """设置缓存（L1 + L2）"""
        self.l1_cache.set(key, value, ttl)
        self.l2_cache.set(key, value, ttl)
        return True
    
    def delete(self, key: str) -> bool:
        """删除缓存（L1 + L2）"""
        l1_deleted = self.l1_cache.delete(key)
        l2_deleted = self.l2_cache.delete(key)
        return l1_deleted or l2_deleted
    
    def invalidate_pattern(self, pattern: str) -> int:
        """按模式失效"""
        count = 0
        for key in list(self.l1_cache._cache.keys()):
            if pattern in key:
                self.l1_cache.delete(key)
                count += 1
        for key in list(self.l2_cache._cache.keys()):
            if pattern in key:
                self.l2_cache.delete(key)
                count += 1
        return count
    
    def clear(self) -> Dict[str, int]:
        """清空所有缓存"""
        return {
            'l1': self.l1_cache.clear(),
            'l2': self.l2_cache.clear()
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计"""
        return {
            'l1': self.l1_cache.get_stats(),
            'l2': self.l2_cache.get_stats(),
            'total': {
                'size': len(self.l1_cache._cache) + len(self.l2_cache._cache),
                'total_size_bytes': self.l1_cache._total_size + self.l2_cache._total_size
            }
        }


def cache_result(cache: MultiLevelCache, ttl: Optional[float] = None):
    """缓存装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            key_parts = [func.__module__, func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            key = hashlib.md5('|'.join(key_parts).encode()).hexdigest()
            
            cached = cache.get(key)
            if cached is not None:
                return cached
            
            result = func(*args, **kwargs)
            cache.set(key, result, ttl)
            return result
        return wrapper
    return decorator


_cache_instance: Optional[MultiLevelCache] = None


def get_cache_system() -> MultiLevelCache:
    """获取缓存系统单例"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = MultiLevelCache()
    return _cache_instance


def get_lru_cache() -> LRUCache:
    """获取简单LRU缓存"""
    return LRUCache[Any]()


def get_cache() -> MultiLevelCache:
    """获取缓存实例（兼容旧接口）"""
    return get_cache_system()
