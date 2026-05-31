"""
记忆系统性能优化与缓存模块
基于第一性原理：确定性、性能、简洁性
"""

import os
import sys
import time
import json
import hashlib
import threading
from typing import Dict, List, Optional, Any, Callable
from collections import OrderedDict
from dataclasses import dataclass, field
from enum import Enum

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class CacheLevel(Enum):
    """缓存层级"""
    L1 = "l1"  # 进程内缓存，最快
    L2 = "l2"  # 进程间缓存
    L3 = "l3"  # 持久化缓存


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: float = field(default_factory=time.time)
    accessed_at: float = field(default_factory=time.time)
    access_count: int = 0
    size_bytes: int = 0

    def touch(self):
        """更新访问时间"""
        self.accessed_at = time.time()
        self.access_count += 1


class LRUCache:
    """LRU缓存实现"""

    def __init__(self, max_size: int = 1000, ttl_seconds: Optional[float] = None):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.lock = threading.RLock()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self.lock:
            if key not in self.cache:
                self.misses += 1
                return None

            entry = self.cache[key]

            # 检查TTL
            if self.ttl_seconds and (time.time() - entry.created_at) > self.ttl_seconds:
                del self.cache[key]
                self.misses += 1
                return None

            # 移到末尾（最近使用）
            self.cache.move_to_end(key)
            entry.touch()
            self.hits += 1

            return entry.value

    def set(self, key: str, value: Any):
        """设置缓存值"""
        with self.lock:
            # 计算大小（简化版）
            size = sys.getsizeof(json.dumps(value)) if not isinstance(value, str) else sys.getsizeof(value)

            # 如果已存在，更新值
            if key in self.cache:
                entry = self.cache[key]
                entry.value = value
                entry.size_bytes = size
                self.cache.move_to_end(key)
                return

            # 如果超过最大容量，删除最旧的
            while len(self.cache) >= self.max_size:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]

            # 添加新条目
            entry = CacheEntry(
                key=key,
                value=value,
                size_bytes=size
            )
            self.cache[key] = entry

    def delete(self, key: str) -> bool:
        """删除缓存条目"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False

    def clear(self):
        """清空缓存"""
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self.lock:
            total = self.hits + self.misses
            hit_rate = self.hits / total if total > 0 else 0.0
            total_size = sum(entry.size_bytes for entry in self.cache.values())

            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": hit_rate,
                "total_size_bytes": total_size,
            }


class QueryCache:
    """查询结果缓存"""

    def __init__(self, max_size: int = 500, ttl_seconds: float = 300):
        self.cache = LRUCache(max_size=max_size, ttl_seconds=ttl_seconds)
        self.query_times: Dict[str, float] = {}

    def _make_key(self, query: str, params: Optional[Dict] = None) -> str:
        """生成缓存键"""
        content = json.dumps({"query": query, "params": params or {}}, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()

    def get(self, query: str, params: Optional[Dict] = None) -> Optional[Any]:
        """获取查询结果"""
        key = self._make_key(query, params)
        return self.cache.get(key)

    def set(self, query: str, result: Any, params: Optional[Dict] = None):
        """设置查询结果"""
        key = self._make_key(query, params)
        self.cache.set(key, result)
        self.query_times[key] = time.time()

    def invalidate(self, query: str, params: Optional[Dict] = None):
        """使缓存失效"""
        key = self._make_key(query, params)
        self.cache.delete(key)
        if key in self.query_times:
            del self.query_times[key]

    def invalidate_all(self):
        """使所有缓存失效"""
        self.cache.clear()
        self.query_times.clear()

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self.cache.get_stats()
        stats["cached_queries"] = len(self.query_times)
        return stats


class MemoryCache:
    """记忆缓存层"""

    def __init__(self):
        self.l1_cache = LRUCache(max_size=500, ttl_seconds=60)  # 1分钟
        self.l2_cache = LRUCache(max_size=1000, ttl_seconds=300)  # 5分钟
        self.l3_cache = LRUCache(max_size=2000, ttl_seconds=3600)  # 1小时
        self.query_cache = QueryCache(max_size=500, ttl_seconds=300)

    def get_memory(self, memory_id: str) -> Optional[Any]:
        """获取记忆（按层级尝试）"""
        # L1
        value = self.l1_cache.get(memory_id)
        if value is not None:
            return value

        # L2
        value = self.l2_cache.get(memory_id)
        if value is not None:
            # 提升到L1
            self.l1_cache.set(memory_id, value)
            return value

        # L3
        value = self.l3_cache.get(memory_id)
        if value is not None:
            # 提升到L2
            self.l2_cache.set(memory_id, value)
            return value

        return None

    def set_memory(self, memory_id: str, value: Any, level: CacheLevel = CacheLevel.L2):
        """设置记忆缓存"""
        cache = {
            CacheLevel.L1: self.l1_cache,
            CacheLevel.L2: self.l2_cache,
            CacheLevel.L3: self.l3_cache,
        }.get(level, self.l2_cache)

        cache.set(memory_id, value)

    def invalidate_memory(self, memory_id: str):
        """使记忆缓存失效"""
        self.l1_cache.delete(memory_id)
        self.l2_cache.delete(memory_id)
        self.l3_cache.delete(memory_id)

    def get_query_result(self, query: str, params: Optional[Dict] = None) -> Optional[Any]:
        """获取查询结果"""
        return self.query_cache.get(query, params)

    def set_query_result(self, query: str, result: Any, params: Optional[Dict] = None):
        """设置查询结果"""
        self.query_cache.set(query, result, params)

    def invalidate_query(self, query: str, params: Optional[Dict] = None):
        """使查询缓存失效"""
        self.query_cache.invalidate(query, params)

    def get_all_stats(self) -> Dict[str, Any]:
        """获取所有统计"""
        return {
            "l1": self.l1_cache.get_stats(),
            "l2": self.l2_cache.get_stats(),
            "l3": self.l3_cache.get_stats(),
            "query": self.query_cache.get_stats(),
        }

    def clear_all(self):
        """清空所有缓存"""
        self.l1_cache.clear()
        self.l2_cache.clear()
        self.l3_cache.clear()
        self.query_cache.invalidate_all()


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}
        self.lock = threading.RLock()
        self.start_time = time.time()

    def record(self, metric_name: str, value: float):
        """记录指标"""
        with self.lock:
            if metric_name not in self.metrics:
                self.metrics[metric_name] = []
            self.metrics[metric_name].append(value)

            # 限制历史记录数量
            if len(self.metrics[metric_name]) > 10000:
                self.metrics[metric_name] = self.metrics[metric_name][-5000:]

    def get_stats(self, metric_name: str) -> Dict[str, float]:
        """获取指标统计"""
        with self.lock:
            if metric_name not in self.metrics or not self.metrics[metric_name]:
                return {}

            values = self.metrics[metric_name]
            return {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "recent_avg": sum(values[-100:]) / len(values[-100:]) if len(values) >= 100 else sum(values) / len(values),
            }

    def get_all_stats(self) -> Dict[str, Any]:
        """获取所有统计"""
        with self.lock:
            uptime = time.time() - self.start_time
            stats = {
                "uptime_seconds": uptime,
                "metrics": {}
            }

            for name in self.metrics:
                stats["metrics"][name] = self.get_stats(name)

            return stats

    def clear(self):
        """清空所有指标"""
        with self.lock:
            self.metrics.clear()
            self.start_time = time.time()


class PerformanceTimer:
    """性能计时器"""

    def __init__(self, monitor: PerformanceMonitor, metric_name: str):
        self.monitor = monitor
        self.metric_name = metric_name
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.time() - self.start_time
        self.monitor.record(self.metric_name, elapsed)

    def elapsed(self) -> float:
        """获取经过的时间"""
        if self.start_time is None:
            return 0.0
        return time.time() - self.start_time


class CachedMemorySystem:
    """带缓存的记忆系统（装饰器）"""

    def __init__(self, memory_system):
        self.memory_system = memory_system
        self.cache = MemoryCache()
        self.monitor = PerformanceMonitor()

    def add(self, content: str, source: str = "unknown", level: str = "l2") -> Optional[str]:
        """添加记忆"""
        with PerformanceTimer(self.monitor, "memory_add"):
            mem_id = self.memory_system.add(content, source, level)

            # 缓存新记忆
            if mem_id:
                memory_item = {
                    "id": mem_id,
                    "text": content,
                    "source": source,
                    "level": level,
                    "timestamp": time.time(),
                }
                self.cache.set_memory(mem_id, memory_item)

            # 使相关查询缓存失效
            self.cache.invalidate_query(content)

            return mem_id

    def get(self, memory_id: str) -> Optional[Any]:
        """获取记忆"""
        with PerformanceTimer(self.monitor, "memory_get"):
            # 先从缓存获取
            cached = self.cache.get_memory(memory_id)
            if cached is not None:
                return cached

            # 从系统获取
            memory = self.memory_system.get(memory_id)

            # 缓存结果
            if memory:
                self.cache.set_memory(memory_id, memory)

            return memory

    def search(self, query: str, **kwargs) -> List[Any]:
        """搜索记忆"""
        with PerformanceTimer(self.monitor, "memory_search"):
            # 先从缓存获取
            cached = self.cache.get_query_result(query, kwargs)
            if cached is not None:
                return cached

            # 执行搜索
            results = self.memory_system.search(query, **kwargs)

            # 缓存结果
            self.cache.set_query_result(query, results, kwargs)

            return results

    def recall(self, query: str, task_id: str = "default", **kwargs) -> Dict[str, List]:
        """召回记忆"""
        with PerformanceTimer(self.monitor, "memory_recall"):
            # 先从缓存获取
            cached = self.cache.get_query_result(f"recall_{query}", {"task_id": task_id})
            if cached is not None:
                return cached

            # 执行召回
            results = self.memory_system.recall(query, task_id, **kwargs)

            # 缓存结果
            self.cache.set_query_result(f"recall_{query}", results, {"task_id": task_id})

            return results

    def delete(self, memory_id: str) -> bool:
        """删除记忆"""
        with PerformanceTimer(self.monitor, "memory_delete"):
            # 使缓存失效
            self.cache.invalidate_memory(memory_id)

            # 执行删除
            return self.memory_system.delete(memory_id)

    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        return {
            "cache": self.cache.get_all_stats(),
            "performance": self.monitor.get_all_stats(),
        }

    def clear_cache(self):
        """清空缓存"""
        self.cache.clear_all()

    def __getattr__(self, name):
        """委托其他方法"""
        return getattr(self.memory_system, name)


# 全局实例
_global_cache = MemoryCache()
_global_monitor = PerformanceMonitor()


def get_memory_cache() -> MemoryCache:
    """获取全局内存缓存"""
    return _global_cache


def get_performance_monitor() -> PerformanceMonitor:
    """获取全局性能监控器"""
    return _global_monitor


def cached_query(cache: MemoryCache, query: str, func: Callable, params: Optional[Dict] = None):
    """带缓存的查询装饰器"""
    # 尝试从缓存获取
    cached_result = cache.get_query_result(query, params)
    if cached_result is not None:
        return cached_result

    # 执行查询
    result = func()

    # 缓存结果
    cache.set_query_result(query, result, params)

    return result
