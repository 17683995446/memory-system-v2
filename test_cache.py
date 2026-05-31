"""
缓存系统测试
验证缓存功能、性能提升
"""

import sys
import os
import time
from typing import Dict, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.cache import get_cache_system, get_lru_cache
from src.cache.memory_cache import CachedMemorySystem, create_cached_memory_system
from src.cache.performance import get_performance_monitor, benchmark_function, format_stats
from src.memory import get_memory_system


def test_lru_cache_basic():
    """测试LRU缓存基本功能"""
    print("\n" + "=" * 60)
    print("测试 LRU 缓存")
    print("=" * 60)
    
    cache = get_lru_cache()
    
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.set("key3", "value3")
    
    assert cache.get("key1") == "value1"
    assert cache.get("key2") == "value2"
    assert cache.get("key3") == "value3"
    print(f"✓ 缓存设置与获取: 通过")
    
    stats = cache.get_stats()
    assert stats['hits'] == 3
    print(f"✓ 缓存命中: {stats['hits']} 次")
    
    cache.delete("key2")
    assert cache.get("key2") is None
    print(f"✓ 缓存删除: 通过")
    
    cache.clear()
    assert len(cache._cache) == 0
    print(f"✓ 缓存清空: 通过")
    
    return True


def test_lru_eviction():
    """测试LRU驱逐策略"""
    print("\n" + "=" * 60)
    print("测试 LRU 驱逐策略")
    print("=" * 60)
    
    from src.cache import CacheConfig, LRUCache
    
    config = CacheConfig(max_size=5)
    cache = LRUCache[str](config)
    
    for i in range(10):
        cache.set(f"key{i}", f"value{i}")
    
    stats = cache.get_stats()
    assert stats['evictions'] >= 5
    print(f"✓ LRU驱逐: {stats['evictions']} 次")
    
    recent_keys = list(cache._cache.keys())
    assert "key0" not in recent_keys
    print(f"✓ 最久未使用被驱逐: 通过")
    
    return True


def test_multilevel_cache():
    """测试多级缓存"""
    print("\n" + "=" * 60)
    print("测试多级缓存")
    print("=" * 60)
    
    cache = get_cache_system()
    
    cache.set("test_key", "test_value")
    
    value1 = cache.get("test_key")
    value2 = cache.get("test_key")
    
    assert value1 == value2 == "test_value"
    
    stats = cache.get_stats()
    print(f"✓ L1缓存命中: {stats['l1']['hits']}")
    print(f"✓ L2缓存命中: {stats['l2']['hits']}")
    
    return True


def test_memory_cache_integration():
    """测试记忆缓存集成"""
    print("\n" + "=" * 60)
    print("测试记忆缓存集成")
    print("=" * 60)
    
    memory_system = get_memory_system()
    cached = create_cached_memory_system(memory_system)
    
    for i in range(10):
        cached.add(f"记忆内容{i}", "session_test", "l2")
    
    print(f"✓ 记忆添加: 10条")
    
    query = "记忆"
    
    result1 = cached.recall(query, "session_test")
    result2 = cached.recall(query, "session_test")
    result3 = cached.recall(query, "session_test")
    
    assert result1 == result2 == result3
    
    stats = cached.get_cache_stats()
    print(f"✓ 召回缓存命中: {stats['recall']['hits']}")
    print(f"✓ 召回缓存缺失: {stats['recall']['misses']}")
    
    return True


def test_performance_improvement():
    """测试缓存性能提升"""
    print("\n" + "=" * 60)
    print("测试缓存性能提升")
    print("=" * 60)
    
    memory_system = get_memory_system()
    cached = create_cached_memory_system(memory_system)
    
    for i in range(50):
        cached.add(f"性能测试{i}", "perf_session", "l2")
    
    print(f"准备数据: 50条记忆")
    
    def no_cache_recall():
        memory_system.recall("性能", "perf_session")
    
    def with_cache_recall():
        cached.recall("性能", "perf_session")
    
    print("\n无缓存基准测试...")
    no_cache_stats = benchmark_function(no_cache_recall, iterations=500)
    
    print("\n带缓存测试...")
    cached.recall("性能", "perf_session")
    with_cache_stats = benchmark_function(with_cache_recall, iterations=500)
    
    print("\n无缓存:")
    print(format_stats(no_cache_stats, ""))
    print("\n带缓存:")
    print(format_stats(with_cache_stats, ""))
    
    improvement = (no_cache_stats.avg_ms / with_cache_stats.avg_ms - 1) * 100
    print(f"\n✓ 性能提升: {improvement:.1f}%")
    
    assert with_cache_stats.avg_ms <= no_cache_stats.avg_ms
    
    return True


def test_cache_invalidation():
    """测试缓存失效"""
    print("\n" + "=" * 60)
    print("测试缓存失效")
    print("=" * 60)
    
    memory_system = get_memory_system()
    cached = create_cached_memory_system(memory_system)
    
    cached.add("内容A", "session_inv", "l2")
    result1 = cached.recall("内容", "session_inv")
    
    cached.add("内容B", "session_inv", "l2")
    result2 = cached.recall("内容", "session_inv")
    
    stats = cached.get_cache_stats()
    print(f"✓ 缓存失效次数: {stats['invalidations']}")
    print(f"✓ 缓存命中: {stats['recall']['hits']}")
    
    assert stats['invalidations'] >= 1
    
    return True


def main():
    """运行所有缓存测试"""
    tests = [
        ("LRU缓存", test_lru_cache_basic),
        ("LRU驱逐", test_lru_eviction),
        ("多级缓存", test_multilevel_cache),
        ("记忆缓存", test_memory_cache_integration),
        ("缓存失效", test_cache_invalidation),
        ("性能提升", test_performance_improvement)
    ]
    
    results = []
    for name, test in tests:
        try:
            passed = test()
            results.append((name, passed, None))
        except Exception as e:
            results.append((name, False, str(e)))
    
    print("\n" + "=" * 60)
    print("缓存系统测试汇总")
    print("=" * 60)
    
    for name, passed, error in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"\n{status}: {name}")
        if error:
            print(f"  错误: {error}")
    
    passed_count = sum(1 for _, p, _ in results if p)
    print(f"\n总计: {passed_count}/{len(tests)} 测试通过")
    
    return passed_count == len(tests)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
