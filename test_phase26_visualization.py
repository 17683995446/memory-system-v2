"""
第26阶段测试：记忆可视化/展示功能
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.memory import get_memory_system
from src.visualization import (
    MemoryDisplay,
    MemoryCard,
    MemoryNavigator,
    EnhancedMemoryWithVisualization
)


def test_memory_display():
    """测试记忆展示格式化"""
    print("\n" + "=" * 60)
    print("测试 1: 记忆展示格式化")
    print("=" * 60)

    # 测试内容
    content = """项目总结
    今天完成了重要项目的核心功能。主要工作包括：
    1. 模块A的实现和测试
    2. 模块B的集成和调试
    3. 性能优化和安全检查
    """

    # 测试不同格式
    print("\n原始内容:")
    print(content[:100] + "..." if len(content) > 100 else content)

    # 文本格式
    text_format = MemoryDisplay.format_content(content, format_type="text")
    print("\n文本格式:")
    print(text_format[:100] + "..." if len(text_format) > 100 else text_format)

    # Markdown格式
    markdown_format = MemoryDisplay.format_content(content, format_type="markdown")
    print("\nMarkdown格式:")
    print(markdown_format[:100] + "..." if len(markdown_format) > 100 else markdown_format)

    # HTML格式
    html_format = MemoryDisplay.format_content(content, format_type="html")
    print("\nHTML格式:")
    print(html_format[:100] + "..." if len(html_format) > 100 else html_format)

    # 美观格式
    pretty_format = MemoryDisplay.format_content(content, format_type="pretty")
    print("\n美观格式:")
    print(pretty_format[:100] + "..." if len(pretty_format) > 100 else pretty_format)

    # 高亮测试
    highlighted = MemoryDisplay.highlight_keywords(content, ["项目", "模块", "测试"])
    print("\n关键词高亮:")
    print(highlighted[:150] + "..." if len(highlighted) > 150 else highlighted)

    print("\n✓ 记忆展示格式化测试通过！")
    return True


def test_memory_card():
    """测试记忆卡片"""
    print("\n" + "=" * 60)
    print("测试 2: 记忆卡片")
    print("=" * 60)

    # 创建几个测试记忆
    cards = []
    for i in range(5):
        content = f"测试记忆内容 {i+1}: 这是第 {i+1} 条记忆的完整内容。"
        card = MemoryCard.create_card(
            memory_id=f"mem_{i+1}",
            content=content,
            memory_level=["L1", "L2", "L3"][i % 3]
        )
        cards.append(card)
        print(f"\n卡片 {i+1}:")
        print(f"  ID: {card['memory_id']}")
        print(f"  预览: {card['content_preview']}")
        print(f"  层级: {card['memory_level']}")

    # 紧凑格式渲染
    print("\n紧凑格式:")
    compact = MemoryCard.render_cards(cards, "compact")
    print(compact)

    # 详细格式渲染
    print("\n详细格式:")
    detailed = MemoryCard.render_cards(cards[:2], "detailed")
    print(detailed)

    # 网格格式渲染
    print("\n网格格式:")
    grid = MemoryCard.render_cards(cards, "grid")
    print(grid)

    print("\n✓ 记忆卡片测试通过！")
    return True


def test_memory_navigator():
    """测试记忆导航器"""
    print("\n" + "=" * 60)
    print("测试 3: 记忆导航器")
    print("=" * 60)

    # 创建测试记忆数据
    memories = []
    for i in range(10):
        memories.append({
            "memory_id": f"mem_{i}",
            "content": f"测试记忆内容 {i}",
            "memory_level": ["L1", "L2", "L3"][i % 3],
            "created_at": time.time() - (9 - i) * 3600
        })

    navigator = MemoryNavigator(memories)

    # 获取当前
    current = navigator.get_current()
    print(f"\n当前记忆: {current['memory_id']}")

    # 导航
    print("\n导航测试:")
    for i in range(3):
        current = navigator.next()
        print(f"  下一个: {current['memory_id']}")

    for i in range(2):
        current = navigator.previous()
        print(f"  上一个: {current['memory_id']}")

    # 过滤
    print("\n过滤测试:")
    navigator.filter_by_level("L2")
    filtered = navigator.apply_filters()
    print(f"  过滤 L2: {len(filtered)} 条记忆")

    # 重置
    navigator.reset()
    print("\n导航器重置完成")

    print("\n✓ 记忆导航器测试通过！")
    return True


def test_enhanced_memory():
    """测试增强记忆系统"""
    print("\n" + "=" * 60)
    print("测试 4: 增强记忆系统")
    print("=" * 60)

    memory = get_memory_system()
    enhanced = EnhancedMemoryWithVisualization(memory)

    # 清空现有数据
    memory.l1.clear()
    memory.l2.clear()
    memory.l3.clear()

    # 添加一些记忆
    sample_contents = [
        "项目总结：今天完成了重要项目的核心功能。主要工作包括：模块A的实现和测试，模块B的集成和调试，性能优化和安全检查。",
        "学习笔记：今天学习了Python的高级特性，包括装饰器、迭代器和上下文管理器。",
        "会议记录：项目组会议讨论了下一阶段的工作计划，确定了里程碑和交付日期。"
    ]
    mem_ids = []
    for i, content in enumerate(sample_contents):
        mem_id = memory.add(content, "test", "l2")
        mem_ids.append(mem_id)

    print(f"\n添加了 {len(mem_ids)} 条记忆")

    # 展示单个记忆
    display = enhanced.display_memory(mem_ids[0], format_type="pretty")
    print(f"\n展示单条记忆:")
    print(display[:200] + "..." if len(display) > 200 else display)

    # 展示所有记忆
    all_display = enhanced.display_all_memories("compact")
    print(f"\n展示所有记忆:")
    print(all_display)

    # 高亮关键词
    if mem_ids:
        highlighted = enhanced.highlight_memory_content(mem_ids[0], ["项目", "模块", "学习"])
        print(f"\n关键词高亮:")
        print(highlighted[:150] + "..." if len(highlighted) > 150 else highlighted)

    # 浏览记忆
    browse = enhanced.browse_memories()
    print(f"\n浏览记忆:")
    print(browse[:200] + "..." if len(browse) > 200 else browse)

    print("\n✓ 增强记忆系统测试通过！")
    return True


def test_integration():
    """测试集成功能"""
    print("\n" + "=" * 60)
    print("测试 5: 集成功能")
    print("=" * 60)

    memory = get_memory_system()
    enhanced = EnhancedMemoryWithVisualization(memory)

    # 清空现有数据
    memory.l1.clear()
    memory.l2.clear()
    memory.l3.clear()

    # 添加更多记忆
    contents = [
        "重要文档：项目需求规格说明书",
        "学习笔记：机器学习基础概念",
        "工作记录：2026年5月工作要点",
        "会议摘要：技术架构评审会议"
    ]
    for content in contents:
        memory.add(content, "test", "l2")

    # 创建导航器
    navigator = enhanced.create_navigator()
    print(f"\n导航器创建成功")

    # 测试不同显示格式
    print("\n紧凑格式:")
    compact = enhanced.display_all_memories("compact")
    print(compact)

    print("\n详细格式:")
    detailed = enhanced.display_all_memories("detailed")
    print(detailed[:300] + "..." if len(detailed) > 300 else detailed)

    print("\n网格格式:")
    grid = enhanced.display_all_memories("grid")
    print(grid)

    # 测试导航
    print("\n导航测试:")
    for i in range(3):
        current = navigator.next()
        preview = MemoryCard.create_card(
            current['memory_id'],
            current['content'],
            current['memory_level']
        )['content_preview']
        print(f"  导航到: {preview}")

    print("\n✓ 集成功能测试通过！")
    return True


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("第26阶段测试：记忆可视化/展示功能")
    print("=" * 60)

    all_passed = True

    try:
        passed = test_memory_display()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试1失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_memory_card()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试2失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_memory_navigator()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试3失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_enhanced_memory()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试4失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_integration()
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
