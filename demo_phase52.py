#!/usr/bin/env python3
"""
第52阶段演示：系统优化与性能调优
演示内存优化、缓存优化和查询优化
"""

import time
from src.optimization import (
    MemoryOptimizer,
    MemoryOptimizationLevel,
    CacheOptimizer,
    CacheOptimizationLevel,
    CacheEvictionPolicy,
    QueryOptimizer,
    QueryAnalyzer,
    get_memory_optimizer,
    get_cache_optimizer,
    get_query_optimizer
)


def demo_memory_optimization():
    """演示内存优化"""
    print("\n" + "=" * 70)
    print("内存优化演示")
    print("=" * 70)
    
    optimizer = MemoryOptimizer()
    
    print("\n1. 获取当前内存使用情况")
    usage = optimizer.get_current_memory_usage()
    print(f"   对象数量: {usage.object_count}")
    print(f"   已分配内存: {(usage.total_allocated / (1024*1024)):.2f} MB")
    
    print("\n2. 分配一些测试数据")
    test_data = [f"test_string_{i}" for i in range(10000)]
    usage_after = optimizer.get_current_memory_usage()
    print(f"   对象数量: {usage_after.object_count}")
    
    print("\n3. 释放数据并运行GC")
    del test_data
    result = optimizer.optimize_memory(MemoryOptimizationLevel.MEDIUM)
    print(f"   执行的操作: {result['actions']}")
    print(f"   GC统计: {len(result['after'].gc_stats)} 代")
    
    print("\n4. 测试对象池")
    class TestObject:
        def __init__(self):
            self.data = []
    
    pool = optimizer.create_object_pool(TestObject, preallocate_count=10)
    print(f"   池大小: {len(pool['available'])}")
    
    obj = optimizer.get_from_pool(pool)
    print(f"   获取对象: {obj}")
    print(f"   池剩余: {len(pool['available'])}")
    
    optimizer.return_to_pool(pool, obj)
    print(f"   返回对象后池大小: {len(pool['available'])}")
    
    print("\n5. 获取优化建议")
    suggestions = optimizer.get_optimization_suggestions()
    print(f"   建议数量: {len(suggestions)}")
    for suggestion in suggestions[:3]:
        print(f"   - {suggestion.category}: {suggestion.issue}")


def demo_cache_optimization():
    """演示缓存优化"""
    print("\n" + "=" * 70)
    print("缓存优化演示")
    print("=" * 70)
    
    optimizer = CacheOptimizer()
    
    print("\n1. 创建LRU缓存")
    cache = optimizer.create_cache(
        name="user_cache",
        max_size=10 * 1024 * 1024,
        max_entries=100,
        default_ttl=300,
        eviction_policy=CacheEvictionPolicy.LRU
    )
    print(f"   缓存创建成功")
    
    print("\n2. 写入缓存数据")
    for i in range(50):
        cache.set(f"user_{i}", {"id": i, "name": f"User {i}"})
    print(f"   写入 50 条数据")
    
    print("\n3. 读取缓存数据")
    hits = 0
    misses = 0
    for i in range(75):
        result = cache.get(f"user_{i}", default=None)
        if result:
            hits += 1
        else:
            misses += 1
    print(f"   Hit: {hits}, Miss: {misses}")
    
    print("\n4. 获取缓存统计")
    stats = cache.get_statistics()
    print(f"   Hit率: {stats.hit_rate:.2f}%")
    print(f"   条目数: {stats.total_entries}")
    print(f"   总大小: {(stats.total_size / 1024):.2f} KB")
    
    print("\n5. 获取访问模式")
    patterns = cache.get_access_patterns(limit=5)
    print(f"   访问模式数量: {len(patterns)}")
    for pattern in patterns[:3]:
        print(f"   - {pattern.key}: {pattern.access_count} 次")
    
    print("\n6. 获取优化建议")
    suggestions = cache.get_optimization_suggestions()
    print(f"   建议数量: {len(suggestions)}")
    for suggestion in suggestions:
        print(f"   - {suggestion.issue}: {suggestion.suggestion}")
    
    print("\n7. 优化缓存")
    result = optimizer.optimize_cache("user_cache", CacheOptimizationLevel.BALANCED)
    print(f"   优化操作: {result['actions']}")


def demo_query_optimization():
    """演示查询优化"""
    print("\n" + "=" * 70)
    print("查询优化演示")
    print("=" * 70)
    
    analyzer = QueryAnalyzer()
    optimizer = QueryOptimizer(analyzer)
    
    print("\n1. 分析查询")
    test_queries = [
        ("SELECT * FROM users WHERE age > 18", 50, 200),
        ("SELECT * FROM users WHERE city = 'New York'", 80, 500),
        ("SELECT * FROM orders JOIN users ON orders.user_id = users.id", 120, 1000),
        ("SELECT * FROM users ORDER BY created_at LIMIT 100", 90, 100),
    ]
    
    for query, time_ms, result_count in test_queries:
        analysis = analyzer.analyze_query(query, time_ms, result_count)
        print(f"   类型: {analysis.query_type.value}")
        print(f"   执行时间: {analysis.execution_time_ms} ms")
        print(f"   结果数: {analysis.result_count}")
        print()
    
    print("2. 获取慢查询")
    slow_queries = analyzer.get_slow_queries(threshold_ms=100.0)
    print(f"   慢查询数量: {len(slow_queries)}")
    for q in slow_queries:
        print(f"   - {q.query_text[:50]}...: {q.execution_time_ms} ms")
    
    print("\n3. 获取频繁查询模式")
    for i in range(20):
        analyzer.analyze_query(
            f"SELECT * FROM users WHERE id = {i}",
            10 + i,
            1
        )
    
    patterns = analyzer.get_frequent_patterns(min_count=5)
    print(f"   频繁模式数量: {len(patterns)}")
    for p in patterns[:3]:
        print(f"   - 模式: {p.pattern[:40]}...")
        print(f"     执行次数: {p.count}")
        print(f"     平均时间: {p.avg_execution_time:.2f} ms")
    
    print("\n4. 查询优化建议")
    suggestions = optimizer.suggest_optimizations(
        "SELECT * FROM users JOIN orders ON users.id = orders.user_id"
    )
    print(f"   建议数量: {len(suggestions)}")
    for s in suggestions:
        print(f"   - 问题: {s.issue}")
        print(f"     建议: {s.suggestion}")
        print(f"     预期改进: {s.expected_improvement}")
    
    print("\n5. 优化查询执行")
    def mock_executor(query):
        time.sleep(0.01)
        return [{"id": 1, "name": "test"}]
    
    result = optimizer.optimize_query(
        "SELECT * FROM users WHERE id = 1",
        mock_executor
    )
    print(f"   查询执行完成: {result}")
    
    print("\n6. 获取优化报告")
    report = optimizer.get_optimization_report()
    print(f"   分析查询数: {report['total_queries_analyzed']}")
    print(f"   慢查询数: {report['slow_queries_count']}")
    print(f"   频繁模式数: {report['frequent_patterns_count']}")


def main():
    """主函数"""
    print("=" * 70)
    print("第52阶段演示：系统优化与性能调优")
    print("=" * 70)
    
    demo_memory_optimization()
    demo_cache_optimization()
    demo_query_optimization()
    
    print("\n" + "=" * 70)
    print("✅ 演示完成！")
    print("=" * 70)


if __name__ == "__main__":
    main()
