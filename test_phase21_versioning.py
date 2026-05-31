"""
第21阶段测试：记忆版本控制功能
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.memory import get_memory_system
from src.versioning import (
    MemoryVersionControl,
    MemoryVersion,
    EnhancedMemoryWithVersionControl
)


def test_basic_versioning():
    """测试基本版本控制功能"""
    print("\n" + "=" * 60)
    print("测试 1: 基本版本控制功能")
    print("=" * 60)

    # 清理测试数据
    test_path = "./data/test_versions_temp.json"
    if os.path.exists(test_path):
        os.remove(test_path)

    version_control = MemoryVersionControl(test_path)

    # 创建初始版本
    v1 = version_control.create_version(
        memory_id="mem_001",
        content="这是初始内容",
        comment="初始版本"
    )
    print(f"创建版本 1: v{ v1.version_number}")

    # 创建第二个版本
    v2 = version_control.create_version(
        memory_id="mem_001",
        content="这是修改后的内容",
        comment="第一次修改"
    )
    print(f"创建版本 2: v{ v2.version_number}")

    # 创建第三个版本
    v3 = version_control.create_version(
        memory_id="mem_001",
        content="这是最终版本内容",
        comment="第二次修改"
    )
    print(f"创建版本 3: v{ v3.version_number}")

    # 获取版本数量
    count = version_control.get_version_count("mem_001")
    print(f"\nmem_001 的版本数量: {count}")
    assert count == 3

    # 获取所有版本
    versions = version_control.get_versions("mem_001")
    print(f"获取到的版本数: {len(versions)}")
    assert len(versions) == 3
    assert versions[0].version_number == 3  # 最新版本在前

    # 获取特定版本
    specific_v = version_control.get_version("mem_001", 1)
    print(f"\n版本 1 的内容: {specific_v.content}")
    assert specific_v is not None
    assert specific_v.comment == "初始版本"

    # 获取最新版本
    latest = version_control.get_latest_version("mem_001")
    print(f"最新版本: v{ latest.version_number}, 内容: {latest.content}")
    assert latest.version_number == 3

    # 清理
    os.remove(test_path)
    print("\n✓ 基本版本控制功能测试通过！")
    return True


def test_version_comparison():
    """测试版本比较功能"""
    print("\n" + "=" * 60)
    print("测试 2: 版本比较功能")
    print("=" * 60)

    test_path = "./data/test_compare_temp.json"
    if os.path.exists(test_path):
        os.remove(test_path)

    version_control = MemoryVersionControl(test_path)

    # 创建多个版本
    version_control.create_version("mem_001", "第一行\n第二行\n第三行", "版本1")
    version_control.create_version("mem_001", "第一行\n修改后的第二行\n第三行", "版本2")
    version_control.create_version("mem_001", "第一行\n修改后的第二行\n新增的第三行", "版本3")

    # 比较版本1和版本3
    comparison = version_control.compare_versions("mem_001", 1, 3)
    print(f"\n比较 v1 和 v3:")
    print(f"  内容哈希变化: {comparison['content_hash_changed']}")
    print(f"  新增行数: {comparison['lines_added']}")
    print(f"  删除行数: {comparison['lines_removed']}")
    print(f"  未变行数: {comparison['lines_unchanged']}")
    print(f"  大小变化: {comparison['size_change']} 字节")

    assert comparison['content_hash_changed'] == True
    assert comparison['lines_added'] >= 0

    # 比较版本1和版本2
    comparison2 = version_control.compare_versions("mem_001", 1, 2)
    print(f"\n比较 v1 和 v2:")
    print(f"  内容哈希变化: {comparison2['content_hash_changed']}")

    assert comparison2['content_hash_changed'] == True

    # 清理
    os.remove(test_path)
    print("\n✓ 版本比较功能测试通过！")
    return True


def test_version_rollback():
    """测试版本回滚功能"""
    print("\n" + "=" * 60)
    print("测试 3: 版本回滚功能")
    print("=" * 60)

    test_path = "./data/test_rollback_temp.json"
    if os.path.exists(test_path):
        os.remove(test_path)

    version_control = MemoryVersionControl(test_path)

    # 创建多个版本
    version_control.create_version("mem_001", "版本1的内容", "v1")
    version_control.create_version("mem_001", "版本2的内容", "v2")
    version_control.create_version("mem_001", "版本3的内容", "v3")

    print(f"当前版本数: {version_control.get_version_count('mem_001')}")

    # 回滚到版本1
    rolled_back_content = version_control.rollback_to_version("mem_001", 1)
    print(f"\n回滚到 v1，内容: {rolled_back_content}")
    assert rolled_back_content == "版本1的内容"

    # 检查是否创建了新版本（回滚记录）
    print(f"回滚后版本数: {version_control.get_version_count('mem_001')}")
    assert version_control.get_version_count("mem_001") == 4

    # 获取最新版本（应该是回滚后创建的新版本）
    latest = version_control.get_latest_version("mem_001")
    print(f"最新版本 v{ latest.version_number}: {latest.content}")
    print(f"回滚注释: {latest.comment}")
    assert latest.content == "版本1的内容"
    assert "回滚" in latest.comment

    # 清理
    os.remove(test_path)
    print("\n✓ 版本回滚功能测试通过！")
    return True


def test_version_cleanup():
    """测试版本清理功能"""
    print("\n" + "=" * 60)
    print("测试 4: 版本清理功能")
    print("=" * 60)

    test_path = "./data/test_cleanup_temp.json"
    if os.path.exists(test_path):
        os.remove(test_path)

    version_control = MemoryVersionControl(test_path)

    # 创建10个版本
    for i in range(10):
        version_control.create_version(
            "mem_001",
            f"版本{i+1}的内容",
            f"v{i+1}"
        )

    print(f"清理前版本数: {version_control.get_version_count('mem_001')}")
    assert version_control.get_version_count("mem_001") == 10

    # 删除旧版本，只保留最新的5个
    deleted_count = version_control.delete_old_versions("mem_001", keep_latest=5)
    print(f"删除了 {deleted_count} 个旧版本")
    assert deleted_count == 5

    print(f"清理后版本数: {version_control.get_version_count('mem_001')}")
    assert version_control.get_version_count("mem_001") == 5

    # 获取版本列表，验证保留的是最新的
    versions = version_control.get_versions("mem_001")
    assert versions[0].version_number == 10  # 最新的版本

    # 清理
    os.remove(test_path)
    print("\n✓ 版本清理功能测试通过！")
    return True


def test_enhanced_memory_versioning():
    """测试增强记忆系统版本控制"""
    print("\n" + "=" * 60)
    print("测试 5: 增强记忆系统版本控制")
    print("=" * 60)

    # 创建系统
    memory = get_memory_system()
    enhanced = EnhancedMemoryWithVersionControl(memory)

    # 清空现有数据
    memory.l1.clear()
    memory.l2.clear()
    memory.l3.clear()

    # 添加带版本控制的记忆
    mem_id = enhanced.add_with_version(
        "初始项目计划",
        "proj_001",
        "l2",
        comment="项目启动"
    )
    print(f"添加记忆: {mem_id}")

    # 更新记忆
    enhanced.update_with_version(
        mem_id,
        "更新后的项目计划",
        comment="需求变更"
    )
    print("更新记忆 v2")

    enhanced.update_with_version(
        mem_id,
        "最终项目计划",
        comment="完成评审"
    )
    print("更新记忆 v3")

    # 获取版本历史
    versions = enhanced.get_memory_versions(mem_id)
    print(f"\n记忆的版本历史 ({len(versions)} 个版本):")
    for v in versions:
        v_time = time.strftime("%H:%M:%S", time.localtime(v.created_at))
        print(f"  v{v.version_number} [{v_time}]: {v.comment}")

    assert len(versions) == 3

    # 获取特定版本详情
    details = enhanced.get_version_details(mem_id, 1)
    print(f"\nv1 详情:")
    print(f"  内容: {details['content']}")
    print(f"  注释: {details['comment']}")
    assert details['content'] == "初始项目计划"

    # 比较版本
    comparison = enhanced.compare_versions(mem_id, 1, 3)
    print(f"\n比较 v1 和 v3:")
    print(f"  内容哈希变化: {comparison['content_hash_changed']}")

    # 回滚测试
    rolled_back = enhanced.rollback_to_version(mem_id, 1)
    print(f"\n回滚到 v1: {rolled_back}")

    versions_after = enhanced.get_memory_versions(mem_id)
    print(f"回滚后版本数: {len(versions_after)}")
    assert len(versions_after) == 4

    # 获取统计
    stats = enhanced.get_version_statistics()
    print(f"\n版本统计:")
    print(f"  总版本数: {stats['total_versions']}")
    print(f"  有版本的记忆数: {stats['memories_with_versions']}")

    print("\n✓ 增强记忆系统版本控制测试通过！")
    return True


def test_multiple_memories():
    """测试多个记忆的版本控制"""
    print("\n" + "=" * 60)
    print("测试 6: 多个记忆的版本控制")
    print("=" * 60)

    test_path = "./data/test_multi_temp.json"
    if os.path.exists(test_path):
        os.remove(test_path)

    version_control = MemoryVersionControl(test_path)

    # 为不同记忆创建版本
    for i in range(3):
        mem_id = f"mem_{i:03d}"
        for j in range(3):
            version_control.create_version(
                mem_id,
                f"{mem_id} 的版本{j+1}",
                f"v{j+1}"
            )

    # 获取统计
    stats = version_control.get_statistics()
    print(f"\n版本统计:")
    print(f"  总版本数: {stats['total_versions']}")
    print(f"  有版本的记忆数: {stats['memories_with_versions']}")
    print(f"  平均每记忆版本数: {stats['average_versions_per_memory']:.2f}")
    print(f"  版本最多的记忆: {stats['most_versions_memories']}")

    assert stats['total_versions'] == 9
    assert stats['memories_with_versions'] == 3
    assert stats['average_versions_per_memory'] == 3.0

    # 测试清空单个记忆的版本
    deleted = version_control.clear_memory_versions("mem_000")
    print(f"\n清空 mem_000 的版本，删除了 {deleted} 个版本")
    assert deleted == 3

    stats_after = version_control.get_statistics()
    assert stats_after['memories_with_versions'] == 2

    # 清理
    os.remove(test_path)
    print("\n✓ 多记忆版本控制测试通过！")
    return True


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("第21阶段测试：记忆版本控制功能")
    print("=" * 60)

    all_passed = True

    try:
        passed = test_basic_versioning()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试1失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_version_comparison()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试2失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_version_rollback()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试3失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_version_cleanup()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试4失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_enhanced_memory_versioning()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试5失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_multiple_memories()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试6失败: {e}")
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
