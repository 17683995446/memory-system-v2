#!/usr/bin/env python3
"""
第51阶段演示：性能监控与分析系统
"""

import time
from src.performance import (
    PerformanceMonitor,
    PerformanceAnalyzer,
    PerformanceReportGenerator,
    PerformanceMetricType
)


def main():
    """主函数"""
    print("=" * 70)
    print("第51阶段演示：性能监控与分析系统")
    print("=" * 70)
    
    # 创建性能监控器
    monitor = PerformanceMonitor()
    print("\n1. 创建性能监控器")
    
    # 创建性能阈值
    print("\n2. 创建性能阈值")
    monitor.create_threshold(
        metric_type=PerformanceMetricType.CPU_USAGE,
        warning_threshold=70.0,
        critical_threshold=85.0,
        unit="%"
    )
    print("   ✓ 创建了CPU使用率阈值 (警告: 70%, 严重: 85%)")
    
    # 获取性能快照
    print("\n3. 获取系统性能快照")
    snapshot_id = monitor.take_snapshot()
    print(f"   ✓ 获取快照: {snapshot_id}")
    
    snapshot = monitor.snapshots[-1]
    print(f"   - CPU: {snapshot.cpu_percent:.2f}%")
    print(f"   - 内存: {snapshot.memory_percent:.2f}%")
    print(f"   - 线程: {snapshot.thread_count}")
    print(f"   - 连接: {snapshot.active_connections}")
    
    # 记录性能指标
    print("\n4. 记录性能指标")
    monitor.record_response_time("query_users", 125.5, success=True)
    monitor.record_response_time("query_items", 89.2, success=True)
    monitor.record_response_time("save_data", 234.1, success=False)
    
    monitor.record_throughput("api", 1000, 10.0)
    monitor.record_throughput("batch", 5000, 30.0)
    
    monitor.record_latency("/api/users", 45.2)
    monitor.record_latency("/api/items", 52.8)
    print("   ✓ 记录了响应时间、吞吐量和延迟指标")
    
    # 设置性能基线
    print("\n5. 设置性能基线")
    baseline = monitor.set_baseline()
    print(f"   ✓ 基线已设置:")
    print(f"   - CPU: {baseline['cpu_percent']:.2f}%")
    print(f"   - 内存: {baseline['memory_percent']:.2f}%")
    print(f"   - 线程: {baseline['thread_count']}")
    
    # 再次获取快照进行对比
    print("\n6. 与基线对比")
    monitor.take_snapshot()
    comparison = monitor.compare_to_baseline()
    print(f"   ✓ CPU变化: {comparison['cpu_diff']:+.2f}%")
    print(f"   ✓ 内存变化: {comparison['memory_diff']:+.2f}%")
    print(f"   ✓ 线程变化: {comparison['thread_diff']:+.0f}")
    
    # 获取性能摘要
    print("\n7. 获取性能摘要")
    summary = monitor.get_performance_summary()
    print(f"   ✓ 总体健康度: {summary['metrics_count']} 个指标已分析")
    print(f"   ✓ 活跃告警: {summary['active_alerts']}")
    print(f"   - 当前CPU: {summary['latest']['cpu_percent']:.2f}%")
    print(f"   - 当前内存: {summary['latest']['memory_percent']:.2f}%")
    
    # 创建性能分析器
    print("\n8. 进行性能分析")
    analyzer = PerformanceAnalyzer(monitor)
    analysis = analyzer.analyze_current_performance()
    print(f"   ✓ 总体健康度: {analysis.overall_health.upper()}")
    print(f"   ✓ 分析指标数: {analysis.metrics_analyzed}")
    print(f"   ✓ 触发告警数: {analysis.alerts_triggered}")
    
    if analysis.trends:
        print("\n   性能趋势:")
        for trend in analysis.trends:
            print(f"   - {trend.metric_name}: {trend.trend} ({trend.change_percent:+.1f}%)")
    
    if analysis.recommendations:
        print("\n   建议:")
        for rec in analysis.recommendations:
            print(f"   - {rec}")
    
    # 生成报告
    print("\n9. 生成性能报告")
    generator = PerformanceReportGenerator(monitor, analyzer)
    
    print("\n   [摘要报告]")
    print("-" * 70)
    summary_report = generator.generate_summary_report()
    print(summary_report)
    
    print("\n   [详细报告]")
    print("-" * 70)
    detailed_report = generator.generate_detailed_report()
    print(detailed_report)
    
    # 保存报告
    print("\n10. 保存报告")
    generator.save_report("summary")
    generator.save_report("detailed")
    history = generator.get_report_history()
    print(f"   ✓ 已保存 {len(history)} 份报告")
    
    # 生成JSON报告
    print("\n11. 生成JSON报告")
    json_report = generator.generate_json_report()
    print("   ✓ JSON报告已生成")
    print(f"   - 报告长度: {len(json_report)} 字符")
    
    # 获取活跃告警
    print("\n12. 检查活跃告警")
    active_alerts = monitor.get_active_alerts()
    if active_alerts:
        print(f"   ✓ 发现 {len(active_alerts)} 个活跃告警:")
        for alert in active_alerts:
            print(f"   - [{alert.severity.upper()}] {alert.metric_name}: {alert.message}")
        
        print("\n   解决告警...")
        for alert in active_alerts:
            monitor.resolve_alert(alert.alert_id)
            print(f"   ✓ 已解决: {alert.metric_name}")
    
    print("\n" + "=" * 70)
    print("✅ 第51阶段演示完成！")
    print("=" * 70)


if __name__ == "__main__":
    main()
