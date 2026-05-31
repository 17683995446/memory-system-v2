"""
第20阶段测试：记忆推荐系统
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.memory import get_memory_system
from src.recommender import (
    MemoryRecommender,
    MemoryRecommendation,
    RecommendationStrategy,
    EnhancedMemoryWithRecommender
)


def test_recently_accessed():
    """测试最近访问推荐"""
    print("\n" + "=" * 60)
    print("测试 1: 最近访问推荐")
    print("=" * 60)

    recommender = MemoryRecommender()

    # 注册记忆
    for i in range(5):
        memory_id = f"mem_{i:03d}"
        recommender.register_memory(memory_id, f"测试记忆{i}")

    # 记录访问（不同时间的访问）
    recommender.register_access("mem_000")
    recommender.register_access("mem_000")
    recommender.register_access("mem_001")
    recommender.register_access("mem_001")
    recommender.register_access("mem_001")
    recommender.register_access("mem_002")

    # 获取推荐
    recommendations = recommender.recommend_recently_accessed(limit=10)
    print(f"获得 {len(recommendations)} 条推荐")

    for rec in recommendations:
        print(f"  {rec.memory_id}: 分数 {rec.score:.2f}, 原因: {rec.reason}")

    # 验证
    assert len(recommendations) >= 3
    assert recommendations[0].memory_id in ["mem_001", "mem_000"]

    print("\n✓ 最近访问推荐测试通过！")
    return True


def test_related_recommendation():
    """测试相关记忆推荐"""
    print("\n" + "=" * 60)
    print("测试 2: 相关记忆推荐")
    print("=" * 60)

    recommender = MemoryRecommender()

    # 注册记忆
    for i in range(4):
        memory_id = f"mem_{i:03d}"
        recommender.register_memory(memory_id, f"测试记忆{i}")

    # 建立关系
    recommender.register_relation("mem_000", "mem_001")
    recommender.register_relation("mem_000", "mem_002")
    recommender.register_relation("mem_001", "mem_003")

    # 获取推荐
    recommendations = recommender.recommend_related("mem_000", limit=5)
    print(f"从mem_000获得 {len(recommendations)} 条相关推荐")

    for rec in recommendations:
        print(f"  {rec.memory_id}: 分数 {rec.score:.2f}, 原因: {rec.reason}")

    assert len(recommendations) == 2
    assert {"mem_001", "mem_002"} == {r.memory_id for r in recommendations}

    print("\n✓ 相关记忆推荐测试通过！")
    return True


def test_important_recommendation():
    """测试重要性推荐"""
    print("\n" + "=" * 60)
    print("测试 3: 重要性推荐")
    print("=" * 60)

    recommender = MemoryRecommender()

    # 注册记忆
    for i in range(5):
        memory_id = f"mem_{i:03d}"
        recommender.register_memory(memory_id, f"测试记忆{i}")
        # 设置不同的重要性
        if i % 2 == 0:
            recommender.register_importance(memory_id, 8.0 - i)  # 8, 6, 4
        else:
            recommender.register_importance(memory_id, 2.0 + i)  # 3, 4

    # 获取推荐
    recommendations = recommender.recommend_important(limit=10, min_importance=5.0)
    print(f"获得 {len(recommendations)} 条重要记忆推荐")

    for rec in recommendations:
        print(f"  {rec.memory_id}: 分数 {rec.score:.2f}, 原因: {rec.reason}")

    assert len(recommendations) == 3  # 重要性>=5的有3条
    assert recommendations[0].memory_id == "mem_000"

    print("\n✓ 重要性推荐测试通过！")
    return True


def test_tag_recommendation():
    """测试标签推荐"""
    print("\n" + "=" * 60)
    print("测试 4: 标签推荐")
    print("=" * 60)

    recommender = MemoryRecommender()

    # 注册记忆
    for i in range(5):
        memory_id = f"mem_{i:03d}"
        recommender.register_memory(memory_id, f"测试记忆{i}")

    # 分配标签
    recommender.register_tag("mem_000", "项目")
    recommender.register_tag("mem_000", "重要")
    recommender.register_tag("mem_001", "项目")
    recommender.register_tag("mem_002", "文档")
    recommender.register_tag("mem_003", "项目")
    recommender.register_tag("mem_003", "重要")

    # 获取推荐
    recommendations = recommender.recommend_by_tag(["项目", "重要"], limit=5)
    print(f"获得 {len(recommendations)} 条标签匹配推荐")

    for rec in recommendations:
        print(f"  {rec.memory_id}: 分数 {rec.score:.2f}, 原因: {rec.reason}")

    assert len(recommendations) >= 2
    assert recommendations[0].score == 1.0  # 匹配所有标签

    print("\n✓ 标签推荐测试通过！")
    return True


def test_combined_recommendation():
    """测试综合推荐"""
    print("\n" + "=" * 60)
    print("测试 5: 综合推荐")
    print("=" * 60)

    recommender = MemoryRecommender()

    # 注册记忆
    for i in range(6):
        memory_id = f"mem_{i:03d}"
        recommender.register_memory(memory_id, f"测试记忆{i}")

    # 设置各种属性
    recommender.register_access("mem_000")
    recommender.register_access("mem_001")
    recommender.register_access("mem_001")
    recommender.register_tag("mem_000", "重要")
    recommender.register_tag("mem_001", "重要")
    recommender.register_importance("mem_000", 9.0)
    recommender.register_importance("mem_002", 8.0)
    recommender.register_relation("mem_003", "mem_000")

    # 获取综合推荐
    recommendations = recommender.recommend_combined(
        context_memory_id="mem_003",
        target_tags=["重要"],
        limit=5
    )
    print(f"获得 {len(recommendations)} 条综合推荐")

    for rec in recommendations:
        print(f"  {rec.memory_id}: 分数 {rec.score:.2f}, 策略: {rec.strategy.value}")
        print(f"    原因: {rec.reason}")

    assert len(recommendations) >= 3

    print("\n✓ 综合推荐测试通过！")
    return True


def test_enhanced_memory():
    """测试增强记忆系统"""
    print("\n" + "=" * 60)
    print("测试 6: 增强记忆系统")
    print("=" * 60)

    # 创建系统
    memory = get_memory_system()
    enhanced = EnhancedMemoryWithRecommender(memory)

    # 清空现有数据
    memory.l1.clear()
    memory.l2.clear()
    memory.l3.clear()

    # 添加记忆
    mem1 = enhanced.add_with_recommendation(
        "项目计划文档",
        "proj_001",
        "l2",
        tags=["项目", "计划"],
        importance=9.0
    )
    mem2 = enhanced.add_with_recommendation(
        "技术架构设计",
        "proj_001",
        "l2",
        tags=["技术", "文档"],
        importance=8.5
    )
    mem3 = enhanced.add_with_recommendation(
        "用户反馈分析",
        "proj_002",
        "l2",
        tags=["用户", "反馈"],
        importance=7.0
    )

    print(f"添加了 3 条记忆到增强系统")

    # 添加关系
    enhanced.add_memory_relation(mem1, mem2)

    # 记录访问
    enhanced.access_memory(mem1)
    enhanced.access_memory(mem1)
    enhanced.access_memory(mem2)

    # 获取推荐
    recommendations = enhanced.get_recommendations(limit=5)
    print(f"\n获得 {len(recommendations)} 条推荐")

    for rec in recommendations:
        print(f"  {rec.memory_id}: 分数 {rec.score:.2f}, 原因: {rec.reason}")

    # 获取统计
    stats = enhanced.get_recommendation_stats()
    print(f"\n推荐系统统计:")
    print(f"  注册记忆数: {stats['registered_memories']}")
    print(f"  总访问数: {stats['total_accesses']}")

    assert stats['registered_memories'] == 3
    assert stats['total_accesses'] == 3

    print("\n✓ 增强记忆系统测试通过！")
    return True


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("第20阶段测试：记忆推荐系统")
    print("=" * 60)

    all_passed = True

    try:
        passed = test_recently_accessed()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试1失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_related_recommendation()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试2失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_important_recommendation()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试3失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_tag_recommendation()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试4失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_combined_recommendation()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试5失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_enhanced_memory()
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
