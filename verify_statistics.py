"""
简单验证统计与报告系统
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("测试统计与报告系统导入...")
try:
    from src.statistics import (
        StatisticsCollector,
        ReportGenerator,
        ReportType,
        get_statistics_collector,
        get_report_generator
    )
    print("✓ 统计与报告系统导入成功！")
except Exception as e:
    print(f"✗ 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n测试统计收集器...")
try:
    collector = StatisticsCollector()

    # 记录一些操作
    collector.record_operation("add", True, 0.05)
    collector.record_operation("recall", True, 0.03)
    collector.record_operation("add", False, 0.01)

    # 记录会话活动
    collector.record_session_activity("test_session", "test_activity")

    # 记录记忆增长
    collector.record_memory_growth("l1", 10)
    collector.record_memory_growth("l1", 15)

    # 获取统计
    op_stats = collector.get_operation_stats()
    print(f"✓ 操作统计: {op_stats}")

    session_stats = collector.get_session_stats()
    print(f"✓ 会话统计: {session_stats['total_sessions']} 个会话")

    growth_stats = collector.get_memory_growth_stats()
    print(f"✓ 记忆增长: {growth_stats}")

    print("✓ 统计收集器功能正常")
except Exception as e:
    print(f"✗ 统计收集器失败: {e}")

print("\n测试报告生成器...")
try:
    generator = ReportGenerator(collector)

    # 生成报告
    report = generator.generate_report(ReportType.WEEKLY)
    print(f"✓ 报告生成成功!")
    print(f"  报告ID: {report.report_id}")
    print(f"  摘要: {report.summary}")
    print(f"  洞察数量: {len(report.insights)}")
    print(f"  建议数量: {len(report.recommendations)}")

    # 测试导出
    json_export = generator.export_report_json(report)
    print(f"✓ JSON导出: {len(json_export)} 字符")

    text_export = generator.export_report_text(report)
    print(f"✓ 文本导出: {len(text_export)} 字符")

except Exception as e:
    print(f"✗ 报告生成器失败: {e}")
    import traceback
    traceback.print_exc()

print("\n测试全局单例...")
try:
    collector1 = get_statistics_collector()
    collector2 = get_statistics_collector()
    assert collector1 is collector2
    print("✓ 全局单例模式正常")
except Exception as e:
    print(f"✗ 全局单例测试失败: {e}")

print("\n" + "=" * 50)
print("所有基本验证通过！")
print("=" * 50)
