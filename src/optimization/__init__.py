"""
系统优化模块
包含内存优化、缓存优化和查询优化
"""

from .memory_optimizer import (
    MemoryOptimizer,
    MemoryOptimizationLevel,
    MemoryUsage,
    ObjectLeak,
    OptimizationSuggestion,
    get_memory_optimizer
)

from .cache_optimizer import (
    CacheOptimizer,
    OptimizedCache,
    CacheEvictionPolicy,
    CacheOptimizationLevel,
    CacheStatistics,
    CacheSuggestion,
    get_cache_optimizer
)

from .query_optimizer import (
    QueryOptimizer,
    QueryAnalyzer,
    QueryType,
    OptimizationStrategy,
    QueryAnalysis,
    QueryPattern,
    get_query_analyzer,
    get_query_optimizer
)

__all__ = [
    'MemoryOptimizer',
    'MemoryOptimizationLevel',
    'MemoryUsage',
    'ObjectLeak',
    'OptimizationSuggestion',
    'CacheOptimizer',
    'OptimizedCache',
    'CacheEvictionPolicy',
    'CacheOptimizationLevel',
    'CacheStatistics',
    'CacheSuggestion',
    'QueryOptimizer',
    'QueryAnalyzer',
    'QueryType',
    'OptimizationStrategy',
    'QueryAnalysis',
    'QueryPattern',
    'get_memory_optimizer',
    'get_cache_optimizer',
    'get_query_analyzer',
    'get_query_optimizer'
]
