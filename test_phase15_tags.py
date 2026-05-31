"""
第15阶段测试：记忆标签/分类功能
"""

import sys
import os
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.memory import get_memory_system
from src.tags import TagManager, EnhancedMemorySystem


def test_tag_manager_basic():
    """测试标签管理器基本功能"""
    print("\n" + "=" * 60)
    print("测试 1: 标签管理器基本功能")
    print("=" * 60)

    # 使用临时文件进行测试
    test_path = "./data/test_tags_temp.json"
    if os.path.exists(test_path):
        os.remove(test_path)

    manager = TagManager(test_path)

    # 测试添加标签
    added = manager.add_tags("mem_001", ["重要", "工作"])
    print(f"添加标签数: {added}")
    assert added == 2

    # 测试获取标签
    tags = manager.get_tags("mem_001")
    print(f"记忆标签: {tags}")
    assert set(tags) == {"重要", "工作"}

    # 测试获取标签的记忆
    mems = manager.get_memories_by_tag("重要")
    print(f"标签 '重要' 的记忆: {mems}")
    assert "mem_001" in mems

    # 测试获取所有标签
    all_tags = manager.get_all_tags()
    print(f"所有标签: {all_tags}")
    assert set(all_tags) == {"重要", "工作"}

    # 测试移除标签
    removed = manager.remove_tags("mem_001", ["工作"])
    print(f"移除标签数: {removed}")
    assert removed == 1

    tags = manager.get_tags("mem_001")
    print(f"移除后标签: {tags}")
    assert tags == ["重要"]

    # 清理
    os.remove(test_path)
    print("✓ 标签管理器基本功能测试通过！")
    return True


def test_enhanced_memory_system():
    """测试增强记忆系统"""
    print("\n" + "=" * 60)
    print("测试 2: 增强记忆系统")
    print("=" * 60)

    # 创建增强记忆系统
    memory = get_memory_system()
    test_path = "./data/test_enhanced_tags.json"
    if os.path.exists(test_path):
        os.remove(test_path)

    tag_manager = TagManager(test_path)
    enhanced = EnhancedMemorySystem(memory, tag_manager)

    # 清空
    memory.l1.clear()
    memory.l2.clear()
    memory.l3.clear()

    # 测试添加带标签的记忆 - 明确指定 L2 层级，确保唯一ID
    mem_id1 = enhanced.add_with_tags(
        "关于项目的重要讨论",
        "session_001",
        ["重要", "工作", "项目"],
        level="l2"
    )
    mem_id2 = enhanced.add_with_tags(
        "个人生活记录",
        "session_002",
        ["生活", "个人"],
        level="l2"
    )

    print(f"添加的记忆ID: {mem_id1}, {mem_id2}")

    # 测试获取记忆标签
    tags1 = enhanced.get_memory_tags(mem_id1)
    print(f"记忆1标签: {tags1}")
    assert set(tags1) == {"重要", "工作", "项目"}

    # 测试按标签召回
    result = enhanced.recall_by_tag("重要")
    print(f"标签 '重要' 的记忆数: {result['count']}")
    assert result['count'] >= 1

    # 测试获取所有标签
    all_tags = enhanced.get_all_tags()
    print(f"所有标签: {all_tags}")
    assert len(all_tags) == 5

    # 测试添加更多标签到现有记忆
    added = enhanced.add_tags_to_memory(mem_id2, ["笔记"])
    print(f"添加标签数: {added}")
    assert added == 1

    # 测试标签统计
    stats = enhanced.get_tag_statistics()
    print(f"\n标签统计:")
    for s in stats:
        print(f"  - {s['tag']}: {s['memory_count']} 条记忆")

    assert len(stats) == 6

    # 清理
    os.remove(test_path)
    print("\n✓ 增强记忆系统测试通过！")
    return True


def test_tag_statistics():
    """测试标签统计功能"""
    print("\n" + "=" * 60)
    print("测试 3: 标签统计功能")
    print("=" * 60)

    test_path = "./data/test_stats_tags.json"
    if os.path.exists(test_path):
        os.remove(test_path)

    manager = TagManager(test_path)

    # 添加多个记忆和标签
    manager.add_tags("mem_1", ["工作", "紧急"])
    manager.add_tags("mem_2", ["工作", "会议"])
    manager.add_tags("mem_3", ["工作", "文档"])
    manager.add_tags("mem_4", ["生活", "阅读"])
    manager.add_tags("mem_5", ["生活", "娱乐"])
    manager.add_tags("mem_6", ["工作"])

    # 获取统计
    stats = manager.get_tag_statistics()
    print("\n标签统计:")
    for s in stats:
        print(f"  - {s['tag']}: {s['memory_count']} 条记忆")

    # 验证 - 注意标签会被转成小写，但中文大小写一样
    assert len(stats) == 7
    # "工作" 应该是最常用的标签
    assert stats[0]['tag'] == '工作'
    assert stats[0]['memory_count'] == 4

    # 清理
    os.remove(test_path)
    print("\n✓ 标签统计功能测试通过！")
    return True


def test_full_integration():
    """测试完整集成"""
    print("\n" + "=" * 60)
    print("测试 4: 完整集成测试")
    print("=" * 60)

    # 创建增强系统
    memory = get_memory_system()
    test_path = "./data/test_full_tags.json"
    if os.path.exists(test_path):
        os.remove(test_path)

    tag_manager = TagManager(test_path)
    enhanced = EnhancedMemorySystem(memory, tag_manager)

    # 清空
    memory.l1.clear()
    memory.l2.clear()
    memory.l3.clear()

    # 添加测试数据 - 明确指定 L2 层级
    mem_ids = []
    mem_ids.append(enhanced.add_with_tags("项目需求文档", "proj_1", ["文档", "需求", "项目A"], level="l2"))
    mem_ids.append(enhanced.add_with_tags("技术架构设计", "proj_1", ["设计", "架构", "项目A"], level="l2"))
    mem_ids.append(enhanced.add_with_tags("会议记录", "proj_1", ["会议", "项目A"], level="l2"))
    mem_ids.append(enhanced.add_with_tags("用户反馈", "proj_2", ["用户", "反馈", "项目B"], level="l2"))
    mem_ids.append(enhanced.add_with_tags("测试报告", "proj_2", ["测试", "报告", "项目B"], level="l2"))

    print(f"\n添加了 {len(mem_ids)} 条记忆")

    # 完整统计
    all_tags = enhanced.get_all_tags()
    print(f"\n所有标签: {all_tags}")

    stats = enhanced.get_tag_statistics()
    print("\n标签使用统计:")
    for s in stats:
        print(f"  - {s['tag']}: {s['memory_count']} 条记忆")

    # 测试按标签检索 - 注意标签是小写的
    print("\n按标签检索:")
    proj_a = enhanced.recall_by_tag("项目A")
    print(f"  - 项目A (转小写是 '项目a' 标签: {proj_a['count']} 条记忆")
    # 检查 '项目a' 应该有 3 条记忆
    proj_a_lower = enhanced.recall_by_tag("项目a")
    assert proj_a_lower['count'] == 3

    docs = enhanced.recall_by_tag("文档")
    print(f"  - 文档 标签: {docs['count']} 条记忆")
    assert docs['count'] == 1

    # 测试移除标签
    print("\n移除标签...")
    removed = enhanced.remove_tags_from_memory(mem_ids[0], ["文档"])
    print(f"移除了 {removed} 个标签")

    # 验证
    tags = enhanced.get_memory_tags(mem_ids[0])
    print(f"记忆0当前标签: {tags}")
    assert "文档" not in tags

    # 清理
    os.remove(test_path)
    print("\n✓ 完整集成测试通过！")
    return True


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("第15阶段测试：记忆标签/分类功能")
    print("=" * 60)

    # 先清理所有可能的测试文件
    for filename in ["test_tags_temp.json", "test_enhanced_tags.json", "test_stats_tags.json", "test_full_tags.json"]:
        filepath = os.path.join("./data", filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:
                pass

    all_passed = True

    try:
        passed = test_tag_manager_basic()
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
        passed = test_tag_statistics()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试3失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_full_integration()
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
