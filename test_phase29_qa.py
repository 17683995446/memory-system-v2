"""
第29阶段测试：记忆智能问答系统
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.qa import (
    MemoryQASystem,
    QuestionType,
    AnswerQuality,
    QueryAnalyzer,
    MemoryRetriever,
    AnswerGenerator,
    ConversationManager,
)


def create_test_memories() -> list:
    """创建测试记忆"""
    memories = [
        {
            "id": "mem_001",
            "text": "项目启动会议在2026年1月15日举行，确定了Q1季度的目标和计划",
            "timestamp": time.time() - 86400 * 120,  # 4个月前
        },
        {
            "id": "mem_002",
            "text": "张三负责前端开发，使用React框架，预计交付时间为3月底",
            "timestamp": time.time() - 86400 * 90,  # 3个月前
        },
        {
            "id": "mem_003",
            "text": "李四负责后端开发，使用Python和FastAPI，数据库采用PostgreSQL",
            "timestamp": time.time() - 86400 * 60,  # 2个月前
        },
        {
            "id": "mem_004",
            "text": "本周完成了用户界面设计评审，收集了10条修改意见，下周开始修改",
            "timestamp": time.time() - 86400 * 3,  # 3天前
        },
        {
            "id": "mem_005",
            "text": "昨天的测试发现了5个bug，其中2个严重，需要在本周修复",
            "timestamp": time.time() - 86400 * 1,  # 1天前
        },
        {
            "id": "mem_006",
            "text": "项目预算为100万元，目前已使用60万元，剩余40万元",
            "timestamp": time.time() - 86400 * 30,  # 1个月前
        },
        {
            "id": "mem_007",
            "text": "客户要求在5月1日前上线第一版功能，包括用户登录、数据展示",
            "timestamp": time.time() - 86400 * 15,  # 15天前
        },
        {
            "id": "mem_008",
            "text": "API文档地址是https://api.example.com/docs，账号是admin，密码需要联系运维",
            "timestamp": time.time() - 86400 * 5,  # 5天前
        },
    ]
    return memories


def test_query_analyzer():
    """测试查询分析器"""
    print("\n" + "=" * 60)
    print("测试 1：查询分析器")
    print("=" * 60)

    analyzer = QueryAnalyzer()

    test_questions = [
        "什么是项目启动会议？",
        "总结一下近期的项目进展",
        "列出所有开发人员",
        "最近有什么重要消息？",
        "查找一下API文档",
        "这是一个普通的问题",
    ]

    for question in test_questions:
        analysis = analyzer.analyze(question)
        print(f"\n问题: {question}")
        print(f"  类型: {analysis['question_type'].value}")
        print(f"  关键词: {analysis['keywords']}")
        print(f"  时间范围: {analysis['time_range']}")

    print("\n✓ 查询分析器测试通过！")
    return True


def test_memory_retriever():
    """测试记忆检索器"""
    print("\n" + "=" * 60)
    print("测试 2：记忆检索器")
    print("=" * 60)

    retriever = MemoryRetriever()
    memories = create_test_memories()

    test_cases = [
        {
            "question": "项目启动",
            "keywords": ["项目", "启动"],
        },
        {
            "question": "张三负责什么",
            "keywords": ["张三", "负责"],
        },
        {
            "question": "API文档在哪里",
            "keywords": ["API", "文档"],
        },
    ]

    for case in test_cases:
        question_analysis = {
            "keywords": case["keywords"],
            "time_range": None,
            "entities": [],
        }
        results = retriever.retrieve(question_analysis, memories, top_k=3)
        print(f"\n查询: {case['question']}")
        for i, result in enumerate(results, 1):
            print(f"  {i}. (分数: {result['score']:.2f}) {result['memory']['text'][:50]}...")

    print("\n✓ 记忆检索器测试通过！")
    return True


def test_answer_generator():
    """测试答案生成器"""
    print("\n" + "=" * 60)
    print("测试 3：答案生成器")
    print("=" * 60)

    generator = AnswerGenerator()
    memories = create_test_memories()

    # 模拟检索结果
    retrieved = [
        {"memory": memories[0], "score": 0.9},
        {"memory": memories[1], "score": 0.7},
    ]

    test_cases = [
        {
            "type": QuestionType.FACTUAL,
            "question": "项目启动会议是什么时候？",
        },
        {
            "type": QuestionType.SUMMARY,
            "question": "总结一下项目情况",
        },
        {
            "type": QuestionType.LIST,
            "question": "有哪些开发人员？",
        },
    ]

    for case in test_cases:
        question_analysis = {"question_type": case["type"]}
        answer = generator.generate(case["question"], question_analysis, retrieved)
        print(f"\n问题类型: {case['type'].value}")
        print(f"答案质量: {answer['quality'].value}")
        print(f"置信度: {answer['confidence']:.2f}")
        print(f"答案:\n{answer['answer']}")

    print("\n✓ 答案生成器测试通过！")
    return True


def test_conversation_manager():
    """测试对话管理器"""
    print("\n" + "=" * 60)
    print("测试 4：对话管理器")
    print("=" * 60)

    manager = ConversationManager()

    # 模拟一些对话
    sample_answer = {
        "answer": "这是一个测试回答",
        "quality": AnswerQuality.GOOD,
        "sources": [],
        "confidence": 0.8,
    }

    # 添加对话
    conv_id = manager.add_interaction("你好", sample_answer)
    manager.add_interaction("介绍一下项目", sample_answer, conv_id)
    manager.add_interaction("谢谢", sample_answer, conv_id)

    print(f"对话ID: {conv_id}")

    # 获取历史
    history = manager.get_history(conv_id)
    print(f"\n历史对话数: {len(history)}")
    for i, item in enumerate(history, 1):
        print(f"  {i}. Q: {item['question']}")

    # 清除对话
    manager.clear_history(conv_id)
    print(f"\n清除后对话数: {len(manager.get_history(conv_id))}")

    print("\n✓ 对话管理器测试通过！")
    return True


def test_qa_system():
    """测试完整问答系统"""
    print("\n" + "=" * 60)
    print("测试 5：完整问答系统")
    print("=" * 60)

    qa_system = MemoryQASystem()
    memories = create_test_memories()

    test_questions = [
        "项目启动会议是什么时候？",
        "张三负责什么工作？",
        "总结一下近期的项目情况",
        "最近有什么重要的事情？",
        "API文档在哪里？",
        "项目预算是多少？",
    ]

    conversation_id = None
    for i, question in enumerate(test_questions, 1):
        result = qa_system.ask(question, memories, conversation_id)
        conversation_id = result["conversation_id"]

        print(f"\n问题 {i}: {question}")
        print(f"类型: {result['analysis']['question_type'].value}")
        print(f"答案质量: {result['answer']['quality'].value}")
        print(f"置信度: {result['answer']['confidence']:.2f}")
        print(f"答案:\n{result['answer']['answer']}")
        print(f"检索到 {len(result['retrieved_memories'])} 条相关记忆")

    # 测试对话历史
    history = qa_system.get_conversation_history(conversation_id)
    print(f"\n✓ 对话历史记录了 {len(history)} 轮交互")

    print("\n✓ 完整问答系统测试通过！")
    return True


def test_batch_ask():
    """测试批量提问"""
    print("\n" + "=" * 60)
    print("测试 6：批量提问")
    print("=" * 60)

    qa_system = MemoryQASystem()
    memories = create_test_memories()

    questions = [
        "项目启动时间",
        "张三负责什么",
        "预算情况",
    ]

    results = qa_system.batch_ask(questions, memories)

    print(f"批量提问了 {len(results)} 个问题")
    for i, result in enumerate(results, 1):
        print(f"\n问题 {i}: {result['question']}")
        print(f"  答案质量: {result['answer']['quality'].value}")

    print("\n✓ 批量提问测试通过！")
    return True


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("第29阶段测试：记忆智能问答系统")
    print("=" * 60)

    all_passed = True

    try:
        passed = test_query_analyzer()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试1失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_memory_retriever()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试2失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_answer_generator()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试3失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_conversation_manager()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试4失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_qa_system()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试5失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_batch_ask()
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
