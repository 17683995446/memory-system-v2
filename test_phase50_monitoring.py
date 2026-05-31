#!/usr/bin/env python3
"""
第50阶段测试：运维监控和告警系统
测试监控指标收集、告警规则、通知渠道、事件管理等功能
"""

import sys
import time
import unittest
from datetime import datetime
from src.monitoring import (
    MetricsCollector,
    get_metrics_collector,
    MetricType,
    AlertRule,
    Alert,
    SLO,
    NotificationChannelType,
    Event
)


class TestMetricsCollector(unittest.TestCase):
    """监控指标收集器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.collector = MetricsCollector()
    
    def test_create_metric(self):
        """测试创建指标"""
        metric_id = self.collector.create_metric(
            name="test_counter",
            metric_type=MetricType.COUNTER,
            help_text="测试计数器",
            unit="count"
        )
        
        self.assertIsNotNone(metric_id)
        self.assertTrue(metric_id.startswith("METRIC-"))
        self.assertIn("test_counter", self.collector.metrics)
    
    def test_record_metric(self):
        """测试记录指标"""
        self.collector.create_metric(
            name="test_gauge",
            metric_type=MetricType.GAUGE,
            help_text="测试仪表盘"
        )
        
        result = self.collector.record_metric("test_gauge", 42.5)
        self.assertTrue(result)
        
        metric = self.collector.get_metric("test_gauge")
        self.assertEqual(len(metric.points), 1)
        self.assertEqual(metric.points[0].value, 42.5)
    
    def test_increment_counter(self):
        """测试增加计数器"""
        self.collector.create_metric(
            name="request_count",
            metric_type=MetricType.COUNTER
        )
        
        self.collector.increment_counter("request_count")
        self.collector.increment_counter("request_count", 2.0)
        
        metric = self.collector.get_metric("request_count")
        self.assertEqual(len(metric.points), 2)
        self.assertEqual(metric.points[1].value, 3.0)
    
    def test_get_metric_values(self):
        """测试获取指标数据点"""
        self.collector.create_metric(
            name="temperature",
            metric_type=MetricType.GAUGE
        )
        
        for i in range(5):
            self.collector.record_metric("temperature", 20.0 + i)
        
        values = self.collector.get_metric_values("temperature")
        self.assertEqual(len(values), 5)
        
        since = datetime.now()
        values_since = self.collector.get_metric_values("temperature", since)
        self.assertEqual(len(values_since), 0)


class TestAlertRule(unittest.TestCase):
    """告警规则测试"""
    
    def setUp(self):
        """测试前准备"""
        self.collector = MetricsCollector()
        self.collector.create_metric(
            name="cpu_usage",
            metric_type=MetricType.GAUGE,
            help_text="CPU使用率"
        )
    
    def test_create_alert_rule(self):
        """测试创建告警规则"""
        rule_id = self.collector.create_alert_rule(
            name="CPU使用率过高",
            metric_name="cpu_usage",
            condition=">",
            threshold=80.0,
            severity="warning",
            window=60
        )
        
        self.assertIsNotNone(rule_id)
        self.assertTrue(rule_id.startswith("ALERT-RULE-"))
        self.assertIn(rule_id, self.collector.alert_rules)
    
    def test_alert_firing(self):
        """测试告警触发"""
        self.collector.create_alert_rule(
            name="CPU使用率过高",
            metric_name="cpu_usage",
            condition=">",
            threshold=80.0,
            severity="warning"
        )
        
        self.collector.record_metric("cpu_usage", 85.0)
        
        active_alerts = self.collector.get_active_alerts()
        self.assertEqual(len(active_alerts), 1)
        self.assertEqual(active_alerts[0].name, "CPU使用率过高")
        self.assertEqual(active_alerts[0].current_value, 85.0)
    
    def test_alert_acknowledge(self):
        """测试告警确认"""
        self.collector.create_alert_rule(
            name="磁盘空间不足",
            metric_name="disk_usage",
            condition=">",
            threshold=90.0,
            severity="critical"
        )
        self.collector.create_metric("disk_usage", MetricType.GAUGE)
        self.collector.record_metric("disk_usage", 95.0)
        
        active_alerts = self.collector.get_active_alerts()
        alert_id = active_alerts[0].alert_id
        
        result = self.collector.acknowledge_alert(alert_id)
        self.assertTrue(result)
        
        alert = self.collector.alerts[alert_id]
        self.assertTrue(alert.acknowledged)
    
    def test_alert_resolve(self):
        """测试告警解决"""
        self.collector.create_alert_rule(
            name="内存使用率过高",
            metric_name="memory_usage",
            condition=">",
            threshold=85.0,
            severity="error"
        )
        self.collector.create_metric("memory_usage", MetricType.GAUGE)
        self.collector.record_metric("memory_usage", 90.0)
        
        active_alerts = self.collector.get_active_alerts()
        alert_id = active_alerts[0].alert_id
        
        result = self.collector.resolve_alert(alert_id)
        self.assertTrue(result)
        
        active_alerts = self.collector.get_active_alerts()
        self.assertEqual(len(active_alerts), 0)


class TestSLO(unittest.TestCase):
    """SLO测试"""
    
    def setUp(self):
        """测试前准备"""
        self.collector = MetricsCollector()
    
    def test_create_slo(self):
        """测试创建SLO"""
        slo_id = self.collector.create_slo(
            name="API可用性",
            description="API服务可用性SLO",
            target=99.9,
            period_days=30
        )
        
        self.assertIsNotNone(slo_id)
        self.assertTrue(slo_id.startswith("SLO-"))
        self.assertIn(slo_id, self.collector.slos)
    
    def test_update_slo(self):
        """测试更新SLO"""
        slo_id = self.collector.create_slo(
            name="响应时间",
            description="API响应时间SLO",
            target=99.0
        )
        
        result = self.collector.update_slo(slo_id, 99.5)
        self.assertTrue(result)
        
        slo = self.collector.slos[slo_id]
        self.assertEqual(slo.current_value, 99.5)


class TestNotificationChannel(unittest.TestCase):
    """通知渠道测试"""
    
    def setUp(self):
        """测试前准备"""
        self.collector = MetricsCollector()
    
    def test_create_notification_channel(self):
        """测试创建通知渠道"""
        channel_id = self.collector.create_notification_channel(
            name="控制台通知",
            channel_type=NotificationChannelType.CONSOLE
        )
        
        self.assertIsNotNone(channel_id)
        self.assertTrue(channel_id.startswith("CHANNEL-"))
        self.assertIn(channel_id, self.collector.notification_channels)
    
    def test_send_notification(self):
        """测试发送通知"""
        self.collector.create_notification_channel(
            name="控制台通知",
            channel_type=NotificationChannelType.CONSOLE
        )
        
        self.collector.create_metric("test_metric", MetricType.GAUGE)
        self.collector.create_alert_rule(
            name="测试告警",
            metric_name="test_metric",
            condition=">",
            threshold=100.0,
            severity="info"
        )
        
        self.collector.record_metric("test_metric", 150.0)
        
        active_alerts = self.collector.get_active_alerts()
        self.assertEqual(len(active_alerts), 1)


class TestEventManagement(unittest.TestCase):
    """事件管理测试"""
    
    def setUp(self):
        """测试前准备"""
        self.collector = MetricsCollector()
    
    def test_create_event(self):
        """测试创建事件"""
        event_id = self.collector.create_event(
            event_type="system",
            source="test",
            message="系统启动",
            level="info"
        )
        
        self.assertIsNotNone(event_id)
        self.assertTrue(event_id.startswith("EVENT-"))
        self.assertIn(event_id, self.collector.events)
    
    def test_get_events(self):
        """测试获取事件列表"""
        self.collector.create_event("system", "source1", "事件1", "info")
        self.collector.create_event("alert", "source2", "事件2", "warning")
        self.collector.create_event("system", "source3", "事件3", "error")
        
        all_events = self.collector.get_events()
        self.assertEqual(len(all_events), 3)
        
        info_events = self.collector.get_events(level="info")
        self.assertEqual(len(info_events), 1)
        
        system_events = self.collector.get_events(event_type="system")
        self.assertEqual(len(system_events), 2)
    
    def test_event_acknowledge_and_resolve(self):
        """测试事件确认和解决"""
        event_id = self.collector.create_event(
            event_type="error",
            source="test",
            message="发生错误",
            level="error"
        )
        
        self.collector.acknowledge_event(event_id)
        event = self.collector.events[event_id]
        self.assertTrue(event.acknowledged)
        
        self.collector.resolve_event(event_id)
        event = self.collector.events[event_id]
        self.assertTrue(event.resolved)


class TestReportGeneration(unittest.TestCase):
    """报告生成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.collector = MetricsCollector()
    
    def test_generate_report(self):
        """测试生成报告"""
        self.collector.create_metric("cpu_usage", MetricType.GAUGE)
        self.collector.create_metric("memory_usage", MetricType.GAUGE)
        
        self.collector.create_alert_rule(
            name="CPU告警",
            metric_name="cpu_usage",
            condition=">",
            threshold=80.0,
            severity="warning"
        )
        
        self.collector.create_slo("API可用性", "API服务SLO", 99.9)
        
        self.collector.create_event("system", "test", "测试事件", "info")
        
        report = self.collector.generate_report()
        
        self.assertIn("监控指标报告", report)
        self.assertIn("指标总数: 2", report)
        self.assertIn("告警总数: 0", report)
        self.assertIn("SLO总数: 1", report)
        self.assertIn("事件总数: 1", report)


class TestGlobalCollector(unittest.TestCase):
    """全局收集器测试"""
    
    def test_get_metrics_collector(self):
        """测试获取全局收集器"""
        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()
        
        self.assertIs(collector1, collector2)


def run_tests():
    """运行测试"""
    print("=" * 70)
    print("第50阶段测试：运维监控和告警系统")
    print("=" * 70)
    
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    
    test_suite.addTests(test_loader.loadTestsFromTestCase(TestMetricsCollector))
    test_suite.addTests(test_loader.loadTestsFromTestCase(TestAlertRule))
    test_suite.addTests(test_loader.loadTestsFromTestCase(TestSLO))
    test_suite.addTests(test_loader.loadTestsFromTestCase(TestNotificationChannel))
    test_suite.addTests(test_loader.loadTestsFromTestCase(TestEventManagement))
    test_suite.addTests(test_loader.loadTestsFromTestCase(TestReportGeneration))
    test_suite.addTests(test_loader.loadTestsFromTestCase(TestGlobalCollector))
    
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
