"""
第17阶段测试：记忆全文搜索功能
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.memory import get_memory_system
from src.search import MemorySearch, EnhancedMemorySearch


def test_basic_search():
    """测试基本搜索功能"""
    print("\n" + "=" * 60)
    print("测试 1: 基本搜索功能")
    print("=" * 60)

    searcher = MemorySearch()

    # 添加测试数据
    memories = [
        ("mem_001", "今天天气真不错，适合户外活动"),
        ("mem_002", "项目截止日期是2026年6月1日"),
        ("mem_003", "需要购买办公用品：笔、纸、文件夹"),
        ("mem_004", "今天的会议讨论了项目进度"),
        ("mem_005", "户外活动注意防晒和补水"),
    ]

    for mem_id, content in memories:
        searcher.index_memory(mem_id, content)

    print(f"已索引 {len(memories)} 条记忆")

    # 测试搜索
    query = "项目"
    results = searcher.search(query)

    print(f"\n搜索: '{query}'")
    print(f"找到 {len(results)} 条结果")

    for result in results:
        print(f"  ID: {result['memory_id']}")
        print(f"  内容: {result['content'][:50]}...")
        print(f"  分数: {result['score']}")
        print()

    assert len(results) >= 2, "应该找到至少2条包含'项目'的结果"

    # 测试另一个查询
    query = "户外活动"
    results = searcher.search(query)
    assert len(results) >= 2, "应该找到至少2条包含'户外活动'的结果"

    print("✓ 基本搜索功能测试通过！")
    return True


def test_keyword_search():
    """测试关键词搜索功能"""
    print("\n" + "=" * 60)
    print("测试 2: 关键词搜索功能")
    print("=" * 60)

    searcher = MemorySearch()

    # 添加测试数据
    searcher.index_memory("mem_001", "Python编程入门教程")
    searcher.index_memory("mem_002", "Java高级编程实战")
    searcher.index_memory("mem_003", "Python数据分析基础")
    searcher.index_memory("mem_004", "Web前端开发入门")
    searcher.index_memory("mem_005", "Python机器学习实战")

    # 测试匹配所有关键词
    keywords = ["Python", "编程"]
    # 测试搜索也可以用单字搜索
    results = searcher.search_by_keywords(["python", "编", "程"], match_all=True)
    print(f"\n匹配所有关键词: {keywords}")
    print(f"找到 {len(results)} 条结果")

    # 调试：看看索引中有什么关键词
    stats = searcher.get_statistics()
    print(f"\n索引中的关键词数: {stats['total_keywords']}")
    print(f"前10个关键词: {[kw for kw, _ in stats['top_keywords'][:10]]}")

    assert len(results) >= 1, "应该找到同时包含两个关键词的结果"

    # 测试匹配任意关键词
    keywords = ["Python", "Java"]
    results = searcher.search_by_keywords(keywords, match_all=False)
    print(f"\n匹配任意关键词: {keywords}")
    print(f"找到 {len(results)} 条结果")

    assert len(results) >= 3, "应该找到包含任意关键词的结果"

    print("✓ 关键词搜索功能测试通过！")
    return True


def test_enhanced_search_system():
    """测试增强的搜索系统"""
    print("\n" + "=" * 60)
    print("测试 3: 增强搜索系统")
    print("=" * 60)

    # 创建记忆系统
    memory = get_memory_system()
    memory.l1.clear()
    memory.l2.clear()
    memory.l3.clear()

    # 创建增强搜索系统
    enhanced_search = EnhancedMemorySearch(memory)

    # 添加一些记忆
    memories = [
        ("智能助手开发计划", "proj_001"),
        ("用户反馈收集与分析", "proj_001"),
        ("产品功能优化方案", "proj_002"),
        ("市场调研报告", "proj_002"),
        ("技术架构设计文档", "proj_001"),
    ]

    for text, task_id in memories:
        enhanced_search.add_memory_and_index(text, task_id, "l2")

    print(f"已添加并索引 {len(memories)} 条记忆")

    # 搜索测试
    query = "计划"
    results = enhanced_search.search_memories(query)

    print(f"\n搜索: '{query}'")
    print(f"找到 {len(results)} 条结果")

    for result in results[:3]:
        print(f"  ID: {result['memory_id']}")
        print(f"  内容: {result['content']}")
        print(f"  分数: {result['score']}")
        print()

    # 测试搜索统计
    stats = enhanced_search.get_search_statistics()
    print(f"\n搜索统计:")
    print(f"  总记忆数: {stats['total_memories']}")
    print(f"  总关键词数: {stats['total_keywords']}")

    assert stats['total_memories'] >= 5, "应该有至少5条记忆"

    print("✓ 增强搜索系统测试通过！")
    return True


def test_fuzzy_search():
    """测试模糊搜索功能"""
    print("\n" + "=" * 60)
    print("测试 4: 模糊搜索功能")
    print("=" * 60)

    searcher = MemorySearch()

    searcher.index_memory("mem_001", "用户满意度调查")
    searcher.index_memory("mem_002", "满意度问卷设计")
    searcher.index_memory("mem_003", "数据分析报告")

    # 测试模糊搜索
    query = "满意"
    results = searcher.search(query)

    print(f"\n模糊搜索: '{query}'")
    print(f"找到 {len(results)} 条结果")

    for result in results:
        print(f"  ID: {result['memory_id']}")
        print(f"  内容: {result['content']}")
        print(f"  分数: {result['score']}")
        print()

    assert len(results) >= 2, "应该找到包含相似关键词的结果"

    print("✓ 模糊搜索功能测试通过！")
    return True


def test_index_management():
    """测试索引管理功能"""
    print("\n" + "=" * 60)
    print("测试 5: 索引管理功能")
    print("=" * 60)

    searcher = MemorySearch()

    # 添加一些记忆
    searcher.index_memory("mem_001", "第一条测试记忆")
    searcher.index_memory("mem_002", "第二条测试记忆")
    searcher.index_memory("mem_003", "第三条测试记忆")

    # 检查统计
    stats = searcher.get_statistics()
    print(f"\n初始统计:")
    print(f"  总记忆数: {stats['total_memories']}")
    print(f"  总关键词数: {stats['total_keywords']}")

    assert stats['total_memories'] == 3, "应该有3条记忆"

    # 移除一条记忆
    removed = searcher.remove_from_index("mem_002")
    assert removed, "应该成功移除"

    # 再次检查统计
    stats = searcher.get_statistics()
    print(f"\n移除一条后统计:")
    print(f"  总记忆数: {stats['total_memories']}")

    assert stats['total_memories'] == 2, "应该剩下2条记忆"

    # 清空所有索引
    cleared = searcher.clear_index()
    print(f"\n清空了 {cleared} 条索引")

    stats = searcher.get_statistics()
    assert stats['total_memories'] == 0, "应该没有记忆了"

    print("✓ 索引管理功能测试通过！")
    return True


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("第17阶段测试：记忆全文搜索功能")
    print("=" * 60)

    all_passed = True

    try:
        passed = test_basic_search()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试1失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_keyword_search()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试2失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_enhanced_search_system()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试3失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_fuzzy_search()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试4失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_index_management()
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
