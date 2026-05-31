#!/usr/bin/env python3
"""
第51阶段测试：性能监控与分析系统
测试性能监控、性能分析和报告生成功能
"""

import sys
import time
import unittest
from datetime import datetime
from src.performance import (
    PerformanceMonitor,
    PerformanceAnalyzer,
    PerformanceReportGenerator,
    get_performance_monitor,
    PerformanceMetricType,
    PerformanceStatus
)


class TestPerformanceMonitor(unittest.TestCase):
    """性能监控器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.monitor = PerformanceMonitor()
    
    def test_create_metric(self):
        """测试创建性能指标"""
        metric_id = self.monitor.create_metric(
            name="test_cpu",
            metric_type=PerformanceMetricType.CPU_USAGE,
            value=45.5,
            unit="%"
        )
        
        self.assertIsNotNone(metric_id)
        self.assertTrue(metric_id.startswith("PERF-METRIC-"))
        self.assertIn("test_cpu", self.monitor.metrics)
    
    def test_record_response_time(self):
        """测试记录响应时间"""
        metric_id = self.monitor.record_response_time(
            operation="test_op",
            duration=125.5,
            success=True
        )
        
        self.assertIsNotNone(metric_id)
        self.assertTrue(metric_id.startswith("PERF-METRIC-"))
        
        metric = self.monitor.get_metric("response_time_test_op")
        self.assertIsNotNone(metric)
        self.assertEqual(metric.value, 125.5)
        self.assertEqual(metric.unit, "ms")
    
    def test_record_throughput(self):
        """测试记录吞吐量"""
        metric_id = self.monitor.record_throughput(
            operation="api",
            count=1000,
            duration=10.0
        )
        
        self.assertIsNotNone(metric_id)
        
        metric = self.monitor.get_metric("throughput_api")
        self.assertIsNotNone(metric)
        self.assertEqual(metric.value, 100.0)
    
    def test_record_latency(self):
        """测试记录延迟"""
        metric_id = self.monitor.record_latency(
            endpoint="/api/users",
            latency=50.2
        )
        
        self.assertIsNotNone(metric_id)
        
        metric = self.monitor.get_metric("latency_/api/users")
        self.assertIsNotNone(metric)
        self.assertEqual(metric.value, 50.2)
    
    def test_take_snapshot(self):
        """测试获取性能快照"""
        snapshot_id = self.monitor.take_snapshot()
        
        self.assertIsNotNone(snapshot_id)
        self.assertTrue(snapshot_id.startswith("SNAPSHOT-"))
        self.assertTrue(len(self.monitor.snapshots) > 0)
        
        snapshot = self.monitor.snapshots[-1]
        self.assertIsNotNone(snapshot.cpu_percent)
        self.assertIsNotNone(snapshot.memory_percent)
    
    def test_create_threshold(self):
        """测试创建性能阈值"""
        threshold_id = self.monitor.create_threshold(
            metric_type=PerformanceMetricType.CPU_USAGE,
            warning_threshold=70.0,
            critical_threshold=85.0,
            unit="%"
        )
        
        self.assertIsNotNone(threshold_id)
        self.assertTrue(threshold_id.startswith("THRESHOLD-"))
        self.assertIn(threshold_id, self.monitor.thresholds)
    
    def test_get_metrics_by_type(self):
        """测试按类型获取指标"""
        self.monitor.create_metric(
            name="metric1",
            metric_type=PerformanceMetricType.CPU_USAGE,
            value=50.0,
            unit="%"
        )
        self.monitor.create_metric(
            name="metric2",
            metric_type=PerformanceMetricType.MEMORY_USAGE,
            value=60.0,
            unit="%"
        )
        self.monitor.create_metric(
            name="metric3",
            metric_type=PerformanceMetricType.CPU_USAGE,
            value=55.0,
            unit="%"
        )
        
        cpu_metrics = self.monitor.get_metrics_by_type(PerformanceMetricType.CPU_USAGE)
        self.assertEqual(len(cpu_metrics), 2)
    
    def test_get_active_alerts(self):
        """测试获取活跃告警"""
        self.monitor.create_threshold(
            metric_type=PerformanceMetricType.CPU_USAGE,
            warning_threshold=50.0,
            critical_threshold=80.0,
            unit="%"
        )
        
        self.monitor.create_metric(
            name="high_cpu",
            metric_type=PerformanceMetricType.CPU_USAGE,
            value=85.0,
            unit="%"
        )
        
        active_alerts = self.monitor.get_active_alerts()
        self.assertTrue(len(active_alerts) > 0)
    
    def test_resolve_alert(self):
        """测试解决告警"""
        self.monitor.create_threshold(
            metric_type=PerformanceMetricType.MEMORY_USAGE,
            warning_threshold=50.0,
            critical_threshold=80.0,
            unit="%"
        )
        
        self.monitor.create_metric(
            name="high_memory",
            metric_type=PerformanceMetricType.MEMORY_USAGE,
            value=90.0,
            unit="%"
        )
        
        active_alerts = self.monitor.get_active_alerts()
        if active_alerts:
            alert_id = active_alerts[0].alert_id
            result = self.monitor.resolve_alert(alert_id)
            self.assertTrue(result)
    
    def test_get_performance_summary(self):
        """测试获取性能摘要"""
        self.monitor.take_snapshot()
        
        summary = self.monitor.get_performance_summary()
        
        self.assertIsNotNone(summary)
        self.assertIn("timestamp", summary)
        self.assertIn("latest", summary)
        self.assertIn("average_10", summary)
        self.assertIn("metrics_count", summary)
    
    def test_baseline(self):
        """测试性能基线"""
        baseline = self.monitor.set_baseline()
        
        self.assertIsNotNone(baseline)
        self.assertIn("cpu_percent", baseline)
        self.assertIn("memory_percent", baseline)
        self.assertIn("thread_count", baseline)
        
        comparison = self.monitor.compare_to_baseline()
        self.assertIn("cpu_diff", comparison)
        self.assertIn("memory_diff", comparison)


class TestPerformanceAnalyzer(unittest.TestCase):
    """性能分析器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.monitor = PerformanceMonitor()
        self.analyzer = PerformanceAnalyzer(self.monitor)
    
    def test_analyze_current_performance(self):
        """测试分析当前性能"""
        self.monitor.take_snapshot()
        
        analysis = self.analyzer.analyze_current_performance()
        
        self.assertIsNotNone(analysis)
        self.assertIn("overall_health", dir(analysis))
        self.assertIsNotNone(analysis.overall_health)
        self.assertIsNotNone(analysis.recommendations)
    
    def test_generate_performance_report(self):
        """测试生成性能报告"""
        self.monitor.take_snapshot()
        
        report = self.analyzer.generate_performance_report()
        
        self.assertIsNotNone(report)
        self.assertIn("性能分析报告", report)
        self.assertIn("总体健康度", report)


class TestPerformanceReportGenerator(unittest.TestCase):
    """性能报告生成器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.monitor = PerformanceMonitor()
        self.analyzer = PerformanceAnalyzer(self.monitor)
        self.generator = PerformanceReportGenerator(self.monitor, self.analyzer)
    
    def test_generate_summary_report(self):
        """测试生成摘要报告"""
        self.monitor.take_snapshot()
        
        report = self.generator.generate_summary_report()
        
        self.assertIsNotNone(report)
        self.assertIn("性能摘要报告", report)
        self.assertIn("总体健康度", report)
    
    def test_generate_detailed_report(self):
        """测试生成详细报告"""
        self.monitor.take_snapshot()
        
        report = self.generator.generate_detailed_report()
        
        self.assertIsNotNone(report)
        self.assertIn("详细性能报告", report)
        self.assertIn("建议", report)
    
    def test_generate_json_report(self):
        """测试生成JSON报告"""
        self.monitor.take_snapshot()
        
        report = self.generator.generate_json_report()
        
        self.assertIsNotNone(report)
        self.assertIn("overall_health", report)
        self.assertIn("metrics_count", report)
    
    def test_save_report(self):
        """测试保存报告"""
        self.monitor.take_snapshot()
        
        report = self.generator.save_report("summary")
        
        self.assertIsNotNone(report)
        self.assertTrue(len(self.generator.get_report_history()) > 0)


class TestGlobalMonitor(unittest.TestCase):
    """全局监控器测试"""
    
    def test_get_performance_monitor(self):
        """测试获取全局监控器"""
        monitor1 = get_performance_monitor()
        monitor2 = get_performance_monitor()
        
        self.assertIs(monitor1, monitor2)


def run_tests():
    """运行测试"""
    print("=" * 70)
    print("第51阶段测试：性能监控与分析系统")
    print("=" * 70)
    
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    
    test_suite.addTests(test_loader.loadTestsFromTestCase(TestPerformanceMonitor))
    test_suite.addTests(test_loader.loadTestsFromTestCase(TestPerformanceAnalyzer))
    test_suite.addTests(test_loader.loadTestsFromTestCase(TestPerformanceReportGenerator))
    test_suite.addTests(test_loader.loadTestsFromTestCase(TestGlobalMonitor))
    
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    print("\n" + "=" * 70)
    if result.wasSuccessful():
        print("✅ 所有测试通过！")
    else:
        print("❌ 部分测试失败！")
    print("=" * 70)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
