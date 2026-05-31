"""
第16阶段测试：记忆重要性/评分功能
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.memory import get_memory_system
from src.importance import (
    ImportanceManager,
    ImportanceLevel,
    EnhancedMemoryWithImportance
)


def test_importance_manager_basic():
    """测试重要性管理器基本功能"""
    print("\n" + "=" * 60)
    print("测试 1: 重要性管理器基本功能")
    print("=" * 60)

    # 清理测试数据
    test_path = "./data/test_importance_temp.json"
    if os.path.exists(test_path):
        os.remove(test_path)

    manager = ImportanceManager(test_path)

    # 设置重要性
    manager.set_importance(
        "mem_001",
        ImportanceLevel.HIGH,
        score=8.5,
        reason="关键项目文档"
    )
    manager.set_importance("mem_002", ImportanceLevel.CRITICAL, 10.0)
    manager.set_importance("mem_003", ImportanceLevel.MEDIUM)
    manager.set_importance("mem_004", ImportanceLevel.LOW)
    manager.set_importance("mem_005", ImportanceLevel.TRIVIAL)

    # 获取重要性
    importance_1 = manager.get_importance("mem_001")
    print(f"mem_001 重要性: {importance_1}")
    assert importance_1['level'] == 4
    assert importance_1['score'] == 8.5

    # 按重要性等级获取
    critical_mems = manager.get_memories_by_importance(ImportanceLevel.CRITICAL)
    print(f"CRITICAL 等级记忆: {critical_mems}")
    assert "mem_002" in critical_mems

    # 获取>=HIGH的记忆
    high_and_above = manager.get_memories_by_importance(
        ImportanceLevel.HIGH,
        min_level=True
    )
    print(f"HIGH 及以上等级记忆: {high_and_above}")
    assert len(high_and_above) == 2

    # 获取评分范围
    high_score_mems = manager.get_memories_by_score(8.0)
    print(f"评分 >= 8.0 的记忆: {high_score_mems}")
    assert len(high_score_mems) == 2

    # 统计
    stats = manager.get_importance_statistics()
    print(f"\n统计信息: {stats}")
    assert stats['total_memories_with_importance'] == 5
    assert stats['level_counts'][5] == 1

    # 移除重要性
    removed = manager.remove_importance("mem_005")
    assert removed

    # 清理
    os.remove(test_path)
    print("\n✓ 重要性管理器基本功能测试通过！")
    return True


def test_enhanced_memory_system():
    """测试增强记忆系统"""
    print("\n" + "=" * 60)
    print("测试 2: 增强记忆系统")
    print("=" * 60)

    # 清理测试数据
    test_path = "./data/test_enhanced_importance.json"
    if os.path.exists(test_path):
        os.remove(test_path)

    # 创建增强记忆系统
    memory = get_memory_system()
    manager = ImportanceManager(test_path)
    enhanced = EnhancedMemoryWithImportance(memory, manager)

    # 清空现有记忆
    memory.l1.clear()
    memory.l2.clear()
    memory.l3.clear()

    # 添加带重要性的记忆
    mem_id1 = enhanced.add_with_importance(
        "产品发布计划文档",
        "proj_001",
        ImportanceLevel.CRITICAL,
        score=9.8,
        reason="即将发布，非常重要",
        memory_level="l2"
    )
    mem_id2 = enhanced.add_with_importance(
        "设计草图",
        "proj_001",
        ImportanceLevel.MEDIUM,
        memory_level="l2"
    )
    mem_id3 = enhanced.add_with_importance(
        "会议纪要",
        "proj_001",
        ImportanceLevel.HIGH,
        memory_level="l2"
    )

    print(f"\n添加的记忆ID: {mem_id1}, {mem_id2}, {mem_id3}")

    # 获取重要性
    importance1 = enhanced.get_importance(mem_id1)
    print(f"mem_id1 重要性: {importance1}")
    assert importance1['level'] == 5
    assert importance1['score'] == 9.8

    # 按重要性召回
    result_high = enhanced.recall_by_importance(ImportanceLevel.HIGH, min_level=True)
    print(f"\n>= HIGH 等级的记忆数量: {result_high['count']}")
    assert result_high['count'] == 2

    # 统计
    stats = enhanced.get_importance_statistics()
    print(f"\n统计: {stats}")
    assert stats['total_memories_with_importance'] == 3

    # 清理
    os.remove(test_path)
    print("\n✓ 增强记忆系统测试通过！")
    return True


def test_importance_statistics():
    """测试重要性统计功能"""
    print("\n" + "=" * 60)
    print("测试 3: 重要性统计功能")
    print("=" * 60)

    test_path = "./data/test_stats_importance.json"
    if os.path.exists(test_path):
        os.remove(test_path)

    manager = ImportanceManager(test_path)

    # 添加多个不同重要性的记忆
    for i in range(5):
        manager.set_importance(f"low_{i}", ImportanceLevel.LOW)

    for i in range(10):
        manager.set_importance(f"medium_{i}", ImportanceLevel.MEDIUM)

    for i in range(3):
        manager.set_importance(f"high_{i}", ImportanceLevel.HIGH, 8.0 + i * 0.5)

    # 获取统计
    stats = manager.get_importance_statistics()
    print(f"\n统计信息:")
    print(f"  总记忆数: {stats['total_memories_with_importance']}")
    print(f"  各等级数量: {stats['level_counts']}")
    print(f"  平均评分: {stats['average_score']}")
    print(f"  有评分的记忆: {stats['memories_with_score']}")

    # 验证统计
    assert stats['total_memories_with_importance'] == 18
    assert stats['level_counts'][2] == 5
    assert stats['level_counts'][3] == 10
    assert stats['level_counts'][4] == 3

    # 清理
    os.remove(test_path)
    print("\n✓ 重要性统计功能测试通过！")
    return True


def test_update_importance():
    """测试更新重要性功能"""
    print("\n" + "=" * 60)
    print("测试 4: 更新重要性")
    print("=" * 60)

    test_path = "./data/test_update_importance.json"
    if os.path.exists(test_path):
        os.remove(test_path)

    manager = ImportanceManager(test_path)

    # 初始设置
    manager.set_importance("mem_001", ImportanceLevel.LOW, score=3.0)
    importance1 = manager.get_importance("mem_001")
    print(f"初始: {importance1}")
    assert importance1['level'] == 2
    assert importance1['score'] == 3.0

    # 更新
    manager.set_importance(
        "mem_001",
        ImportanceLevel.HIGH,
        score=8.5,
        reason="变得重要了"
    )
    importance2 = manager.get_importance("mem_001")
    print(f"更新后: {importance2}")
    assert importance2['level'] == 4
    assert importance2['score'] == 8.5

    # 验证索引更新
    low_mems = manager.get_memories_by_importance(ImportanceLevel.LOW)
    assert "mem_001" not in low_mems

    high_mems = manager.get_memories_by_importance(ImportanceLevel.HIGH)
    assert "mem_001" in high_mems

    # 清理
    os.remove(test_path)
    print("\n✓ 更新重要性测试通过！")
    return True


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("第16阶段测试：记忆重要性/评分功能")
    print("=" * 60)

    all_passed = True

    try:
        passed = test_importance_manager_basic()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试1失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_enhanced_memory_system()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试2失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_importance_statistics()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试3失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_update_importance()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试4失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("✓ 所有测试通过！")
    else:
        print("✗ 部分测试失败")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
