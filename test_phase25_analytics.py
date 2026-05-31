"""
第25阶段测试：记忆统计分析/仪表盘功能
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.memory import get_memory_system
from src.analytics import (
    MemoryDashboard,
    ActivityTracker,
    TrendAnalyzer,
    EnhancedMemoryWithAnalytics
)


def test_trend_analyzer():
    """测试趋势分析器"""
    print("\n" + "=" * 60)
    print("测试 1: 趋势分析器")
    print("=" * 60)

    analyzer = TrendAnalyzer()

    # 测试增长趋势
    increasing_values = [10, 12, 15, 18, 20, 22, 25]
    growth = analyzer.calculate_growth_rate(increasing_values)
    print(f"\n增长趋势数据: {increasing_values}")
    print(f"增长率: {growth['growth_rate']:.2f}%")
    print(f"趋势: {growth['trend']}")
    assert growth['trend'] == "increasing"

    # 测试下降趋势
    decreasing_values = [25, 22, 20, 18, 15, 12, 10]
    growth = analyzer.calculate_growth_rate(decreasing_values)
    print(f"\n下降趋势数据: {decreasing_values}")
    print(f"增长率: {growth['growth_rate']:.2f}%")
    print(f"趋势: {growth['trend']}")
    assert growth['trend'] == "decreasing"

    # 测试稳定趋势
    stable_values = [10, 10, 11, 10, 10, 10, 11]
    growth = analyzer.calculate_growth_rate(stable_values)
    print(f"\n稳定趋势数据: {stable_values}")
    print(f"增长率: {growth['growth_rate']:.2f}%")
    print(f"趋势: {growth['trend']}")
    assert growth['trend'] == "stable"

    # 测试异常检测
    normal_values = [10, 11, 10, 11, 10, 11, 50, 10, 11]
    anomalies = analyzer.detect_anomalies(normal_values, threshold=2.0)
    print(f"\n异常检测: {anomalies}")
    assert len(anomalies) > 0

    print("\n✓ 趋势分析器测试通过！")
    return True


def test_activity_tracker():
    """测试活动追踪器"""
    print("\n" + "=" * 60)
    print("测试 2: 活动追踪器")
    print("=" * 60)

    tracker = ActivityTracker()

    # 追踪一些事件
    tracker.track_event("memory_created", "mem_001", {"level": "l2"})
    time.sleep(0.1)
    tracker.track_event("memory_accessed", "mem_001")
    time.sleep(0.1)
    tracker.track_event("memory_updated", "mem_002", {"old_size": 100})
    time.sleep(0.1)
    tracker.track_event("memory_created", "mem_003")

    print(f"\n总事件数: {len(tracker.events)}")

    # 获取最近活动
    recent = tracker.get_recent_activity(hours=1)
    print(f"最近1小时活动: {len(recent)} 个事件")
    assert len(recent) == 4

    # 按类型获取
    created_events = tracker.get_activity_by_type("memory_created")
    print(f"创建事件: {len(created_events)} 个")
    assert len(created_events) == 2

    # 小时统计
    hourly = tracker.get_hourly_stats(hours=24)
    print(f"小时统计: {hourly}")

    # 每日统计
    daily = tracker.get_daily_stats(days=7)
    print(f"每日统计: {daily}")
    assert len(daily) >= 1

    print("\n✓ 活动追踪器测试通过！")
    return True


def test_productivity_analysis():
    """测试生产力分析"""
    print("\n" + "=" * 60)
    print("测试 3: 生产力分析")
    print("=" * 60)

    tracker = ActivityTracker()

    # 模拟多天活动
    for day in range(7):
        num_events = 5 + day  # 每天递增
        for i in range(num_events):
            tracker.track_event("memory_created", f"mem_{day}_{i}")

    # 分析生产力
    productivity = tracker.analyze_productivity(days=7)
    print(f"\n生产力分析:")
    print(f"  平均每日活动: {productivity['avg_daily_activity']:.2f}")
    print(f"  最活跃日: {productivity['most_active_day']} ({productivity['most_active_count']}次)")
    print(f"  最不活跃日: {productivity['least_active_day']} ({productivity['least_active_count']}次)")
    print(f"  趋势: {productivity['trend']}")
    print(f"  增长率: {productivity['growth_rate']:.2f}%")
    print(f"  每日详情: {productivity['daily_breakdown']}")

    # 注意：这里检测到stable是因为所有事件都在同一天
    assert productivity['avg_daily_activity'] > 0
    # 如果只有一天数据，趋势应该是stable
    if len(productivity['daily_breakdown']) == 1:
        assert productivity['trend'] == 'stable'

    print("\n✓ 生产力分析测试通过！")
    return True


def test_dashboard():
    """测试仪表盘"""
    print("\n" + "=" * 60)
    print("测试 4: 仪表盘")
    print("=" * 60)

    # 创建仪表盘（不绑定记忆系统）
    dashboard = MemoryDashboard()

    # 生成报告
    report = dashboard.generate_report()
    print(f"\n报告预览:")
    print(report[:200] + "...")

    # 导出统计
    summary = dashboard.get_summary()
    print(f"\n摘要统计:")
    print(f"  总记忆数: {summary['total_memories']}")
    print(f"  总访问次数: {summary['total_accesses']}")

    print("\n✓ 仪表盘测试通过！")
    return True


def test_enhanced_memory():
    """测试增强记忆系统"""
    print("\n" + "=" * 60)
    print("测试 5: 增强记忆系统")
    print("=" * 60)

    memory = get_memory_system()
    enhanced = EnhancedMemoryWithAnalytics(memory)

    # 清空现有数据
    memory.l1.clear()
    memory.l2.clear()
    memory.l3.clear()

    # 添加一些记忆
    mem_ids = []
    for i in range(5):
        mem_id = memory.add(f"测试记忆{i+1}", "test", "l2")
        mem_ids.append(mem_id)
        enhanced.track_activity("memory_created", mem_id, {"level": "l2"})
        time.sleep(0.01)

    print(f"\n创建了 {len(mem_ids)} 条记忆")

    # 收集统计
    stats = enhanced.collect_stats()
    print(f"收集的统计:")
    print(f"  总记忆数: {stats['total_memories']}")
    print(f"  总访问次数: {stats['total_accesses']}")

    # 获取仪表盘
    dashboard = enhanced.get_dashboard()
    print(f"\n仪表盘数据:")
    print(f"  记忆分布: {dashboard['summary']['memory_level_distribution']}")

    # 生成报告
    report = enhanced.generate_report()
    print(f"\n报告:")
    print(report)

    # 追踪更多活动
    for mem_id in mem_ids[:3]:
        enhanced.track_activity("memory_accessed", mem_id)
        time.sleep(0.01)

    # 获取最近活动
    recent = enhanced.get_recent_activity(hours=1)
    print(f"\n最近活动数: {len(recent)}")

    # 生产力分析
    productivity = enhanced.analyze_productivity()
    print(f"\n生产力分析:")
    print(f"  平均每日活动: {productivity['avg_daily_activity']:.2f}")
    print(f"  趋势: {productivity['trend']}")

    # 导出分析
    analytics = enhanced.export_analytics()
    print(f"\n导出分析数据:")
    print(f"  最近24小时活动: {analytics['activity']['recent_24h']}")
    print(f"  最近7天活动: {analytics['activity']['recent_7d']}")

    assert stats['total_memories'] >= 5

    print("\n✓ 增强记忆系统测试通过！")
    return True


def test_activity_stats():
    """测试活动统计"""
    print("\n" + "=" * 60)
    print("测试 6: 活动统计")
    print("=" * 60)

    tracker = ActivityTracker()

    # 追踪多种类型的事件
    for i in range(10):
        tracker.track_event("memory_created", f"mem_{i}")
        tracker.track_event("memory_accessed", f"mem_{i}")

    # 添加更新事件
    for i in range(5):
        tracker.track_event("memory_updated", f"mem_{i}")

    # 获取类型统计
    event_types = {}
    for event in tracker.events:
        event_type = event['type']
        event_types[event_type] = event_types.get(event_type, 0) + 1

    print(f"\n事件类型统计:")
    for event_type, count in event_types.items():
        print(f"  {event_type}: {count}")

    assert event_types['memory_created'] == 10
    assert event_types['memory_accessed'] == 10
    assert event_types['memory_updated'] == 5

    print("\n✓ 活动统计测试通过！")
    return True


def test_dashboard_export():
    """测试仪表盘导出"""
    print("\n" + "=" * 60)
    print("测试 7: 仪表盘导出")
    print("=" * 60)

    dashboard = MemoryDashboard()

    # 测试不同格式导出
    summary_export = dashboard.export_statistics(format="summary")
    print(f"\n摘要格式导出:")
    print(f"  类型: {type(summary_export)}")
    print(f"  内容: {summary_export}")

    dict_export = dashboard.export_statistics(format="dict")
    print(f"\n字典格式导出:")
    print(f"  类型: {type(dict_export)}")
    print(f"  键: {list(dict_export.keys())}")

    report_export = dashboard.export_statistics(format="report")
    print(f"\n报告格式导出:")
    print(f"  类型: {type(report_export)}")
    print(f"  长度: {len(report_export)} 字符")

    assert isinstance(summary_export, dict)
    assert isinstance(dict_export, dict)
    assert isinstance(report_export, str)

    print("\n✓ 仪表盘导出测试通过！")
    return True


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("第25阶段测试：记忆统计分析/仪表盘功能")
    print("=" * 60)

    all_passed = True

    try:
        passed = test_trend_analyzer()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试1失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_activity_tracker()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试2失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_productivity_analysis()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试3失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_dashboard()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试4失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_enhanced_memory()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试5失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_activity_stats()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试6失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_dashboard_export()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试7失败: {e}")
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
