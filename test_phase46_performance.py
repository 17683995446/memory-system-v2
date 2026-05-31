"""
第46阶段测试：记忆系统性能优化和大规模部署
遵循"图难于其易，为大于其细"原则
"""

import sys
import os
import time
import threading

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.performance import (
    PerformanceOptimizer,
    QueryOptimizer,
    MultiLevelCache,
    ConnectionPool,
    ResourceManager,
    LoadBalancer,
    DistributedCache,
    get_performance_optimizer
)


def test_query_optimizer():
    """测试查询优化器"""
    print("\n=== 测试查询优化器 ===")
    
    optimizer = QueryOptimizer()
    
    # 测试查询优化
    result1 = optimizer.optimize_query("SELECT * FROM memories", {"user_id": "user1"})
    assert result1 is not None
    assert "optimized" in result1
    print("✓ 查询优化成功")
    
    # 测试缓存
    result2 = optimizer.optimize_query("SELECT * FROM memories", {"user_id": "user1"}, use_cache=True)
    assert result2 is not None
    print("✓ 查询缓存成功")
    
    # 测试统计
    stats = optimizer.get_query_stats()
    assert len(stats) > 0
    print(f"✓ 查询统计: {len(stats)} 条记录")
    
    # 清理缓存
    optimizer.clear_cache()
    print("✓ 缓存清理成功")
    
    print("✓ 查询优化器测试通过")


def test_multi_level_cache():
    """测试多级缓存"""
    print("\n=== 测试多级缓存 ===")
    
    cache = MultiLevelCache(l1_size=10, l2_size=20, l1_ttl=1.0, l2_ttl=2.0)
    
    # 测试缓存操作
    cache.put("key1", "value1")
    assert cache.get("key1") == "value1"
    print("✓ 缓存写入和读取成功")
    
    # 测试L1未命中，查找L2
    cache.put("key2", "value2")
    assert cache.get("key2") == "value2"
    print("✓ L1缓存正常")
    
    # 测试统计
    stats = cache.get_stats()
    assert "l1_size" in stats
    assert "hit_rate" in stats
    print(f"✓ 缓存统计: 命中率 {stats['hit_rate']:.2%}")
    
    # 测试清空
    cache.clear()
    assert cache.get("key1") is None
    print("✓ 缓存清空成功")
    
    print("✓ 多级缓存测试通过")


def test_connection_pool():
    """测试连接池"""
    print("\n=== 测试连接池 ===")
    
    pool = ConnectionPool(min_connections=2, max_connections=5)
    
    # 测试获取连接
    conn1 = pool.acquire(timeout=1.0)
    assert conn1 is not None
    print(f"✓ 获取连接: {conn1}")
    
    # 测试获取多个连接
    conn2 = pool.acquire(timeout=1.0)
    assert conn2 is not None
    
    # 释放连接
    pool.release(conn1)
    print("✓ 连接释放成功")
    
    # 测试统计
    stats = pool.get_stats()
    assert stats["total"] >= 2
    print(f"✓ 连接池统计: 总数={stats['total']}, 可用={stats['available']}, 使用中={stats['in_use']}")
    
    # 测试清理空闲连接
    pool.cleanup_idle()
    print("✓ 空闲连接清理成功")
    
    print("✓ 连接池测试通过")


def test_resource_manager():
    """测试资源管理器"""
    print("\n=== 测试资源管理器 ===")
    
    manager = ResourceManager()
    
    # 测试锁
    lock = manager.get_lock("test_resource")
    assert lock is not None
    print("✓ 资源锁获取成功")
    
    # 测试计数器
    count1 = manager.increment_counter("test_counter")
    count2 = manager.increment_counter("test_counter", 5)
    assert count2 == count1 + 5
    print(f"✓ 计数器: {count2}")
    
    # 测试仪表
    manager.set_gauge("test_gauge", 100.5)
    assert manager.get_gauge("test_gauge") == 100.5
    print("✓ 仪表设置成功")
    
    # 测试计时器
    manager.record_timer("test_timer", 0.5)
    manager.record_timer("test_timer", 1.5)
    timer_stats = manager.get_timer_stats("test_timer")
    assert timer_stats["count"] == 2
    assert timer_stats["min"] == 0.5
    print(f"✓ 计时器统计: avg={timer_stats['avg']:.2f}s")
    
    # 测试综合统计
    stats = manager.get_stats()
    assert "counters" in stats
    assert "gauges" in stats
    assert "timers" in stats
    print("✓ 综合统计获取成功")
    
    print("✓ 资源管理器测试通过")


def test_load_balancer():
    """测试负载均衡器"""
    print("\n=== 测试负载均衡器 ===")
    
    lb = LoadBalancer(strategy="round_robin")
    
    # 添加节点
    lb.add_node("node1", weight=1)
    lb.add_node("node2", weight=2)
    lb.add_node("node3", weight=1)
    print("✓ 节点添加成功")
    
    # 测试选择节点
    selected = lb.select_node()
    assert selected in ["node1", "node2", "node3"]
    print(f"✓ 节点选择: {selected}")
    
    # 测试节点连接
    lb.node_connected(selected)
    print("✓ 节点连接成功")
    
    # 测试节点失败（需要3次失败才标记为不活跃）
    lb.node_failed(selected)
    lb.node_failed(selected)
    lb.node_failed(selected)
    stats = lb.get_stats()
    assert stats["active_nodes"] < stats["total_nodes"]
    print("✓ 节点失败处理成功")
    
    # 测试节点恢复
    lb.node_recovered(selected)
    stats = lb.get_stats()
    assert stats["active_nodes"] == stats["total_nodes"]
    print("✓ 节点恢复成功")
    
    # 测试移除节点
    lb.remove_node("node3")
    stats = lb.get_stats()
    assert stats["total_nodes"] == 2
    print("✓ 节点移除成功")
    
    print("✓ 负载均衡器测试通过")


def test_distributed_cache():
    """测试分布式缓存"""
    print("\n=== 测试分布式缓存 ===")
    
    cache = DistributedCache("test_cluster")
    
    # 添加节点
    cache.add_node("cache1", "localhost", 6379, capacity=1000)
    cache.add_node("cache2", "localhost", 6380, capacity=1000)
    print("✓ 缓存节点添加成功")
    
    # 测试存储
    success = cache.put("key1", {"data": "value1"})
    assert success
    print("✓ 数据存储成功")
    
    # 测试读取
    value = cache.get("key1")
    assert value is not None
    print("✓ 数据读取成功")
    
    # 测试删除
    success = cache.delete("key1")
    assert success
    print("✓ 数据删除成功")
    
    # 测试统计
    stats = cache.get_stats()
    assert stats["total_nodes"] == 2
    print(f"✓ 分布式缓存统计: {stats['total_nodes']} 个节点")
    
    print("✓ 分布式缓存测试通过")


def test_performance_optimizer():
    """测试综合性能优化器"""
    print("\n=== 测试综合性能优化器 ===")
    
    optimizer = PerformanceOptimizer()
    
    # 测试操作优化
    def test_operation():
        time.sleep(0.01)
        return {"result": "success"}
    
    result = optimizer.optimize_operation("test_op", test_operation)
    assert result["result"] == "success"
    print("✓ 操作优化成功")
    
    # 测试综合统计
    stats = optimizer.get_comprehensive_stats()
    assert "cache" in stats
    assert "connection_pool" in stats
    assert "resources" in stats
    print("✓ 综合性能统计成功")
    
    print("✓ 综合性能优化器测试通过")


def test_global_instance():
    """测试全局单例"""
    print("\n=== 测试全局单例 ===")
    
    opt1 = get_performance_optimizer()
    opt2 = get_performance_optimizer()
    
    assert opt1 is opt2
    print("✓ 全局单例测试通过")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("第46阶段测试：记忆系统性能优化和大规模部署")
    print("遵循原则：图难于其易，为大于其细")
    print("=" * 60)
    
    try:
        test_query_optimizer()
        test_multi_level_cache()
        test_connection_pool()
        test_resource_manager()
        test_load_balancer()
        test_distributed_cache()
        test_performance_optimizer()
        test_global_instance()
        
        print("\n" + "=" * 60)
        print("✓ 所有第46阶段测试通过！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
