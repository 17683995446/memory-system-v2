#!/usr/bin/env python3
"""
第50阶段演示：运维监控和告警系统
"""

from src.monitoring import (
    MetricsCollector,
    get_metrics_collector,
    MetricType,
    NotificationChannelType
)


def main():
    """主函数"""
    print("=" * 70)
    print("第50阶段演示：运维监控和告警系统")
    print("=" * 70)
    
    # 创建监控收集器
    collector = MetricsCollector()
    print("\n1. 创建监控收集器")
    
    # 创建指标
    print("\n2. 创建监控指标")
    collector.create_metric(
        name="cpu_usage",
        metric_type=MetricType.GAUGE,
        help_text="CPU使用率",
        unit="%"
    )
    
    collector.create_metric(
        name="memory_usage",
        metric_type=MetricType.GAUGE,
        help_text="内存使用率",
        unit="%"
    )
    
    collector.create_metric(
        name="request_count",
        metric_type=MetricType.COUNTER,
        help_text="请求计数",
        unit="count"
    )
    print("   ✓ 创建了3个监控指标")
    
    # 创建告警规则
    print("\n3. 创建告警规则")
    collector.create_alert_rule(
        name="CPU使用率过高",
        metric_name="cpu_usage",
        condition=">",
        threshold=80.0,
        severity="warning"
    )
    
    collector.create_alert_rule(
        name="内存使用率过高",
        metric_name="memory_usage",
        condition=">",
        threshold=85.0,
        severity="error"
    )
    print("   ✓ 创建了2个告警规则")
    
    # 创建通知渠道
    print("\n4. 创建通知渠道")
    collector.create_notification_channel(
        name="控制台通知",
        channel_type=NotificationChannelType.CONSOLE
    )
    print("   ✓ 创建了控制台通知渠道")
    
    # 创建SLO
    print("\n5. 创建服务水平目标")
    collector.create_slo(
        name="API可用性",
        description="API服务可用性目标",
        target=99.9,
        period_days=30
    )
    print("   ✓ 创建了API可用性SLO")
    
    # 记录指标数据
    print("\n6. 记录监控指标数据")
    collector.record_metric("cpu_usage", 45.0)
    collector.record_metric("memory_usage", 60.0)
    collector.increment_counter("request_count")
    collector.increment_counter("request_count")
    print("   ✓ 记录了CPU、内存和请求计数")
    
    # 触发告警
    print("\n7. 模拟高负载，触发告警")
    print("   记录CPU使用率为85%...")
    collector.record_metric("cpu_usage", 85.0)
    
    # 创建事件
    print("\n8. 创建系统事件")
    collector.create_event(
        event_type="system",
        source="demo",
        message="系统启动",
        level="info"
    )
    print("   ✓ 创建了系统启动事件")
    
    # 生成报告
    print("\n9. 生成监控报告")
    report = collector.generate_report()
    print(report)
    
    # 解决告警
    print("\n10. 解决告警")
    active_alerts = collector.get_active_alerts()
    if active_alerts:
        alert_id = active_alerts[0].alert_id
        collector.resolve_alert(alert_id)
        print(f"   ✓ 解决了告警: {active_alerts[0].name}")
    
    # 创建全局收集器
    print("\n11. 测试全局收集器")
    global_collector = get_metrics_collector()
    global_collector.create_metric(
        name="disk_usage",
        metric_type=MetricType.GAUGE,
        help_text="磁盘使用率"
    )
    print("   ✓ 全局收集器创建成功")
    
    print("\n" + "=" * 70)
    print("✅ 第50阶段演示完成！")
    print("=" * 70)


if __name__ == "__main__":
    main()
