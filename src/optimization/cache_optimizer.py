"""
缓存优化策略
用于缓存访问模式分析和优化
"""

import time
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from collections import OrderedDict, defaultdict


class CacheEvictionPolicy(Enum):
    """缓存驱逐策略"""
    LRU = "lru"
    LFU = "lfu"
    FIFO = "fifo"
    RANDOM = "random"
    TTL = "ttl"


class CacheOptimizationLevel(Enum):
    """缓存优化级别"""
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    size: int
    hit_count: int
    miss_count: int
    last_access_time: datetime
    expiration_time: Optional[datetime]
    creation_time: datetime


@dataclass
class CacheStatistics:
    """缓存统计"""
    total_hits: int
    total_misses: int
    hit_rate: float
    total_entries: int
    total_size: int
    avg_size: float
    oldest_entry: Optional[datetime]
    newest_entry: Optional[datetime]


@dataclass
class AccessPattern:
    """访问模式"""
    key: str
    access_count: int
    last_access: datetime
    avg_access_interval: float


@dataclass
class CacheSuggestion:
    """缓存建议"""
    category: str
    issue: str
    suggestion: str
    priority: int
    expected_improvement: str


class OptimizedCache:
    """优化的缓存实现"""
    
    def __init__(
        self,
        max_size: int = 100 * 1024 * 1024,
        max_entries: int = 10000,
        default_ttl: int = 3600,
        eviction_policy: CacheEvictionPolicy = CacheEvictionPolicy.LRU
    ):
        self._cache: OrderedDict = OrderedDict()
        self._access_counts: Dict[str, int] = defaultdict(int)
        self._max_size = max_size
        self._max_entries = max_entries
        self._default_ttl = default_ttl
        self._eviction_policy = eviction_policy
        self._lock = threading.Lock()
        
        self._total_hits = 0
        self._total_misses = 0
        self._current_size = 0
        self._entry_sizes: Dict[str, int] = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取缓存条目"""
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                
                if entry.expiration_time and datetime.now() > entry.expiration_time:
                    self._remove_entry(key)
                    self._total_misses += 1
                    return default
                
                entry.hit_count += 1
                entry.last_access_time = datetime.now()
                self._total_hits += 1
                
                if self._eviction_policy == CacheEvictionPolicy.LRU:
                    self._cache.move_to_end(key)
                
                self._access_counts[key] = self._access_counts.get(key, 0) + 1
                
                return entry.value
            
            self._total_misses += 1
            return default
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        size: Optional[int] = None
    ):
        """设置缓存条目"""
        with self._lock:
            if key in self._cache:
                self._remove_entry(key)
            
            if size is None:
                try:
                    size = self._estimate_size(value)
                except Exception:
                    size = 1024
            
            self._evict_if_needed(size)
            
            expiration_time = None
            if ttl is not None:
                expiration_time = datetime.now() + timedelta(seconds=ttl)
            elif self._default_ttl > 0:
                expiration_time = datetime.now() + timedelta(seconds=self._default_ttl)
            
            entry = CacheEntry(
                key=key,
                value=value,
                size=size,
                hit_count=0,
                miss_count=0,
                last_access_time=datetime.now(),
                expiration_time=expiration_time,
                creation_time=datetime.now()
            )
            
            self._cache[key] = entry
            self._current_size += size
            self._entry_sizes[key] = size
    
    def delete(self, key: str):
        """删除缓存条目"""
        with self._lock:
            self._remove_entry(key)
    
    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._current_size = 0
            self._entry_sizes.clear()
            self._access_counts.clear()
    
    def _remove_entry(self, key: str):
        """移除缓存条目（内部方法）"""
        if key in self._cache:
            size = self._entry_sizes.get(key, 0)
            self._current_size -= size
            del self._cache[key]
            if key in self._entry_sizes:
                del self._entry_sizes[key]
    
    def _estimate_size(self, value: Any) -> int:
        """估算值的大小"""
        import sys
        
        size = sys.getsizeof(value)
        
        if hasattr(value, '__dict__'):
            size += sum(sys.getsizeof(v) for v in value.__dict__.values())
        
        if isinstance(value, (list, tuple, set)):
            size += sum(sys.getsizeof(item) for item in value)
        
        if isinstance(value, dict):
            size += sum(sys.getsizeof(k) + sys.getsizeof(v) for k, v in value.items())
        
        return size
    
    def _evict_if_needed(self, new_size: int):
        """根据需要驱逐条目"""
        while (self._current_size + new_size > self._max_size or
               len(self._cache) >= self._max_entries):
            
            if not self._cache:
                break
            
            key_to_evict = self._select_eviction_key()
            
            if key_to_evict:
                self._remove_entry(key_to_evict)
            else:
                break
    
    def _select_eviction_key(self) -> Optional[str]:
        """选择要驱逐的键"""
        if self._eviction_policy == CacheEvictionPolicy.LRU:
            return next(iter(self._cache))
        
        elif self._eviction_policy == CacheEvictionPolicy.LFU:
            min_count = float('inf')
            lfu_key = None
            for key in self._cache:
                count = self._access_counts.get(key, 0)
                if count < min_count:
                    min_count = count
                    lfu_key = key
            return lfu_key
        
        elif self._eviction_policy == CacheEvictionPolicy.FIFO:
            return next(iter(self._cache))
        
        elif self._eviction_policy == CacheEvictionPolicy.TTL:
            oldest_expiry = None
            ttl_key = None
            now = datetime.now()
            for key, entry in self._cache.items():
                if entry.expiration_time:
                    if not oldest_expiry or entry.expiration_time < oldest_expiry:
                        oldest_expiry = entry.expiration_time
                        ttl_key = key
            return ttl_key if ttl_key else next(iter(self._cache))
        
        else:
            import random
            return random.choice(list(self._cache.keys())) if self._cache else None
    
    def get_statistics(self) -> CacheStatistics:
        """获取缓存统计"""
        with self._lock:
            total_requests = self._total_hits + self._total_misses
            hit_rate = (self._total_hits / total_requests * 100) if total_requests > 0 else 0.0
            
            entries = list(self._cache.values())
            avg_size = (sum(e.size for e in entries) / len(entries)) if entries else 0.0
            
            oldest = min((e.creation_time for e in entries), default=None)
            newest = max((e.creation_time for e in entries), default=None)
            
            return CacheStatistics(
                total_hits=self._total_hits,
                total_misses=self._total_misses,
                hit_rate=hit_rate,
                total_entries=len(self._cache),
                total_size=self._current_size,
                avg_size=avg_size,
                oldest_entry=oldest,
                newest_entry=newest
            )
    
    def get_access_patterns(self, limit: int = 20) -> List[AccessPattern]:
        """获取访问模式"""
        with self._lock:
            sorted_access = sorted(
                self._access_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            patterns = []
            for key, count in sorted_access[:limit]:
                if key in self._cache:
                    entry = self._cache[key]
                    patterns.append(AccessPattern(
                        key=key,
                        access_count=count,
                        last_access=entry.last_access_time,
                        avg_access_interval=0.0
                    ))
            
            return patterns
    
    def get_optimization_suggestions(self) -> List[CacheSuggestion]:
        """获取优化建议"""
        suggestions = []
        stats = self.get_statistics()
        
        if stats.hit_rate < 50:
            suggestions.append(CacheSuggestion(
                category="hit_rate",
                issue="Low cache hit rate",
                suggestion=f"Current hit rate: {stats.hit_rate:.1f}%. Consider increasing cache size or adjusting TTL",
                priority=1,
                expected_improvement="high"
            ))
        
        if stats.total_entries >= self._max_entries * 0.9:
            suggestions.append(CacheSuggestion(
                category="capacity",
                issue="Cache nearing capacity",
                suggestion=f"Entries: {stats.total_entries}/{self._max_entries}. Consider increasing max entries",
                priority=2,
                expected_improvement="medium"
            ))
        
        if stats.total_size >= self._max_size * 0.9:
            suggestions.append(CacheSuggestion(
                category="size",
                issue="Cache size nearly full",
                suggestion=f"Size: {stats.total_size / (1024*1024):.1f}MB/{self._max_size / (1024*1024):.1f}MB. Consider increasing max size",
                priority=2,
                expected_improvement="medium"
            ))
        
        if stats.avg_size > 100 * 1024:
            suggestions.append(CacheSuggestion(
                category="entry_size",
                issue="Large cache entries",
                suggestion=f"Average entry size: {stats.avg_size / 1024:.1f}KB. Consider compressing large values",
                priority=3,
                expected_improvement="medium"
            ))
        
        return suggestions


class CacheOptimizer:
    """缓存优化器"""
    
    def __init__(self):
        self._caches: Dict[str, OptimizedCache] = {}
        self._optimization_history: List[Dict[str, Any]] = []
    
    def create_cache(
        self,
        name: str,
        max_size: int = 100 * 1024 * 1024,
        max_entries: int = 10000,
        default_ttl: int = 3600,
        eviction_policy: CacheEvictionPolicy = CacheEvictionPolicy.LRU
    ) -> OptimizedCache:
        """创建缓存"""
        cache = OptimizedCache(
            max_size=max_size,
            max_entries=max_entries,
            default_ttl=default_ttl,
            eviction_policy=eviction_policy
        )
        self._caches[name] = cache
        return cache
    
    def get_cache(self, name: str) -> Optional[OptimizedCache]:
        """获取缓存"""
        return self._caches.get(name)
    
    def optimize_cache(
        self,
        name: str,
        level: CacheOptimizationLevel = CacheOptimizationLevel.BALANCED
    ) -> Dict[str, Any]:
        """优化缓存"""
        cache = self._caches.get(name)
        if not cache:
            return {"error": "Cache not found"}
        
        before_stats = cache.get_statistics()
        
        actions = []
        
        if level == CacheOptimizationLevel.CONSERVATIVE:
            cache.clear()
            actions.append("clear_expired")
        
        elif level == CacheOptimizationLevel.BALANCED:
            cache.clear()
            actions.append("clear_expired")
            actions.append("reset_statistics")
            cache._total_hits = 0
            cache._total_misses = 0
            cache._access_counts.clear()
        
        elif level == CacheOptimizationLevel.AGGRESSIVE:
            cache.clear()
            actions.append("clear_expired")
            actions.append("reset_statistics")
            actions.append("adjust_config")
            cache._total_hits = 0
            cache._total_misses = 0
            cache._access_counts.clear()
            cache._max_entries = int(cache._max_entries * 1.2)
            cache._max_size = int(cache._max_size * 1.2)
        
        after_stats = cache.get_statistics()
        
        result = {
            "timestamp": datetime.now(),
            "cache_name": name,
            "level": level.value,
            "actions": actions,
            "before": {
                "hit_rate": before_stats.hit_rate,
                "entries": before_stats.total_entries,
                "size": before_stats.total_size
            },
            "after": {
                "hit_rate": after_stats.hit_rate,
                "entries": after_stats.total_entries,
                "size": after_stats.total_size
            }
        }
        
        self._optimization_history.append(result)
        
        return result
    
    def optimize_all(
        self,
        level: CacheOptimizationLevel = CacheOptimizationLevel.BALANCED
    ) -> Dict[str, Any]:
        """优化所有缓存"""
        results = {}
        
        for name in self._caches:
            results[name] = self.optimize_cache(name, level)
        
        return results
    
    def get_all_statistics(self) -> Dict[str, CacheStatistics]:
        """获取所有缓存的统计"""
        stats = {}
        for name, cache in self._caches.items():
            stats[name] = cache.get_statistics()
        return stats
    
    def get_optimization_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取优化历史"""
        return self._optimization_history[-limit:]


_global_cache_optimizer: Optional[CacheOptimizer] = None


def get_cache_optimizer() -> CacheOptimizer:
    """获取全局缓存优化器"""
    global _global_cache_optimizer
    if _global_cache_optimizer is None:
        _global_cache_optimizer = CacheOptimizer()
    return _global_cache_optimizer
