#!/usr/bin/env python3
"""
第52阶段测试：系统优化与性能调优
测试内存优化、缓存优化和查询优化功能
"""

import sys
import time
import unittest
from datetime import datetime
from src.optimization import (
    MemoryOptimizer,
    MemoryOptimizationLevel,
    CacheOptimizer,
    OptimizedCache,
    CacheEvictionPolicy,
    CacheOptimizationLevel,
    QueryOptimizer,
    QueryAnalyzer,
    QueryType,
    get_memory_optimizer,
    get_cache_optimizer,
    get_query_analyzer,
    get_query_optimizer
)


class TestMemoryOptimizer(unittest.TestCase):
    """内存优化器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.optimizer = MemoryOptimizer()
    
    def test_get_current_memory_usage(self):
        """测试获取内存使用情况"""
        usage = self.optimizer.get_current_memory_usage()
        
        self.assertIsNotNone(usage)
        self.assertIsInstance(usage.timestamp, datetime)
        self.assertGreater(usage.object_count, 0)
        self.assertGreater(usage.total_allocated, 0)
    
    def test_memory_tracing(self):
        """测试内存追踪"""
        self.optimizer.start_tracing()
        
        test_data = [x for x in range(10000)]
        
        usage = self.optimizer.get_current_memory_usage()
        self.assertIsNotNone(usage)
        
        del test_data
        
        self.optimizer.stop_tracing()
    
    def test_optimize_memory(self):
        """测试内存优化"""
        result = self.optimizer.optimize_memory(MemoryOptimizationLevel.LIGHT)
        
        self.assertIsNotNone(result)
        self.assertIn("light_gc_collect", result["actions"])
        self.assertIsNotNone(result["before"])
        self.assertIsNotNone(result["after"])
    
    def test_object_pool(self):
        """测试对象池"""
        class TestObject:
            def __init__(self):
                self.data = None
        
        pool = self.optimizer.create_object_pool(TestObject, preallocate_count=5)
        
        self.assertEqual(len(pool["available"]), 5)
        
        obj = self.optimizer.get_from_pool(pool)
        self.assertIsNotNone(obj)
        
        self.optimizer.return_to_pool(pool, obj)
        self.assertEqual(len(pool["available"]), 5)
    
    def test_optimization_suggestions(self):
        """测试优化建议"""
        self.optimizer.get_current_memory_usage()
        
        suggestions = self.optimizer.get_optimization_suggestions()
        
        self.assertIsInstance(suggestions, list)
    
    def test_usage_trend(self):
        """测试使用趋势"""
        for _ in range(3):
            self.optimizer.get_current_memory_usage()
            time.sleep(0.1)
        
        trend = self.optimizer.get_usage_trend(minutes=1)
        
        self.assertIsNotNone(trend)
        self.assertIn("data_points", trend)
        self.assertIn("trend", trend)


class TestCacheOptimizer(unittest.TestCase):
    """缓存优化器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.optimizer = CacheOptimizer()
    
    def test_create_cache(self):
        """测试创建缓存"""
        cache = self.optimizer.create_cache(
            name="test_cache",
            max_size=10 * 1024 * 1024,
            max_entries=1000
        )
        
        self.assertIsNotNone(cache)
    
    def test_cache_get_set(self):
        """测试缓存读写"""
        cache = self.optimizer.create_cache(name="test_cache")
        
        cache.set("key1", "value1")
        value = cache.get("key1")
        
        self.assertEqual(value, "value1")
    
    def test_cache_statistics(self):
        """测试缓存统计"""
        cache = self.optimizer.create_cache(name="test_cache")
        
        cache.set("key1", "value1")
        cache.get("key1")
        cache.get("key2", "default")
        
        stats = cache.get_statistics()
        
        self.assertEqual(stats.total_hits, 1)
        self.assertEqual(stats.total_misses, 1)
        self.assertEqual(stats.hit_rate, 50.0)
        self.assertEqual(stats.total_entries, 1)
    
    def test_cache_eviction(self):
        """测试缓存驱逐"""
        cache = self.optimizer.create_cache(
            name="small_cache",
            max_size=1024,
            max_entries=5
        )
        
        for i in range(10):
            cache.set(f"key{i}", f"value{i}")
        
        stats = cache.get_statistics()
        self.assertLessEqual(stats.total_entries, 5)
    
    def test_access_patterns(self):
        """测试访问模式"""
        cache = self.optimizer.create_cache(name="test_cache")
        
        for i in range(3):
            cache.set(f"key{i}", f"value{i}")
        
        for i in range(10):
            cache.get("key0")
            cache.get("key1")
        
        patterns = cache.get_access_patterns()
        
        self.assertGreater(len(patterns), 0)
    
    def test_optimization_suggestions(self):
        """测试优化建议"""
        cache = self.optimizer.create_cache(name="test_cache")
        
        for i in range(100):
            cache.get(f"key{i}")
        
        suggestions = cache.get_optimization_suggestions()
        
        self.assertIsInstance(suggestions, list)
    
    def test_optimize_cache(self):
        """测试优化缓存"""
        cache = self.optimizer.create_cache(name="test_cache")
        
        for i in range(10):
            cache.set(f"key{i}", f"value{i}")
        
        result = self.optimizer.optimize_cache(
            "test_cache",
            CacheOptimizationLevel.CONSERVATIVE
        )
        
        self.assertIsNotNone(result)
        self.assertIn("actions", result)


class TestQueryOptimizer(unittest.TestCase):
    """查询优化器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.analyzer = QueryAnalyzer()
        self.optimizer = QueryOptimizer(self.analyzer)
    
    def test_analyze_query(self):
        """测试分析查询"""
        query = "SELECT * FROM users WHERE age > 18"
        analysis = self.analyzer.analyze_query(
            query=query,
            execution_time=15.5,
            result_count=100
        )
        
        self.assertIsNotNone(analysis)
        self.assertEqual(analysis.query_type, QueryType.SELECT)
        self.assertEqual(analysis.execution_time_ms, 15.5)
        self.assertEqual(analysis.result_count, 100)
    
    def test_query_type_detection(self):
        """测试查询类型检测"""
        test_cases = [
            ("SELECT * FROM users", QueryType.SELECT),
            ("INSERT INTO users VALUES (1, 'test')", QueryType.INSERT),
            ("UPDATE users SET name='test'", QueryType.UPDATE),
            ("DELETE FROM users WHERE id=1", QueryType.DELETE)
        ]
        
        for query, expected_type in test_cases:
            analysis = self.analyzer.analyze_query(
                query=query,
                execution_time=10.0,
                result_count=1
            )
            self.assertEqual(analysis.query_type, expected_type)
    
    def test_slow_queries(self):
        """测试慢查询"""
        self.analyzer.analyze_query(
            query="SELECT * FROM big_table",
            execution_time=2000.0,
            result_count=10000
        )
        
        slow_queries = self.analyzer.get_slow_queries(threshold_ms=1000.0)
        
        self.assertGreater(len(slow_queries), 0)
    
    def test_query_patterns(self):
        """测试查询模式"""
        for i in range(15):
            self.analyzer.analyze_query(
                query=f"SELECT * FROM users WHERE id={i}",
                execution_time=5.0 + i,
                result_count=1
            )
        
        patterns = self.analyzer.get_frequent_patterns(min_count=5)
        
        self.assertGreater(len(patterns), 0)
    
    def test_optimize_query(self):
        """测试优化查询"""
        def executor(query):
            return [{"id": 1, "name": "test"}]
        
        result = self.optimizer.optimize_query(
            query="SELECT * FROM users WHERE id=1",
            executor=executor
        )
        
        self.assertIsNotNone(result)
    
    def test_suggest_optimizations(self):
        """测试优化建议"""
        suggestions = self.optimizer.suggest_optimizations(
            "SELECT * FROM users JOIN orders ON users.id = orders.user_id"
        )
        
        self.assertIsInstance(suggestions, list)
    
    def test_optimization_report(self):
        """测试优化报告"""
        for i in range(10):
            self.analyzer.analyze_query(
                query=f"SELECT * FROM users WHERE id={i}",
                execution_time=5.0 + i,
                result_count=1
            )
        
        report = self.optimizer.get_optimization_report()
        
        self.assertIsNotNone(report)
        self.assertIn("total_queries_analyzed", report)
        self.assertIn("slow_queries_count", report)


class TestGlobalOptimizers(unittest.TestCase):
    """全局优化器测试"""
    
    def test_get_memory_optimizer(self):
        """测试获取全局内存优化器"""
        optimizer1 = get_memory_optimizer()
        optimizer2 = get_memory_optimizer()
        
        self.assertIs(optimizer1, optimizer2)
    
    def test_get_cache_optimizer(self):
        """测试获取全局缓存优化器"""
        optimizer1 = get_cache_optimizer()
        optimizer2 = get_cache_optimizer()
        
        self.assertIs(optimizer1, optimizer2)
    
    def test_get_query_analyzer(self):
        """测试获取全局查询分析器"""
        analyzer1 = get_query_analyzer()
        analyzer2 = get_query_analyzer()
        
        self.assertIs(analyzer1, analyzer2)
    
    def test_get_query_optimizer(self):
        """测试获取全局查询优化器"""
        optimizer1 = get_query_optimizer()
        optimizer2 = get_query_optimizer()
        
        self.assertIs(optimizer1, optimizer2)


def run_tests():
    """运行测试"""
    print("=" * 70)
    print("第52阶段测试：系统优化与性能调优")
    print("=" * 70)
    
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    
    test_suite.addTests(test_loader.loadTestsFromTestCase(TestMemoryOptimizer))
    test_suite.addTests(test_loader.loadTestsFromTestCase(TestCacheOptimizer))
    test_suite.addTests(test_loader.loadTestsFromTestCase(TestQueryOptimizer))
    test_suite.addTests(test_loader.loadTestsFromTestCase(TestGlobalOptimizers))
    
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    print("\n" + "=" * 70)
    if result.wasSuccessful():
        print("✅ 所有测试通过！")
    else:
        print("❌ 部分测试失败！")
    print("=" * 70)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
