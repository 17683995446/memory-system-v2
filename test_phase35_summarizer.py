"""
第35阶段测试：记忆摘要与总结系统
遵循"图难于其易，为大于其细"原则
"""
import os
import sys
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.summarizer import (
    MemorySummarizer,
    SummaryLevel,
    SummaryType,
    get_summarizer,
    TextAnalyzer
)
from src.memory import get_memory_system


def test_text_analyzer():
    """测试文本分析器"""
    print("\n=== 测试文本分析器")

    analyzer = TextAnalyzer()

    # 测试关键词提取
    test_text = """
    人工智能是计算机科学的重要分支。重要的技术包括机器学习和深度学习。
    我们需要学习了如何应用这些技术来解决实际问题。
    """
    keywords = analyzer.extract_keywords(test_text, max_count=5)
    print(f"✓ 关键词提取: {keywords}")
    assert len(keywords) > 0

    # 测试分句
    sentences = analyzer.split_into_sentences(test_text)
    print(f"✓ 分句: {len(sentences)} 个句子")
    assert len(sentences) >= 1

    # 测试重要性计算
    for sentence in sentences:
        importance = analyzer.calculate_importance(sentence)
        print(f"  - 句子: {sentence[:30]}... 重要性: {importance:.2f}")

    print("✓ 文本分析器测试通过")


def test_basic_summarization():
    """测试基本摘要生成"""
    print("\n=== 测试基本摘要生成")

    summarizer = MemorySummarizer()

    # 创建测试记忆
    test_memories = [
        {"text": "今天学习了Python编程基础，包括变量、函数和循环。重要的是要练习。"},
        {"text": "明天需要复习面向对象编程，学习类和对象的概念。应该注意继承很重要。"},
        {"text": "项目截止日期是下周五，必须在那之前完成。有3个主要功能需要实现。"},
        {"text": "记得安装了一些重要的依赖库，版本号是1.2.3。"},
        {"text": "团队会议安排在周三下午3点，需要准备项目进度报告。重要事项包括需求分析。"}
    ]

    # 测试不同级别的摘要
    for level in [SummaryLevel.BRIEF, SummaryLevel.NORMAL, SummaryLevel.DETAILED]:
        result = summarizer.summarize_memories(test_memories, summary_level=level)
        print(f"\n✓ {level.value} 级别摘要:")
        print(f"  内容: {result.content[:100]}...")
        print(f"  要点: {len(result.key_points)} 个")
        print(f"  字数: {result.word_count}")
        assert result.content
        assert len(result.key_points) > 0

    print("✓ 基本摘要生成测试通过")


def test_summarization_types():
    """测试不同类型的摘要"""
    print("\n=== 测试不同类型的摘要")

    summarizer = MemorySummarizer()

    test_memories = [
        {"text": "人工智能技术在医疗领域有重要应用，可以辅助医生诊断疾病。这是一个重要的研究方向。"},
        {"text": "机器学习算法包括监督学习和无监督学习。需要了解不同算法的适用场景。"},
        {"text": "数据预处理是机器学习流程中的关键步骤，数据质量直接影响模型效果。"}
    ]

    # 测试不同摘要类型
    for summary_type in SummaryType:
        result = summarizer.summarize_memories(test_memories, summary_type=summary_type)
        print(f"\n✓ {summary_type.value} 类型摘要:")
        print(f"  内容: {result.content[:80]}...")
        assert result.summary_type == summary_type

    print("✓ 不同类型摘要测试通过")


def test_with_memory_system():
    """测试与记忆系统集成"""
    print("\n=== 测试与记忆系统集成")

    # 创建记忆系统
    memory_system = get_memory_system()
    summarizer = get_summarizer(memory_system)

    # 添加测试数据
    memory_system.add("第一个测试记忆内容，包含一些重要信息。这是一个测试。", "test_session_35)
    memory_system.add("第二个测试记忆，测试摘要功能是否正常工作。重要的是要确保准确性。", "test_session_35")
    memory_system.add("第三个测试记忆，添加更多内容来测试摘要生成。", "test_session_35")
    memory_system.add_fact("测试", "项目", "第35阶段测试记忆系统", "test")

    # 测试按层级摘要
    for level in ["l1", "l2", "l3"]:
        result = summarizer.summarize_by_level(level, summary_level=SummaryLevel.NORMAL)
        if result:
            print(f"\n✓ {level} 层级摘要:")
            print(f"  记忆数量: {result.memory_count}")
            print(f"  内容: {result.content[:80]}...")

    # 测试按会话摘要
    session_result = summarizer.summarize_by_session("test_session_35")
    if session_result:
        print(f"\n✓ 会话摘要:")
        print(f"  内容: {session_result.content[:80]}...")

    print("✓ 与记忆系统集成测试通过")


def test_topic_summary():
    """测试主题摘要"""
    print("\n=== 测试主题摘要")

    memory_system = get_memory_system()
    summarizer = get_summarizer(memory_system)

    # 添加一些关于特定主题的记忆
    memory_system.add("人工智能在医疗领域的应用前景很广阔。人工智能可以帮助医生提高诊断准确率。", "ai_session")
    memory_system.add("机器学习是人工智能的重要子领域。机器学习算法能够从数据中学习模式。", "ai_session")
    memory_system.add("深度学习是机器学习的一种，使用神经网络模型。", "ai_session")

    # 测试主题摘要
    result = summarizer.summarize_topic("人工智能")
    if result:
        print(f"\n✓ 主题摘要（人工智能）:")
        print(f"  内容: {result.content[:100]}...")
        print(f"  要点: {result.key_points}")
        assert result.summary_type == SummaryType.TOPIC

    print("✓ 主题摘要测试通过")


def test_weekly_summary():
    """测试周摘要"""
    print("\n=== 测试周摘要")

    memory_system = get_memory_system()
    summarizer = get_summarizer(memory_system)

    # 添加更多记忆
    for i in range(5):
        memory_system.add(f"周记忆内容 {i+1}，这是第 {i+1} 条测试内容。", f"session_{i}")

    # 测试周摘要
    result = summarizer.generate_weekly_summary()
    if result:
        print(f"\n✓ 周摘要:")
        print(f"  记忆数量: {result.memory_count}")
        print(f"  内容: {result.content[:100]}...")
        print(f"  元数据: {result.metadata}")
        assert result.metadata.get("period") == "weekly"

    print("✓ 周摘要测试通过")


def test_global_summarizer():
    """测试全局摘要器"""
    print("\n=== 测试全局摘要器")

    memory_system = get_memory_system()
    # 获取全局摘要器
    summarizer1 = get_summarizer(memory_system)
    summarizer2 = get_summarizer()

    # 验证是同一个实例
    assert summarizer1 is summarizer2
    print("✓ 全局摘要器单例模式正常")
    assert summarizer1.memory_system is not None
    print("✓ 记忆系统关联正常")

    print("✓ 全局摘要器测试通过")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("第35阶段测试：记忆摘要与总结系统")
    print("遵循原则：图难于其易，为大于其细")
    print("=" * 60)

    try:
        test_text_analyzer()
        test_basic_summarization()
        test_summarization_types()
        test_with_memory_system()
        test_topic_summary()
        test_weekly_summary()
        test_global_summarizer()

        print("\n" + "=" * 60)
        print("✓ 所有第35阶段测试通过！")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
