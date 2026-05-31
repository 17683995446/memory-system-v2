"""
第18阶段测试：记忆关联/关系网络功能
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.memory import get_memory_system
from src.relations import MemoryRelationNetwork, MemoryRelation, EnhancedMemoryWithRelations


def test_relation_network_basic():
    """测试关系网络基本功能"""
    print("\n" + "=" * 60)
    print("测试 1: 关系网络基本功能")
    print("=" * 60)

    # 清理测试数据
    test_path = "./data/test_relations_temp.json"
    if os.path.exists(test_path):
        os.remove(test_path)

    network = MemoryRelationNetwork(test_path)

    # 添加关系
    rel1 = network.add_relation("mem_001", "mem_002", "related_to", "项目相关")
    rel2 = network.add_relation("mem_002", "mem_003", "depends_on", "依赖关系")
    rel3 = network.add_relation("mem_001", "mem_004", "similar_to", "相似内容")

    print(f"添加了 {len(network.relations)} 个关系")

    # 测试获取关系
    from_001 = network.get_relations_from("mem_001")
    print(f"\n从 mem_001 出发的关系数: {len(from_001)}")
    assert len(from_001) == 2, "应该有2个从mem_001出发的关系"

    to_002 = network.get_relations_to("mem_002")
    print(f"指向 mem_002 的关系数: {len(to_002)}")
    assert len(to_002) == 1, "应该有1个指向mem_002的关系"

    # 测试按类型获取关系
    related_to = network.get_relations_by_type("related_to")
    print(f"'related_to' 类型的关系数: {len(related_to)}")
    assert len(related_to) == 1

    # 测试统计
    stats = network.get_statistics()
    print(f"\n统计:")
    print(f"  总关系数: {stats['total_relations']}")
    print(f"  关系类型: {stats['relation_types']}")
    assert stats['total_relations'] == 3

    # 清理
    os.remove(test_path)
    print("\n✓ 关系网络基本功能测试通过！")
    return True


def test_relation_traversal():
    """测试关系网络遍历"""
    print("\n" + "=" * 60)
    print("测试 2: 关系网络遍历")
    print("=" * 60)

    test_path = "./data/test_traversal_temp.json"
    if os.path.exists(test_path):
        os.remove(test_path)

    network = MemoryRelationNetwork(test_path)

    # 构建一个链式关系
    network.add_relation("a", "b", "next")
    network.add_relation("b", "c", "next")
    network.add_relation("c", "d", "next")
    network.add_relation("a", "e", "branch")

    # 测试遍历
    result = network.traverse("a", max_depth=3, include_self=True)
    print(f"从 'a' 遍历的结果:")
    for depth, mems in sorted(result.items()):
        print(f"  深度 {depth}: {mems}")

    # 验证结果
    assert 0 in result and "a" in result[0], "应该包含起始节点"
    assert 1 in result and "b" in result[1] and "e" in result[1], "深度1应该包含b和e"
    assert 2 in result and "c" in result[2], "深度2应该包含c"
    assert 3 in result and "d" in result[3], "深度3应该包含d"

    # 清理
    os.remove(test_path)
    print("\n✓ 关系网络遍历测试通过！")
    return True


def test_enhanced_memory_relations():
    """测试增强记忆系统关系功能"""
    print("\n" + "=" * 60)
    print("测试 3: 增强记忆系统关系功能")
    print("=" * 60)

    # 清理可能的测试文件
    test_path = "./data/relations.json"
    if os.path.exists(test_path):
        os.remove(test_path)

    # 创建记忆系统
    memory = get_memory_system()
    memory.l1.clear()
    memory.l2.clear()
    memory.l3.clear()

    # 创建增强记忆系统
    enhanced = EnhancedMemoryWithRelations(memory)

    # 添加一些记忆（确保使用L2层级，这样我们能获得唯一ID）
    mem_id1 = memory.add("项目需求文档", "proj_001", "l2")
    mem_id2 = memory.add("技术架构设计", "proj_001", "l2")
    mem_id3 = memory.add("用户反馈分析", "proj_002", "l2")

    # 添加关系
    enhanced.add_relation(mem_id1, mem_id2, "related_to", "同一项目")
    enhanced.add_relation(mem_id1, mem_id3, "depends_on", "需求依赖反馈")

    # 获取相关记忆
    related = enhanced.get_related_memories(mem_id1)
    print(f"\n与 {mem_id1} 相关的记忆数: {len(related)}")

    for rel in related:
        print(f"  {rel['direction']} 关系: {rel['memory_id']} ({rel['relation_type']})")

    assert len(related) >= 2, "应该至少有2个相关记忆"

    # 测试统计
    stats = enhanced.get_relation_statistics()
    print(f"\n关系统计:")
    print(f"  总关系数: {stats['total_relations']}")
    assert stats['total_relations'] == 2

    # 清理
    if os.path.exists(test_path):
        os.remove(test_path)

    print("\n✓ 增强记忆系统关系功能测试通过！")
    return True


def test_relation_types():
    """测试不同类型的关系"""
    print("\n" + "=" * 60)
    print("测试 4: 不同类型的关系")
    print("=" * 60)

    test_path = "./data/test_types_temp.json"
    if os.path.exists(test_path):
        os.remove(test_path)

    network = MemoryRelationNetwork(test_path)

    # 添加不同类型的关系
    relation_types = ["related_to", "depends_on", "similar_to", "part_of", "causes"]
    for i, rel_type in enumerate(relation_types):
        network.add_relation(f"mem_{i}", f"mem_{i+1}", rel_type)

    # 测试按类型查询
    for rel_type in relation_types:
        relations = network.get_relations_by_type(rel_type)
        print(f"\n'{rel_type}' 类型的关系数: {len(relations)}")
        assert len(relations) == 1, f"应该有1个 '{rel_type}' 关系"

    # 测试统计中的类型分布
    stats = network.get_statistics()
    print(f"\n所有关系类型: {sorted(stats['type_distribution'].keys())}")
    assert len(stats['type_distribution']) == 5

    # 清理
    os.remove(test_path)
    print("\n✓ 不同类型关系测试通过！")
    return True


def test_relation_removal():
    """测试关系移除功能"""
    print("\n" + "=" * 60)
    print("测试 5: 关系移除功能")
    print("=" * 60)

    test_path = "./data/test_removal_temp.json"
    if os.path.exists(test_path):
        os.remove(test_path)

    network = MemoryRelationNetwork(test_path)

    # 添加一些关系
    rel1 = network.add_relation("x", "y", "test")
    rel2 = network.add_relation("y", "z", "test")
    network.add_relation("x", "z", "test")

    # 移除单个关系
    removed = network.remove_relation(rel1)
    assert removed
    assert len(network.relations) == 2, "应该还剩2个关系"

    # 移除与某个记忆相关的所有关系
    count = network.remove_relations_related_to("y")
    print(f"移除了 {count} 个与 'y' 相关的关系")
    assert len(network.relations) == 1, "应该还剩1个关系"

    # 清理
    os.remove(test_path)
    print("\n✓ 关系移除功能测试通过！")
    return True


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("第18阶段测试：记忆关联/关系网络功能")
    print("=" * 60)

    all_passed = True

    try:
        passed = test_relation_network_basic()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试1失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_relation_traversal()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试2失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_enhanced_memory_relations()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试3失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_relation_types()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试4失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_relation_removal()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试5失败: {e}")
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
