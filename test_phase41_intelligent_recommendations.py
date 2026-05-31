"""
第41阶段测试：智能建议和推荐功能
遵循"图难于其易，为大于其细"原则
"""

import sys
import os
import time
import random

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.intelligent_recommendations import (
    IntelligentSuggestionEngine,
    UserBehaviorAnalyzer,
    MemoryAssociator,
    MemoryRecommender,
    PersonalizedLearner,
    UserAction,
    ActionType,
    RecommendationType,
    get_intelligent_engine
)


def test_user_behavior_analyzer():
    """测试用户行为分析器"""
    print("\n=== 测试用户行为分析器 ===")
    
    analyzer = UserBehaviorAnalyzer()
    
    # 模拟用户行为
    user_id = "test_user_1"
    
    # 记录一些行为
    actions = [
        (ActionType.VIEW, "mem_1"),
        (ActionType.VIEW, "mem_2"),
        (ActionType.CREATE, "mem_3"),
        (ActionType.VIEW, "mem_1"),
        (ActionType.UPDATE, "mem_2"),
        (ActionType.FAVORITE, "mem_1"),
        (ActionType.SEARCH, None, "test query"),
    ]
    
    for action_type, memory_id, *rest in actions:
        action = UserAction(
            user_id=user_id,
            action_type=action_type,
            memory_id=memory_id,
            query=rest[0] if rest else None
        )
        analyzer.record_action(action)
        time.sleep(0.01)  # 稍微延迟确保时间戳不同
    
    # 获取用户画像
    profile = analyzer.get_user_profile(user_id)
    
    print(f"用户画像: {profile}")
    assert profile["user_id"] == user_id
    assert profile["total_actions"] == len(actions)
    assert profile["active_memory_count"] == 3
    
    print("✓ 用户行为分析器测试通过")


def test_memory_associator():
    """测试记忆关联发现器"""
    print("\n=== 测试记忆关联发现器 ===")
    
    associator = MemoryAssociator()
    
    # 添加共现关系
    associator.add_co_occurrence("mem_1", "mem_2")
    associator.add_co_occurrence("mem_1", "mem_2")
    associator.add_co_occurrence("mem_1", "mem_3")
    associator.add_co_occurrence("mem_2", "mem_3")
    
    # 获取关联记忆
    associations = associator.get_associated_memories("mem_1", limit=5)
    
    print(f"mem_1 的关联记忆: {associations}")
    assert len(associations) >= 2
    
    # 检查关联强度
    for memory_id, strength in associations:
        assert strength > 0
    
    print("✓ 记忆关联发现器测试通过")


def test_recommender():
    """测试推荐系统"""
    print("\n=== 测试推荐系统 ===")
    
    recommender = MemoryRecommender()
    
    # 注册一些记忆
    test_memories = [
        ("mem_1", "Python is a programming language", {"topic": "programming"}),
        ("mem_2", "Machine learning is fun", {"topic": "ml"}),
        ("mem_3", "JavaScript and web development", {"topic": "web"}),
        ("mem_4", "Data science and Python", {"topic": "data"}),
    ]
    
    for mem_id, content, metadata in test_memories:
        recommender.register_memory(mem_id, content, metadata)
    
    # 模拟用户行为
    user_id = "user_recommend_test"
    
    # 创建一些用户行为
    actions = [
        (ActionType.VIEW, "mem_1"),
        (ActionType.VIEW, "mem_2"),
        (ActionType.VIEW, "mem_1"),
        (ActionType.FAVORITE, "mem_1"),
        (ActionType.VIEW, "mem_4"),
    ]
    
    for action_type, memory_id in actions:
        action = UserAction(
            user_id=user_id,
            action_type=action_type,
            memory_id=memory_id
        )
        recommender.record_user_action(action)
        time.sleep(0.01)
    
    # 获取推荐
    recommendations = recommender.get_recommendations(user_id, limit=5)
    
    print(f"推荐结果:")
    for rec in recommendations:
        print(f"  - {rec.memory_id}: {rec.score:.2f} ({rec.type.value}) - {rec.reason}")
    
    assert len(recommendations) > 0
    
    # 检查推荐类型
    types_in_result = {rec.type for rec in recommendations}
    print(f"包含的推荐类型: {[t.value for t in types_in_result]}")
    
    print("✓ 推荐系统测试通过")


def test_personalized_learner():
    """测试个性化学习器"""
    print("\n=== 测试个性化学习器 ===")
    
    learner = PersonalizedLearner()
    
    user_id = "user_learn_test"
    
    # 记录一些反馈
    learner.record_feedback(user_id, "mem_1", True)
    learner.record_feedback(user_id, "mem_1", True)
    learner.record_feedback(user_id, "mem_2", False)
    
    # 获取自适应评分
    score, reason = learner.get_adaptive_score(user_id, "mem_1")
    print(f"mem_1 的自适应评分: {score:.2f} - {reason}")
    assert score > 0.5
    
    score2, reason2 = learner.get_adaptive_score(user_id, "mem_2")
    print(f"mem_2 的自适应评分: {score2:.2f} - {reason2}")
    assert score2 < 0.5
    
    print("✓ 个性化学习器测试通过")


def test_intelligent_engine():
    """测试智能建议引擎"""
    print("\n=== 测试智能建议引擎 ===")
    
    engine = IntelligentSuggestionEngine()
    
    # 注册记忆
    memories = [
        ("mem_a", "The quick brown fox jumps", {"type": "text"}),
        ("mem_b", "Python programming tutorial", {"type": "tutorial"}),
        ("mem_c", "Machine learning basics", {"type": "course"}),
        ("mem_d", "Web development with JavaScript", {"type": "guide"}),
    ]
    
    for mem_id, content, meta in memories:
        engine.register_memory(mem_id, content, meta)
    
    # 模拟用户行为
    user_id = "user_intelligent_test"
    
    user_actions = [
        (ActionType.VIEW, "mem_a"),
        (ActionType.VIEW, "mem_b"),
        (ActionType.CREATE, "mem_b"),
        (ActionType.VIEW, "mem_a"),
        (ActionType.FAVORITE, "mem_b"),
        (ActionType.SEARCH, "mem_c", "learning"),
    ]
    
    for action_type, memory_id, *rest in user_actions:
        engine.record_user_action(
            user_id=user_id,
            action_type=action_type,
            memory_id=memory_id,
            query=rest[0] if rest else None
        )
    
    # 获取建议
    suggestions = engine.get_suggestions(user_id, limit=5)
    
    print(f"智能建议:")
    for i, rec in enumerate(suggestions, 1):
        print(f"  {i}. {rec.memory_id} [{rec.type.value}] - Score: {rec.score:.2f} - {rec.reason}")
    
    assert len(suggestions) > 0
    
    # 测试智能补全
    completions = engine.get_smart_completion(user_id, "Python")
    print(f"\n智能补全建议 (查询: 'Python'):")
    for comp in completions:
        print(f"  - {comp['suggested_content']}")
    
    # 测试上下文提醒
    context = {"current_task": "programming"}
    reminders = engine.get_contextual_reminders(user_id, context)
    print(f"\n上下文提醒:")
    for rem in reminders:
        print(f"  - {rem['type']}: {rem['reason']}")
    
    print("✓ 智能建议引擎测试通过")


def test_feedback_optimization():
    """测试反馈优化"""
    print("\n=== 测试反馈优化 ===")
    
    engine = IntelligentSuggestionEngine()
    
    # 设置数据
    engine.register_memory("mem_feedback", "Feedback test content")
    
    user_id = "user_feedback_test"
    engine.record_user_action(user_id, ActionType.VIEW, "mem_feedback")
    
    # 记录正面反馈
    engine.record_feedback(user_id, "mem_feedback", True)
    
    # 获取建议
    suggestions = engine.get_suggestions(user_id, limit=3)
    
    # 再次记录更多正面反馈
    engine.record_feedback(user_id, "mem_feedback", True)
    engine.record_feedback(user_id, "mem_feedback", True)
    
    # 再次获取建议
    optimized_suggestions = engine.get_suggestions(user_id, limit=3)
    
    print("反馈优化测试完成")
    print("✓ 反馈优化测试通过")


def test_multiple_users():
    """测试多用户场景"""
    print("\n=== 测试多用户场景 ===")
    
    engine = IntelligentSuggestionEngine()
    
    # 注册内容
    engine.register_memory("shared_mem_1", "Shared content 1")
    engine.register_memory("shared_mem_2", "Shared content 2")
    engine.register_memory("shared_mem_3", "Shared content 3")
    
    # 用户1的行为
    user1 = "user_1"
    engine.record_user_action(user1, ActionType.VIEW, "shared_mem_1")
    engine.record_user_action(user1, ActionType.FAVORITE, "shared_mem_1")
    engine.record_user_action(user1, ActionType.VIEW, "shared_mem_2")
    
    # 用户2的行为
    user2 = "user_2"
    engine.record_user_action(user2, ActionType.VIEW, "shared_mem_3")
    engine.record_user_action(user2, ActionType.UPDATE, "shared_mem_3")
    engine.record_user_action(user2, ActionType.VIEW, "shared_mem_2")
    
    # 分别获取推荐
    rec1 = engine.get_suggestions(user1, limit=3)
    rec2 = engine.get_suggestions(user2, limit=3)
    
    print(f"用户1的推荐: {[r.memory_id for r in rec1]}")
    print(f"用户2的推荐: {[r.memory_id for r in rec2]}")
    
    assert len(rec1) > 0
    assert len(rec2) > 0
    
    print("✓ 多用户场景测试通过")


def test_global_instance():
    """测试全局单例"""
    print("\n=== 测试全局单例 ===")
    
    engine1 = get_intelligent_engine()
    engine2 = get_intelligent_engine()
    
    assert engine1 is engine2
    print("✓ 全局单例测试通过")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("第41阶段测试：智能建议和推荐功能")
    print("遵循原则：图难于其易，为大于其细")
    print("=" * 60)
    
    try:
        test_user_behavior_analyzer()
        test_memory_associator()
        test_recommender()
        test_personalized_learner()
        test_intelligent_engine()
        test_feedback_optimization()
        test_multiple_users()
        test_global_instance()
        
        print("\n" + "=" * 60)
        print("✓ 所有第41阶段测试通过！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
