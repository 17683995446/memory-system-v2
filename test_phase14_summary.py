"""
第14阶段测试：记忆摘要功能
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.memory import get_memory_system
from src.summary import MemorySummarizer


def add_sample_data(memory):
    """添加测试数据"""
    # 清空现有数据
    memory.l1.clear()
    memory.l2.clear()
    memory.l3.clear()

    # 添加 L1 记忆
    print("添加 L1 记忆...")
    memory.l1.add("用户问候：你好，我想了解产品", "session_001")
    memory.l1.add("用户需求：需要价格比较功能", "session_001")
    memory.l1.add("临时笔记：明天开会讨论", "session_002")
    memory.l1.add("思考：这个设计可能有问题", "session_002")
    memory.l1.add("提醒：需要更新文档", "session_002")

    # 添加 L2 记忆
    print("添加 L2 记忆...")
    for i in range(8):
        memory.add(
            f"项目讨论：关于功能 {i} 的实现方案，考虑到性能优化和用户体验",
            f"session_{(i % 3) + 1}",
            "l2"
        )

    # 添加 L3 事实
    print("添加 L3 事实...")
    memory.add_fact("用户", "姓名", "张三")
    memory.add_fact("用户", "等级", "VIP")
    memory.add_fact("用户", "注册日期", "2024-01-15")
    memory.add_fact("产品", "名称", "智能助手")
    memory.add_fact("产品", "版本", "2.1.0")
    memory.add_fact("产品", "价格", "99/月")
    memory.add_fact("系统", "状态", "正常")
    memory.add_fact("系统", "语言", "中文")

    print("测试数据添加完成！\n")


def test_l1_summary():
    """测试 L1 摘要"""
    print("=" * 60)
    print("测试 1: L1 记忆摘要")
    print("=" * 60)

    memory = get_memory_system()
    summary = MemorySummarizer.summarize_l1(memory.l1)

    print(f"总记忆数: {summary['total_items']}")
    print(f"会话数: {summary['total_sessions']}")
    print(f"摘要: {summary['summary']}")
    print(f"\n最近的记忆:")
    for item in summary['recent_items']:
        print(f"  - [{item['session']}] {item['text']}")

    assert summary['total_items'] == 5
    assert summary['total_sessions'] == 2
    assert len(summary['recent_items']) <= 5

    print("\n✓ L1 摘要测试通过！\n")
    return True


def test_l2_summary():
    """测试 L2 摘要"""
    print("=" * 60)
    print("测试 2: L2 记忆摘要")
    print("=" * 60)

    memory = get_memory_system()
    summary = MemorySummarizer.summarize_l2(memory.l2)

    print(f"总记忆数: {summary['total_items']}")
    print(f"摘要: {summary['summary']}")
    print(f"\n会话分布: {summary['sessions']}")
    print(f"\n最近添加:")
    for item in summary['recent_items']:
        print(f"  - {item['text']}")

    assert summary['total_items'] == 8
    assert len(summary['sessions']) >= 1

    print("\n✓ L2 摘要测试通过！\n")
    return True


def test_l3_summary():
    """测试 L3 摘要"""
    print("=" * 60)
    print("测试 3: L3 事实摘要")
    print("=" * 60)

    memory = get_memory_system()
    summary = MemorySummarizer.summarize_l3(memory.l3)

    print(f"总事实数: {summary['total_facts']}")
    print(f"实体数: {summary['total_entities']}")
    print(f"摘要: {summary['summary']}")
    print(f"\n主要实体:")
    for ent in summary['top_entities']:
        print(f"  - {ent['entity']}: {ent['fact_count']} 条事实 ({ent['preview']})")

    assert summary['total_facts'] == 8
    assert summary['total_entities'] == 3

    print("\n✓ L3 摘要测试通过！\n")
    return True


def test_full_summary():
    """测试完整摘要"""
    print("=" * 60)
    print("测试 4: 完整记忆系统摘要")
    print("=" * 60)

    memory = get_memory_system()
    summary = MemorySummarizer.summarize_all(memory)

    print(f"总记忆数: {summary['total_items']}")
    print(f"系统摘要: {summary['system_summary']}")

    # 格式化输出
    formatted = MemorySummarizer.format_summary(summary)
    print("\n格式化摘要:")
    print("-" * 60)
    print(formatted)
    print("-" * 60)

    assert summary['total_items'] == 21  # 5+8+8
    assert summary['l1'] is not None
    assert summary['l2'] is not None
    assert summary['l3'] is not None

    print("\n✓ 完整摘要测试通过！\n")
    return True


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("第14阶段测试：记忆摘要功能")
    print("=" * 60 + "\n")

    # 初始化并添加数据
    memory = get_memory_system()
    add_sample_data(memory)

    all_passed = True

    try:
        passed = test_l1_summary()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"✗ L1 摘要测试失败: {e}")
        all_passed = False

    try:
        passed = test_l2_summary()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"✗ L2 摘要测试失败: {e}")
        all_passed = False

    try:
        passed = test_l3_summary()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"✗ L3 摘要测试失败: {e}")
        all_passed = False

    try:
        passed = test_full_summary()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"✗ 完整摘要测试失败: {e}")
        all_passed = False

    print("=" * 60)
    if all_passed:
        print("✓ 所有测试通过！")
    else:
        print("✗ 部分测试失败")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
