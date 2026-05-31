"""
第32阶段测试: 性能优化与缓存系统
测试已集成的缓存功能
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.cache import LRUCache, get_cache_system, MultiLevelCache


def test_lru_cache():
    """测试LRU缓存"""
    print("\n" + "=" * 70)
    print("测试 1：LRU缓存")
    print("=" * 70)

    cache = LRUCache()

    # 添加测试
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.set("key3", "value3")
    print("✓ 添加3个缓存条目")

    # 获取测试
    value1 = cache.get("key1")
    assert value1 == "value1"
    print("✓ 获取缓存成功")

    # 统计
    stats = cache.get_stats()
    print(f"  缓存统计:")
    print(f"    大小: {stats['size']}")
    print(f"    命中率: {stats['hit_rate']:.2f}%")
    print(f"    命中数: {stats['hits']}")
    print(f"    未命中: {stats['misses']}")

    print("\n✓ LRU缓存测试通过!")
    return True


def test_multi_level_cache():
    """测试多级缓存"""
    print("\n" + "=" * 70)
    print("测试 2：多级缓存")
    print("=" * 70)

    cache = MultiLevelCache()

    # L1缓存
    cache.set("key1", "value1_l1")
    print("✓ L1缓存设置成功")

    # L2缓存
    cache.set("key2", "value2_l2")
    print("✓ L2缓存设置成功")

    # 获取测试
    value1 = cache.get("key1")
    assert value1 == "value1_l1"
    print("✓ L1缓存获取成功")

    value2 = cache.get("key2")
    assert value2 == "value2_l2"
    print("✓ L2缓存获取成功")

    # 统计
    stats = cache.get_stats()
    print(f"\n  多级缓存统计:")
    print(f"    L1 大小: {stats['l1']['size']}")
    print(f"    L2 大小: {stats['l2']['size']}")
    print(f"    总大小: {stats['total']['size']}")

    # 清空
    result = cache.clear()
    print(f"\n✓ 清空缓存成功: {result}")

    print("\n✓ 多级缓存测试通过!")
    return True


def test_cache_system():
    """测试全局缓存系统"""
    print("\n" + "=" * 70)
    print("测试 3：全局缓存系统")
    print("=" * 70)

    cache = get_cache_system()

    # 添加一些缓存
    for i in range(10):
        cache.set(f"key_{i}", f"value_{i}")
    print("✓ 添加10个缓存条目")

    # 获取统计
    stats = cache.get_stats()
    print(f"\n  全局缓存统计:")
    print(f"    L1: {stats['l1']['size']} 条, 命中率: {stats['l1']['hit_rate']:.2f}%")
    print(f"    L2: {stats['l2']['size']} 条, 命中率: {stats['l2']['hit_rate']:.2f}%")

    # 清空
    result = cache.clear()
    print(f"\n✓ 全局缓存已清空: {result}")

    print("\n✓ 全局缓存系统测试通过!")
    return True


def test_cache_integration():
    """测试缓存与记忆系统集成"""
    print("\n" + "=" * 70)
    print("测试 4：缓存与记忆系统集成")
    print("=" * 70)

    from src.memory import get_memory_system
    from src.cache.memory_cache import CachedMemorySystem

    # 创建基础记忆系统
    base_system = get_memory_system()

    # 创建带缓存的记忆系统
    cached_system = CachedMemorySystem(base_system)

    # 添加记忆
    mem_id = cached_system.add("这是集成测试记忆", "test", "l2")
    assert mem_id is not None
    print(f"✓ 添加记忆成功: {mem_id}")

    # 召回记忆（首次，无缓存）
    result1 = cached_system.recall("集成测试")
    print(f"✓ 首次召回: {len(result1)} 条")

    # 再次召回（有缓存）
    result2 = cached_system.recall("集成测试")
    print(f"✓ 缓存召回: {len(result2)} 条")

    # 获取缓存统计
    cache_stats = cached_system.get_cache_stats()
    print(f"\n  缓存统计:")
    print(f"    召回缓存命中率: {cache_stats['recall']['hit_rate']:.2f}%")
    print(f"    缓存失效次数: {cache_stats['invalidations']}")

    # 清空缓存
    result = cached_system.clear_cache()
    print(f"\n✓ 清空缓存: {result}")

    print("\n✓ 缓存集成测试通过!")
    return True


def test_cache_performance():
    """测试缓存性能"""
    print("\n" + "=" * 70)
    print("测试 5：缓存性能测试")
    print("=" * 70)

    cache = get_cache_system()

    # 添加测试数据
    print("添加测试数据...")
    for i in range(100):
        cache.set(f"perf_key_{i}", {"data": f"value_{i}", "index": i})

    # 测试读取性能
    print("\n读取性能测试:")

    # 无缓存读取（首次）
    start = time.time()
    for i in range(50):
        cache.get(f"perf_key_{i % 100}")
        cache.l1_cache._cache.clear()  # 清除L1缓存
    first_read = time.time() - start
    print(f"  首次读取 (无缓存): {first_read:.4f}秒")

    # 有缓存读取
    start = time.time()
    for i in range(50):
        cache.get(f"perf_key_{i % 100}")
    cached_read = time.time() - start
    print(f"  缓存读取: {cached_read:.4f}秒")

    # 性能提升
    if first_read > 0:
        speedup = first_read / cached_read if cached_read > 0 else 1.0
        print(f"\n  性能提升: {speedup:.2f}x")

    # 获取最终统计
    stats = cache.get_stats()
    print(f"\n  最终缓存统计:")
    print(f"    L1 命中率: {stats['l1']['hit_rate']:.2f}%")
    print(f"    L2 命中率: {stats['l2']['hit_rate']:.2f}%")

    print("\n✓ 缓存性能测试完成!")
    return True


def main():
    """主测试函数"""
    print("\n" + "=" * 70)
    print("第32阶段测试: 性能优化与缓存系统")
    print("=" * 70)

    all_passed = True

    tests = [
        ("LRU缓存", test_lru_cache),
        ("多级缓存", test_multi_level_cache),
        ("全局缓存系统", test_cache_system),
        ("缓存与记忆系统集成", test_cache_integration),
        ("缓存性能测试", test_cache_performance),
    ]

    for test_name, test_func in tests:
        try:
            passed = test_func()
            if not passed:
                all_passed = False
        except Exception as e:
            print(f"\n✗ {test_name}失败: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print("✓ 所有性能测试通过!")
    else:
        print("✗ 部分测试失败")
    print("=" * 70)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
