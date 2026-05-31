"""
第36阶段测试：记忆系统统计与报告系统
遵循"图难于其易，为大于其细"原则
"""
import os
import sys
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.statistics import (
    StatisticsCollector,
    ReportGenerator,
    TrendAnalyzer,
    ReportType,
    get_statistics_collector,
    get_report_generator
)
from src.memory import get_memory_system


def test_statistics_collector():
    """测试统计收集器"""
    print("\n=== 测试统计收集器")

    collector = StatisticsCollector()

    # 测试记录操作
    collector.record_operation("add", success=True, duration=0.05)
    collector.record_operation("recall", success=True, duration=0.03)
    collector.record_operation("add", success=True, duration=0.04)
    collector.record_operation("recall", success=False, duration=0.02)
    print("✓ 操作记录功能正常")

    # 测试获取操作统计
    stats = collector.get_operation_stats()
    assert "add" in stats
    assert stats["add"]["total_count"] == 2
    assert stats["add"]["success_count"] == 2
    print(f"✓ 操作统计: {stats['add']}")

    # 测试记录会话活动
    collector.record_session_activity("session_1", "memory_add")
    collector.record_session_activity("session_1", "memory_recall")
    collector.record_session_activity("session_2", "memory_add")
    print("✓ 会话活动记录功能正常")

    # 测试获取会话统计
    session_stats = collector.get_session_stats()
    assert session_stats["total_sessions"] == 2
    print(f"✓ 会话统计: {session_stats['total_sessions']} 个会话")

    # 测试记录记忆增长
    collector.record_memory_growth("l1", 10)
    collector.record_memory_growth("l1", 15)
    collector.record_memory_growth("l1", 20)
    growth_stats = collector.get_memory_growth_stats()
    assert growth_stats["current_count"] == 20
    print(f"✓ 记忆增长统计: {growth_stats}")

    # 测试重置
    collector.reset()
    stats_after_reset = collector.get_operation_stats()
    assert len(stats_after_reset) == 0
    print("✓ 重置功能正常")

    print("✓ 统计收集器测试通过")


def test_trend_analyzer():
    """测试趋势分析器"""
    print("\n=== 测试趋势分析器")

    collector = StatisticsCollector()

    # 添加一些测试数据
    for i in range(10):
        collector.record_memory_growth("l1", 5 + i * 2)
        collector.record_operation("add", success=True, duration=0.01 + i * 0.001)
        collector.record_operation("recall", success=True, duration=0.02 + i * 0.001)

    analyzer = TrendAnalyzer(collector)

    # 测试记忆趋势分析
    memory_trends = analyzer.analyze_memory_trends()
    assert "trend" in memory_trends
    assert "daily_average" in memory_trends
    print(f"✓ 记忆趋势: {memory_trends['trend_description']}")
    print(f"  日均增长: {memory_trends['daily_average']:.2f}")

    # 测试操作趋势分析
    operation_trends = analyzer.analyze_operation_trends()
    assert "most_active_operations" in operation_trends
    assert "overall_success_rate" in operation_trends
    print(f"✓ 操作趋势: {operation_trends['overall_success_rate']*100:.1f}% 成功率")

    # 测试会话趋势分析
    session_trends = analyzer.analyze_session_trends()
    assert "total_sessions" in session_trends
    print(f"✓ 会话趋势: {session_trends['total_sessions']} 个会话")

    print("✓ 趋势分析器测试通过")


def test_report_generator():
    """测试报告生成器"""
    print("\n=== 测试报告生成器")

    collector = StatisticsCollector()

    # 添加测试数据
    for i in range(5):
        collector.record_memory_growth("l1", 10 + i * 5)
        collector.record_operation("add", success=True, duration=0.05)
        collector.record_operation("recall", success=True, duration=0.03)
        collector.record_session_activity(f"session_{i}", "activity")

    generator = ReportGenerator(collector)

    # 测试生成周报
    weekly_report = generator.generate_report(ReportType.WEEKLY)
    assert weekly_report.report_type == ReportType.WEEKLY
    assert weekly_report.summary
    assert len(weekly_report.insights) > 0
    assert len(weekly_report.recommendations) > 0
    print(f"✓ 周报生成成功")
    print(f"  摘要: {weekly_report.summary}")
    print(f"  洞察: {weekly_report.insights}")
    print(f"  建议: {weekly_report.recommendations}")

    # 测试生成日报
    daily_report = generator.generate_report(ReportType.DAILY)
    assert daily_report.report_type == ReportType.DAILY
    print(f"✓ 日报生成成功")

    # 测试生成月报
    monthly_report = generator.generate_report(ReportType.MONTHLY)
    assert monthly_report.report_type == ReportType.MONTHLY
    print(f"✓ 月报生成成功")

    # 测试导出JSON
    json_export = generator.export_report_json(weekly_report)
    assert "report_id" in json_export
    print("✓ JSON导出功能正常")

    # 测试导出文本
    text_export = generator.export_report_text(weekly_report)
    assert "记忆系统" in text_export
    assert "周报" in text_export
    print("✓ 文本导出功能正常")

    print("✓ 报告生成器测试通过")


def test_global_instances():
    """测试全局单例"""
    print("\n=== 测试全局单例")

    # 获取全局统计收集器
    collector1 = get_statistics_collector()
    collector2 = get_statistics_collector()
    assert collector1 is collector2
    print("✓ 统计收集器单例模式正常")

    # 获取全局报告生成器
    generator1 = get_report_generator()
    generator2 = get_report_generator()
    assert generator1 is generator2
    print("✓ 报告生成器单例模式正常")

    # 测试集成
    collector = get_statistics_collector()
    collector.record_operation("test_op", True, 0.01)
    report = get_report_generator().generate_report()
    assert report is not None
    print("✓ 全局实例集成正常")

    print("✓ 全局单例测试通过")


def test_with_memory_system():
    """测试与记忆系统集成"""
    print("\n=== 测试与记忆系统集成")

    memory_system = get_memory_system()
    collector = get_statistics_collector()

    # 模拟记忆系统操作
    for i in range(3):
        start = time.time()
        memory_system.add(f"测试记忆 {i}", f"session_{i}")
        duration = time.time() - start
        collector.record_operation("add", True, duration)

    for i in range(2):
        start = time.time()
        memory_system.recall("测试", f"session_{i}")
        duration = time.time() - start
        collector.record_operation("recall", True, duration)

    # 生成报告
    report = get_report_generator().generate_report()
    assert report is not None
    assert report.memory_stats is not None
    assert report.operation_stats is not None
    print(f"✓ 与记忆系统集成正常")
    print(f"  记忆统计: {report.memory_stats}")
    print(f"  操作统计: {report.operation_stats}")

    print("✓ 与记忆系统集成测试通过")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("第36阶段测试：记忆系统统计与报告系统")
    print("遵循原则：图难于其易，为大于其细")
    print("=" * 60)

    try:
        test_statistics_collector()
        test_trend_analyzer()
        test_report_generator()
        test_global_instances()
        test_with_memory_system()

        print("\n" + "=" * 60)
        print("✓ 所有第36阶段测试通过！")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
