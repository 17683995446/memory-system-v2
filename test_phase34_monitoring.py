"""
第34阶段测试：记忆系统监控与诊断
遵循"图难于其易，为大于其细"原则
"""

import os
import sys
import time
import tempfile
import shutil

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.monitoring import (
    MetricsCollector,
    AlertManager,
    MemorySystemMonitor,
    MetricType,
    AlertLevel,
    get_monitor
)
from src.memory import get_memory_system


def test_metrics_collector():
    """测试指标收集器"""
    print("\n=== 测试指标收集器 ===")

    collector = MetricsCollector()

    # 测试计数器
    collector.increment("test_counter", 1)
    collector.increment("test_counter", 2)
    assert collector.get_counter("test_counter") == 3
    print("✓ 计数器功能正常")

    # 测试仪表盘
    collector.set_gauge("test_gauge", 10.5)
    collector.set_gauge("test_gauge", 15.3)
    assert collector.get_gauge("test_gauge") == 15.3
    print("✓ 仪表盘功能正常")

    # 测试直方图
    collector.record_histogram("test_histogram", 1.0)
    collector.record_histogram("test_histogram", 2.0)
    collector.record_histogram("test_histogram", 3.0)
    stats = collector.get_histogram_stats("test_histogram")
    assert stats["count"] == 3
    assert stats["avg"] == 2.0
    print("✓ 直方图功能正常")

    # 测试计时器
    collector.start_timer("test_timer")
    time.sleep(0.01)
    elapsed = collector.stop_timer("test_timer")
    assert elapsed > 0
    timer_stats = collector.get_timer_stats("test_timer")
    assert timer_stats["count"] == 1
    print("✓ 计时器功能正常")

    # 测试装饰器
    @collector.timeit("decorated_function")
    def test_func():
        time.sleep(0.005)
        return "done"

    result = test_func()
    assert result == "done"
    assert collector.get_timer_stats("decorated_function")["count"] == 1
    print("✓ 计时器装饰器功能正常")

    # 测试获取所有指标
    all_metrics = collector.get_all_metrics()
    assert "counters" in all_metrics
    assert "gauges" in all_metrics
    assert "histograms" in all_metrics
    assert "timers" in all_metrics
    print("✓ 获取所有指标功能正常")

    # 测试重置
    collector.reset("test_counter")
    assert collector.get_counter("test_counter") is None
    collector.reset()
    assert len(collector.get_all_metrics()["counters"]) == 0
    print("✓ 重置功能正常")

    print("✓ 指标收集器测试通过")


def test_alert_manager():
    """测试告警管理器"""
    print("\n=== 测试告警管理器 ===")

    manager = AlertManager()

    # 测试创建告警
    alert_id = manager.alert(
        AlertLevel.WARNING,
        "Test warning message",
        source="test"
    )
    assert alert_id is not None
    print("✓ 告警创建功能正常")

    # 测试获取活跃告警
    active_alerts = manager.get_active_alerts()
    assert len(active_alerts) == 1
    assert active_alerts[0].message == "Test warning message"
    print("✓ 获取活跃告警功能正常")

    # 测试解决告警
    resolved = manager.resolve(alert_id)
    assert resolved is True
    active_alerts = manager.get_active_alerts()
    assert len(active_alerts) == 0
    print("✓ 告警解决功能正常")

    # 测试告警历史
    history = manager.get_alert_history()
    assert len(history) >= 1
    print("✓ 告警历史功能正常")

    # 测试不同级别的告警
    info_id = manager.alert(AlertLevel.INFO, "Info message")
    error_id = manager.alert(AlertLevel.ERROR, "Error message")
    critical_id = manager.alert(AlertLevel.CRITICAL, "Critical message")

    active = manager.get_active_alerts()
    assert len(active) == 3
    print("✓ 不同级别告警功能正常")

    # 测试告警监听器
    listener_called = False
    def test_listener(alert):
        nonlocal listener_called
        listener_called = True

    manager.add_listener(test_listener)
    manager.alert(AlertLevel.INFO, "Listener test")
    assert listener_called is True
    print("✓ 告警监听器功能正常")

    print("✓ 告警管理器测试通过")


def test_memory_system_monitor():
    """测试记忆系统监控器"""
    print("\n=== 测试记忆系统监控器 ===")

    # 创建记忆系统
    memory_system = get_memory_system()

    # 创建监控器
    monitor = MemorySystemMonitor(memory_system)

    # 添加一些测试数据
    memory_system.add("Test memory 1", "session_1")
    memory_system.add("Test memory 2", "session_1")
    memory_system.add_fact("Test", "key", "value", "test")

    # 测试健康检查
    health = monitor.run_health_checks()
    assert "overall" in health
    assert "memory_sizes" in health
    print("✓ 健康检查功能正常")

    # 测试获取状态
    status = monitor.get_status()
    assert "timestamp" in status
    assert "metrics" in status
    assert "alerts" in status
    assert "health" in status
    print("✓ 获取状态功能正常")

    # 测试记录记忆操作
    monitor.record_memory_operation("add", True)
    monitor.record_memory_operation("query", True)
    monitor.record_memory_operation("delete", False)

    metrics = monitor.metrics.get_all_metrics()
    assert "memory_operations_total" in metrics["counters"]
    print("✓ 记忆操作记录功能正常")

    # 测试记录查询延迟
    monitor.record_query_latency(0.05, "recall")
    monitor.record_query_latency(0.10, "search")
    monitor.record_query_latency(0.03, "recall")

    latency_stats = monitor.metrics.get_histogram_stats("query_latency_seconds")
    assert latency_stats["count"] == 3
    print("✓ 查询延迟记录功能正常")

    # 测试告警集成
    alert_id = monitor.alerts.alert(
        AlertLevel.WARNING,
        "High memory usage detected",
        source="monitor"
    )
    assert alert_id is not None
    print("✓ 告警集成功能正常")

    print("✓ 记忆系统监控器测试通过")


def test_global_monitor():
    """测试全局监控器"""
    print("\n=== 测试全局监控器 ===")

    memory_system = get_memory_system()

    # 获取全局监控器
    monitor1 = get_monitor(memory_system)
    monitor2 = get_monitor()

    # 验证是同一个实例
    assert monitor1 is monitor2
    print("✓ 全局监控器单例模式正常")

    # 验证记忆系统已设置
    assert monitor1.memory_system is not None
    print("✓ 记忆系统关联正常")

    print("✓ 全局监控器测试通过")


def test_integration():
    """测试完整集成"""
    print("\n=== 测试完整集成 ===")

    # 创建记忆系统和监控器
    memory_system = get_memory_system()
    monitor = get_monitor(memory_system)

    # 模拟一些操作
    operations = [
        ("add", lambda: memory_system.add("Integrated test", "session_int")),
        ("recall", lambda: memory_system.recall("test", "session_int")),
        ("add_fact", lambda: memory_system.add_fact("Int", "test", "data", "test"))
    ]

    for op_name, op_func in operations:
        start = time.time()
        try:
            result = op_func()
            monitor.record_memory_operation(op_name, True)
        except Exception:
            monitor.record_memory_operation(op_name, False)
        latency = time.time() - start
        monitor.record_query_latency(latency, op_name)

    # 检查指标
    metrics = monitor.metrics.get_all_metrics()
    assert "memory_operations_total" in metrics["counters"]
    assert "query_latency_seconds" in metrics["histograms"]
    print("✓ 操作指标记录正常")

    # 运行健康检查
    health = monitor.run_health_checks()
    assert health["overall"]["status"] in ["healthy", "degraded", "unhealthy"]
    print("✓ 健康检查运行正常")

    # 获取完整状态
    status = monitor.get_status()
    print(f"✓ 完整状态获取正常: {status['health']['overall']['status']}")

    print("✓ 完整集成测试通过")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("第34阶段测试：记忆系统监控与诊断")
    print("遵循原则：图难于其易，为大于其细")
    print("=" * 60)

    try:
        test_metrics_collector()
        test_alert_manager()
        test_memory_system_monitor()
        test_global_monitor()
        test_integration()

        print("\n" + "=" * 60)
        print("✓ 所有第34阶段测试通过！")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
