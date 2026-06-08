#!/usr/bin/env python3
"""
可观测性测试 - 验证Prometheus导出、告警规则、分布式追踪
"""

import sys
import time
sys.path.insert(0, '/workspace')

from src.monitoring.observability import (
    get_observability, PrometheusExporter, AlertRule, AutoAlertEngine,
    Tracer, ObservabilitySystem, SLOStatus
)


def test_prometheus_exporter():
    """测试Prometheus格式导出"""
    print("[Observability] 测试Prometheus导出...")
    obs = ObservabilitySystem()

    # 记录一些指标
    obs.record_counter("memory_add_total", 100, {"level": "l2"})
    obs.record_counter("memory_add_total", 50, {"level": "l3"})
    obs.record_gauge("memory_size", 1024.0, {"level": "l1"})
    obs.record_latency("memory_recall", 150.0, {"level": "l2"})
    obs.record_latency("memory_recall", 200.0, {"level": "l2"})

    # 获取Prometheus格式
    metrics = obs.get_prometheus_metrics()

    assert "memory_add_total" in metrics
    assert "memory_size" in metrics
    assert "memory_recall_duration_seconds_bucket" in metrics
    assert "# TYPE memory_add_total counter" in metrics
    assert "# TYPE memory_size gauge" in metrics
    assert "# TYPE memory_recall_duration_seconds histogram" in metrics

    print("[Observability] Prometheus导出通过")
    return True


def test_alert_rules():
    """测试告警规则"""
    print("[Observability] 测试告警规则...")
    engine = AutoAlertEngine()

    # 测试内存使用过高告警
    alerts = engine.evaluate_all({
        "l1_size": 50000,
        "l2_size": 40000,
        "l3_size": 20000,
        "failure_rate": 0.01,
        "avg_response_time_ms": 1000
    })
    # 总数 110000 > 100000，应该触发
    assert len(alerts) >= 1
    assert any(a["rule"] == "memory_usage_high" for a in alerts)

    # 测试失败率告警
    alerts = engine.evaluate_all({
        "l1_size": 100,
        "l2_size": 100,
        "l3_size": 100,
        "failure_rate": 0.1,
        "avg_response_time_ms": 1000
    })
    assert any(a["rule"] == "operation_failure_rate_high" for a in alerts)

    # 测试响应时间告警
    alerts = engine.evaluate_all({
        "l1_size": 100,
        "l2_size": 100,
        "l3_size": 100,
        "failure_rate": 0.01,
        "avg_response_time_ms": 6000
    })
    assert any(a["rule"] == "response_time_high" for a in alerts)

    # 测试冷却期
    alerts2 = engine.evaluate_all({
        "l1_size": 50000,
        "l2_size": 40000,
        "l3_size": 20000,
        "failure_rate": 0.01,
        "avg_response_time_ms": 1000
    })
    # 冷却期内不应重复触发
    assert len(alerts2) == 0

    print("[Observability] 告警规则通过")
    return True


def test_tracer():
    """测试分布式追踪"""
    print("[Observability] 测试分布式追踪...")
    tracer = Tracer()

    # 开始追踪
    span1 = tracer.start_span("trace-1", "memory.add")
    time.sleep(0.01)
    span2 = tracer.start_span("trace-1", "embedding.encode", parent_id=span1.span_id)
    time.sleep(0.01)
    span2.finish()
    span1.finish()

    # 获取追踪数据
    trace = tracer.get_trace("trace-1")
    assert len(trace) == 2
    assert trace[0]["operation"] == "memory.add"
    assert trace[1]["operation"] == "embedding.encode"
    assert trace[0]["duration_ms"] > 0
    assert trace[1]["duration_ms"] > 0

    print("[Observability] 分布式追踪通过")
    return True


def test_sli_tracking():
    """测试SLI追踪"""
    print("[Observability] 测试SLI追踪...")
    obs = ObservabilitySystem()

    # 记录SLI - 响应时间（越小越好）
    status = obs.record_sli("recall_latency_ms", 100.0, 500.0, 'lt')
    assert status == SLOStatus.HEALTHY

    status = obs.record_sli("recall_latency_ms", 450.0, 500.0, 'lt')
    assert status == SLOStatus.WARNING

    status = obs.record_sli("recall_latency_ms", 600.0, 500.0, 'lt')
    assert status == SLOStatus.BREACH

    # 记录SLI - 成功率（越大越好）
    status = obs.record_sli("success_rate", 0.99, 0.95, 'gt')
    # 0.99 >= 0.95*1.2=1.14 不成立，但 >=0.95，所以是WARNING
    assert status == SLOStatus.WARNING

    status = obs.record_sli("success_rate", 0.90, 0.95, 'gt')
    assert status == SLOStatus.BREACH

    # 获取SLO报告
    report = obs.get_slo_report()
    assert report["summary"]["total"] >= 5
    assert report["summary"]["warning"] >= 2
    assert report["summary"]["breach"] >= 2

    # 健康评分
    score = obs.get_health_score()
    assert 0 <= score <= 100

    print("[Observability] SLI追踪通过")
    return True


def test_observability_singleton():
    """测试可观测性单例"""
    print("[Observability] 测试单例...")
    obs1 = get_observability()
    obs2 = get_observability()
    assert obs1 is obs2
    print("[Observability] 单例通过")
    return True


def run_all_observability_tests():
    """运行所有可观测性测试"""
    print("=" * 80)
    print("可观测性测试开始")
    print("=" * 80)

    tests = [
        test_prometheus_exporter,
        test_alert_rules,
        test_tracer,
        test_sli_tracking,
        test_observability_singleton,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            failed += 1
            print(f"[Observability] 测试失败: {test.__name__}: {e}")

    print("\n" + "=" * 80)
    print(f"可观测性测试完成: 通过={passed}, 失败={failed}")
    print("=" * 80)

    return failed == 0


if __name__ == "__main__":
    success = run_all_observability_tests()
    sys.exit(0 if success else 1)
