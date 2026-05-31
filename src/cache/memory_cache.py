"""
记忆系统缓存集成
将缓存与记忆系统无缝集成
"""

from typing import Dict, Any, Optional
import hashlib
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MemoryCacheConfig:
    """记忆缓存配置"""
    enable_recall_cache: bool = True
    enable_fact_cache: bool = True
    recall_ttl: int = 300
    fact_ttl: int = 1800
    max_recall_entries: int = 1000
    max_fact_entries: int = 500


class CachedMemorySystem:
    """带缓存的记忆系统包装器"""
    
    def __init__(self, memory_system, cache=None, config=None):
        self.memory_system = memory_system
        self.config = config or MemoryCacheConfig()
        
        from src.cache import get_cache_system
        self.cache = cache or get_cache_system()
        
        self._stats = {
            'recall_cache_hits': 0,
            'recall_cache_misses': 0,
            'fact_cache_hits': 0,
            'fact_cache_misses': 0,
            'cache_invalidations': 0
        }
    
    def add(self, text: str, session_id: str = "default", level: str = "l2") -> str:
        """添加记忆并失效相关缓存"""
        result = self.memory_system.add(text, session_id, level)
        
        if self.config.enable_recall_cache:
            self._invalidate_recall_cache(session_id)
        
        return result
    
    def recall(self, query: str, session_id: str = "default") -> Dict[str, Any]:
        """召回记忆（优先从缓存）"""
        if not self.config.enable_recall_cache:
            return self.memory_system.recall(query, session_id)
        
        cache_key = self._get_recall_cache_key(query, session_id)
        cached = self.cache.get(cache_key)
        
        if cached is not None:
            self._stats['recall_cache_hits'] += 1
            return cached
        
        self._stats['recall_cache_misses'] += 1
        result = self.memory_system.recall(query, session_id)
        
        self.cache.set(cache_key, result, ttl=self.config.recall_ttl)
        
        return result
    
    def add_fact(self, entity: str, attribute: str, value: str) -> str:
        """添加事实并失效相关缓存"""
        result = self.memory_system.add_fact(entity, attribute, value)
        
        if self.config.enable_fact_cache:
            self._invalidate_fact_cache(entity, attribute)
        
        return result
    
    def query_facts(
        self,
        entity: Optional[str] = None,
        attribute: Optional[str] = None
    ) -> Dict[str, Any]:
        """查询事实（优先从缓存）"""
        if not self.config.enable_fact_cache:
            return self.memory_system.query_facts(entity, attribute)
        
        cache_key = self._get_fact_cache_key(entity, attribute)
        cached = self.cache.get(cache_key)
        
        if cached is not None:
            self._stats['fact_cache_hits'] += 1
            return cached
        
        self._stats['fact_cache_misses'] += 1
        result = self.memory_system.query_facts(entity, attribute)
        
        self.cache.set(cache_key, result, ttl=self.config.fact_ttl)
        
        return result
    
    def _get_recall_cache_key(self, query: str, session_id: str) -> str:
        """获取召回缓存键"""
        return f"recall|{session_id}|{query}"
    
    def _get_fact_cache_key(
        self,
        entity: Optional[str],
        attribute: Optional[str]
    ) -> str:
        """获取事实缓存键"""
        return f"fact|{entity or '*'}|{attribute or '*'}"
    
    def _invalidate_recall_cache(self, session_id: str) -> int:
        """失效召回缓存"""
        count = self.cache.invalidate_pattern(f"recall|{session_id}|")
        self._stats['cache_invalidations'] += count
        return count
    
    def _invalidate_fact_cache(
        self,
        entity: Optional[str],
        attribute: Optional[str]
    ) -> int:
        """失效事实缓存"""
        pattern = "fact|"
        if entity:
            pattern += f"{entity}|"
        elif attribute:
            pattern += f"*|{attribute}"
        else:
            pattern += "*"
        
        count = self.cache.invalidate_pattern(pattern)
        self._stats['cache_invalidations'] += count
        return count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        cache_stats = self.cache.get_stats()
        
        total_recall = self._stats['recall_cache_hits'] + self._stats['recall_cache_misses']
        recall_hit_rate = (
            (self._stats['recall_cache_hits'] / total_recall * 100)
            if total_recall > 0 else 0
        )
        
        total_fact = self._stats['fact_cache_hits'] + self._stats['fact_cache_misses']
        fact_hit_rate = (
            (self._stats['fact_cache_hits'] / total_fact * 100)
            if total_fact > 0 else 0
        )
        
        return {
            'recall': {
                'hits': self._stats['recall_cache_hits'],
                'misses': self._stats['recall_cache_misses'],
                'hit_rate': recall_hit_rate
            },
            'fact': {
                'hits': self._stats['fact_cache_hits'],
                'misses': self._stats['fact_cache_misses'],
                'hit_rate': fact_hit_rate
            },
            'invalidations': self._stats['cache_invalidations'],
            'cache_layers': cache_stats
        }
    
    def clear_cache(self) -> Dict[str, int]:
        """清空缓存"""
        return self.cache.clear()
    
    def warmup_cache(self, common_queries=None, session_id="default") -> Dict[str, Any]:
        """缓存预热 - 预先缓存常见查询"""
        warmup_stats = {
            'queries_warmed': 0,
            'total_time_ms': 0,
            'success': True
        }
        
        import time
        start_time = time.time()
        
        try:
            if common_queries is None:
                # 默认预热：获取最近的记忆并生成相关查询
                common_queries = [
                    "最近",
                    "重要",
                    "记忆"
                ]
            
            for query in common_queries:
                try:
                    self.recall(query, session_id)
                    warmup_stats['queries_warmed'] += 1
                except Exception as e:
                    logger.warning(f"预热查询失败: {query}, 错误: {e}")
            
            warmup_stats['total_time_ms'] = (time.time() - start_time) * 1000
            
        except Exception as e:
            warmup_stats['success'] = False
            warmup_stats['error'] = str(e)
            logger.error(f"缓存预热失败: {e}")
        
        return warmup_stats
    
    def __getattr__(self, name):
        """委托其他方法给底层记忆系统"""
        return getattr(self.memory_system, name)


def create_cached_memory_system(
    memory_system,
    enable_caching: bool = True,
    config: Optional[MemoryCacheConfig] = None
) -> Any:
    """创建带缓存的记忆系统"""
    if not enable_caching:
        return memory_system
    return CachedMemorySystem(memory_system, config=config)
