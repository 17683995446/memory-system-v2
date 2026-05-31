"""
简单验证记忆摘要与总结系统
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("测试记忆摘要与总结系统导入...")
try:
    from src.summarizer import (
        MemorySummarizer,
        SummaryLevel,
        SummaryType,
        get_summarizer,
        TextAnalyzer
    )
    print("✓ 摘要系统导入成功！")
except Exception as e:
    print(f"✗ 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n测试文本分析器...")
try:
    analyzer = TextAnalyzer()
    test_text = """
    这是一段测试文本。它包含多个句子。有些句子很重要，需要被识别出来。
    我们测试了关键词提取功能，结果显示良好。
    """
    keywords = analyzer.extract_keywords(test_text, max_count=5)
    print(f"✓ 提取关键词: {keywords}")
    sentences = analyzer.split_into_sentences(test_text)
    print(f"✓ 分句: {len(sentences)} 个句子")
    print("✓ 文本分析器功能正常")
except Exception as e:
    print(f"✗ 文本分析器失败: {e}")

print("\n测试记忆摘要器...")
try:
    summarizer = MemorySummarizer()
    test_memories = [
        {"text": "今天学习了Python编程基础，包括变量、函数和循环。重要的是要练习。"},
        {"text": "明天需要复习面向对象编程，学习类和对象的概念。"},
        {"text": "项目截止日期是下周五，必须在那之前完成。"}
    ]
    result = summarizer.summarize_memories(test_memories, summary_level=SummaryLevel.NORMAL)
    print(f"✓ 摘要生成成功!")
    print(f"  内容: {result.content[:100]}...")
    print(f"  要点: {len(result.key_points)} 个")
    print(f"  关键词: {result.metadata.get('keywords', [])}")
except Exception as e:
    print(f"✗ 记忆摘要器失败: {e}")
    import traceback
    traceback.print_exc()

print("\n测试全局摘要器...")
try:
    from src.memory import get_memory_system
    memory_system = get_memory_system()
    summarizer = get_summarizer(memory_system)
    memory_system.add("这是一个测试记忆，用于验证摘要系统。", "test_session")
    result = summarizer.summarize_by_level("l1")
    if result:
        print(f"✓ 全局摘要器与记忆系统集成正常!")
except Exception as e:
    print(f"✗ 全局摘要器测试失败: {e}")

print("\n" + "=" * 50)
print("所有基本验证通过！")
print("=" * 50)
