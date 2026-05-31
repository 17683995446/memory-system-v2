"""
监控指标收集器
用于收集、存储和分析系统监控指标
"""
import time
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
from datetime import datetime, timedelta
import json


class NotificationChannelType(Enum):
    """通知渠道类型"""
    CONSOLE = "console"
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"


@dataclass
class NotificationChannel:
    """通知渠道"""
    channel_id: str
    name: str
    channel_type: NotificationChannelType
    config: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True


@dataclass
class Event:
    """事件"""
    event_id: str
    event_type: str
    source: str
    message: str
    level: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False
    resolved: bool = False


class MetricType(Enum):
    """指标类型"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class MetricStatus(Enum):
    """指标状态"""
    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class MetricPoint:
    """指标数据点"""
    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class Metric:
    """监控指标"""
    metric_id: str
    name: str
    type: MetricType
    help_text: str
    points: List[MetricPoint] = field(default_factory=list)
    status: MetricStatus = MetricStatus.UNKNOWN
    max_points: int = 10000
    unit: str = ""


@dataclass
class AlertRule:
    """告警规则"""
    rule_id: str
    name: str
    metric_name: str
    condition: str
    threshold: float
    severity: str
    window: int
    evaluation_interval: int = 60
    enabled: bool = True


@dataclass
class Alert:
    """告警实例"""
    alert_id: str
    rule_id: str
    name: str
    severity: str
    metric_name: str
    current_value: float
    threshold: float
    condition: str
    timestamp: datetime
    status: str = "firing"
    acknowledged: bool = False
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class SLO:
    """服务等级目标"""
    slo_id: str
    name: str
    description: str
    target: float
    period_days: int
    current_value: float = 0.0
    window_start: Optional[datetime] = None
    period_start: Optional[datetime] = None


class MetricsCollector:
    """监控指标收集器"""
    
    def __init__(self):
        self.metrics: Dict[str, Metric] = {}
        self.alert_rules: Dict[str, AlertRule] = {}
        self.alerts: Dict[str, Alert] = {}
        self.slos: Dict[str, SLO] = {}
        self.notification_channels: Dict[str, NotificationChannel] = {}
        self.events: Dict[str, Event] = {}
        self._metric_counter: int = 0
        self._alert_counter: int = 0
        self._slo_counter: int = 0
        self._channel_counter: int = 0
        self._event_counter: int = 0
        self._lock: threading.Lock = threading.Lock()
        self._collectors: List[Callable] = []
        self._running: bool = False
        self._collector_thread: Optional[threading.Thread] = None
        
    def create_metric(
        self,
        name: str,
        metric_type: MetricType,
        help_text: str = "",
        unit: str = "",
        max_points: int = 10000
    ) -> str:
        """创建监控指标"""
        with self._lock:
            self._metric_counter += 1
            metric_id = f"METRIC-{self._metric_counter:06d}"
            
            metric = Metric(
                metric_id=metric_id,
                name=name,
                type=metric_type,
                help_text=help_text,
                unit=unit,
                max_points=max_points
            )
            
            self.metrics[name] = metric
            return metric_id
    
    def record_metric(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ) -> bool:
        """记录指标数据点"""
        with self._lock:
            if name not in self.metrics:
                return False
            
            metric = self.metrics[name]
            point = MetricPoint(
                timestamp=datetime.now(),
                value=value,
                labels=labels or {}
            )
            
            metric.points.append(point)
            
            if len(metric.points) > metric.max_points:
                metric.points = metric.points[-metric.max_points:]
            
            self._evaluate_alerts(name, value)
            return True
    
    def increment_counter(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None
    ) -> bool:
        """增加计数器指标"""
        with self._lock:
            if name not in self.metrics:
                return False
            
            metric = self.metrics[name]
            last_value = metric.points[-1].value if metric.points else 0.0
            new_value = last_value + value
            
            point = MetricPoint(
                timestamp=datetime.now(),
                value=new_value,
                labels=labels or {}
            )
            
            metric.points.append(point)
            
            if len(metric.points) > metric.max_points:
                metric.points = metric.points[-metric.max_points:]
            
            return True
    
    def get_metric(self, name: str) -> Optional[Metric]:
        """获取指标"""
        return self.metrics.get(name)
    
    def get_metric_values(
        self,
        name: str,
        since: Optional[datetime] = None
    ) -> List[MetricPoint]:
        """获取指标数据点"""
        if name not in self.metrics:
            return []
        
        points = self.metrics[name].points
        
        if since:
            points = [p for p in points if p.timestamp >= since]
        
        return points
    
    def create_alert_rule(
        self,
        name: str,
        metric_name: str,
        condition: str,
        threshold: float,
        severity: str,
        window: int = 60,
        evaluation_interval: int = 60
    ) -> str:
        """创建告警规则"""
        with self._lock:
            self._alert_counter += 1
            rule_id = f"ALERT-RULE-{self._alert_counter:06d}"
            
            rule = AlertRule(
                rule_id=rule_id,
                name=name,
                metric_name=metric_name,
                condition=condition,
                threshold=threshold,
                severity=severity,
                window=window,
                evaluation_interval=evaluation_interval
            )
            
            self.alert_rules[rule_id] = rule
            return rule_id
    
    def _evaluate_alerts(self, metric_name: str, value: float) -> None:
        """评估告警规则（内部方法）"""
        rules = [r for r in self.alert_rules.values() if r.metric_name == metric_name and r.enabled]
        
        for rule in rules:
            if self._check_condition(rule, value):
                self._fire_alert(rule, value)
    
    def _check_condition(self, rule: AlertRule, value: float) -> bool:
        """检查告警条件"""
        if rule.condition == ">":
            return value > rule.threshold
        elif rule.condition == ">=":
            return value >= rule.threshold
        elif rule.condition == "<":
            return value < rule.threshold
        elif rule.condition == "<=":
            return value <= rule.threshold
        elif rule.condition == "==":
            return value == rule.threshold
        elif rule.condition == "!=":
            return value != rule.threshold
        else:
            return False
    
    def _fire_alert(self, rule: AlertRule, current_value: float) -> None:
        """触发告警"""
        with self._lock:
            self._alert_counter += 1
            alert_id = f"ALERT-{self._alert_counter:06d}"
            
            alert = Alert(
                alert_id=alert_id,
                rule_id=rule.rule_id,
                name=rule.name,
                severity=rule.severity,
                metric_name=rule.metric_name,
                current_value=current_value,
                threshold=rule.threshold,
                condition=rule.condition,
                timestamp=datetime.now()
            )
            
            self.alerts[alert_id] = alert
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """确认告警"""
        with self._lock:
            if alert_id not in self.alerts:
                return False
            
            alert = self.alerts[alert_id]
            alert.acknowledged = True
            return True
    
    def resolve_alert(self, alert_id: str) -> bool:
        """解决告警"""
        with self._lock:
            if alert_id not in self.alerts:
                return False
            
            alert = self.alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.now()
            alert.status = "resolved"
            return True
    
    def get_active_alerts(self, severity: Optional[str] = None) -> List[Alert]:
        """获取活跃告警"""
        alerts = [a for a in self.alerts.values() if not a.resolved]
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        return alerts
    
    def create_slo(
        self,
        name: str,
        description: str,
        target: float,
        period_days: int = 30
    ) -> str:
        """创建服务等级目标"""
        with self._lock:
            self._slo_counter += 1
            slo_id = f"SLO-{self._slo_counter:06d}"
            
            slo = SLO(
                slo_id=slo_id,
                name=name,
                description=description,
                target=target,
                period_days=period_days,
                current_value=target,
                window_start=datetime.now(),
                period_start=datetime.now()
            )
            
            self.slos[slo_id] = slo
            return slo_id
    
    def update_slo(self, slo_id: str, value: float) -> bool:
        """更新SLO值"""
        with self._lock:
            if slo_id not in self.slos:
                return False
            
            self.slos[slo_id].current_value = value
            return True
    
    def add_collector(self, collector_func: Callable) -> None:
        """添加自定义收集器"""
        self._collectors.append(collector_func)
    
    def start_collecting(self, interval: int = 60) -> None:
        """开始自动收集"""
        if self._running:
            return
        
        self._running = True
        self._collector_thread = threading.Thread(
            target=self._collect_loop,
            args=(interval,),
            daemon=True
        )
        self._collector_thread.start()
    
    def stop_collecting(self) -> None:
        """停止自动收集"""
        self._running = False
        if self._collector_thread:
            self._collector_thread.join(timeout=5.0)
    
    def _collect_loop(self, interval: int) -> None:
        """收集循环"""
        while self._running:
            try:
                for collector in self._collectors:
                    try:
                        collector()
                    except Exception:
                        pass
            except Exception:
                pass
            
            time.sleep(interval)
    
    def create_notification_channel(
        self,
        name: str,
        channel_type: NotificationChannelType,
        config: Optional[Dict[str, Any]] = None
    ) -> str:
        """创建通知渠道"""
        with self._lock:
            self._channel_counter += 1
            channel_id = f"CHANNEL-{self._channel_counter:06d}"
            
            channel = NotificationChannel(
                channel_id=channel_id,
                name=name,
                channel_type=channel_type,
                config=config or {}
            )
            
            self.notification_channels[channel_id] = channel
            return channel_id
    
    def send_notification(self, alert: Alert) -> bool:
        """发送告警通知"""
        with self._lock:
            channels = [c for c in self.notification_channels.values() if c.enabled]
            
            for channel in channels:
                try:
                    self._send_to_channel(channel, alert)
                except Exception:
                    pass
            
            return len(channels) > 0
    
    def _send_to_channel(self, channel: NotificationChannel, alert: Alert) -> None:
        """发送到指定渠道"""
        if channel.channel_type == NotificationChannelType.CONSOLE:
            print(f"[ALERT {alert.severity}] {alert.name}: {alert.metric_name} = {alert.current_value} {alert.condition} {alert.threshold}")
        elif channel.channel_type == NotificationChannelType.EMAIL:
            pass
        elif channel.channel_type == NotificationChannelType.SLACK:
            pass
        elif channel.channel_type == NotificationChannelType.WEBHOOK:
            pass
    
    def create_event(
        self,
        event_type: str,
        source: str,
        message: str,
        level: str = "info",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """创建事件"""
        with self._lock:
            self._event_counter += 1
            event_id = f"EVENT-{self._event_counter:06d}"
            
            event = Event(
                event_id=event_id,
                event_type=event_type,
                source=source,
                message=message,
                level=level,
                timestamp=datetime.now(),
                metadata=metadata or {}
            )
            
            self.events[event_id] = event
            return event_id
    
    def acknowledge_event(self, event_id: str) -> bool:
        """确认事件"""
        with self._lock:
            if event_id not in self.events:
                return False
            
            self.events[event_id].acknowledged = True
            return True
    
    def resolve_event(self, event_id: str) -> bool:
        """解决事件"""
        with self._lock:
            if event_id not in self.events:
                return False
            
            self.events[event_id].resolved = True
            return True
    
    def get_events(
        self,
        event_type: Optional[str] = None,
        level: Optional[str] = None,
        unresolved_only: bool = False
    ) -> List[Event]:
        """获取事件列表"""
        events = list(self.events.values())
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        if level:
            events = [e for e in events if e.level == level]
        if unresolved_only:
            events = [e for e in events if not e.resolved]
        
        return sorted(events, key=lambda e: e.timestamp, reverse=True)
    
    def _fire_alert(self, rule: AlertRule, current_value: float) -> None:
        """触发告警"""
        with self._lock:
            self._alert_counter += 1
            alert_id = f"ALERT-{self._alert_counter:06d}"
            
            alert = Alert(
                alert_id=alert_id,
                rule_id=rule.rule_id,
                name=rule.name,
                severity=rule.severity,
                metric_name=rule.metric_name,
                current_value=current_value,
                threshold=rule.threshold,
                condition=rule.condition,
                timestamp=datetime.now()
            )
            
            self.alerts[alert_id] = alert
        
        self.send_notification(alert)
        self.create_event(
            event_type="alert",
            source="monitoring",
            message=f"告警触发: {rule.name}",
            level=rule.severity,
            metadata={"alert_id": alert_id, "metric_name": rule.metric_name}
        )
    
    def generate_report(self) -> str:
        """生成监控报告"""
        report = []
        report.append("=" * 70)
        report.append("监控指标报告")
        report.append("=" * 70)
        
        report.append(f"\n指标总数: {len(self.metrics)}")
        for name, metric in self.metrics.items():
            report.append(f"\n  指标: {name}")
            report.append(f"    类型: {metric.type.value}")
            report.append(f"    状态: {metric.status.value}")
            report.append(f"    数据点: {len(metric.points)}")
            if metric.unit:
                report.append(f"    单位: {metric.unit}")
        
        report.append(f"\n告警总数: {len(self.alerts)}")
        active_alerts = self.get_active_alerts()
        report.append(f"活跃告警: {len(active_alerts)}")
        
        for alert in active_alerts:
            report.append(f"\n  告警: {alert.name}")
            report.append(f"    级别: {alert.severity}")
            report.append(f"    当前值: {alert.current_value}")
            report.append(f"    阈值: {alert.threshold}")
            report.append(f"    时间: {alert.timestamp}")
        
        report.append(f"\nSLO总数: {len(self.slos)}")
        for slo in self.slos.values():
            report.append(f"\n  SLO: {slo.name}")
            report.append(f"    当前值: {slo.current_value}")
            report.append(f"    周期: {slo.period_days}天")
        
        report.append(f"\n事件总数: {len(self.events)}")
        unresolved_events = self.get_events(unresolved_only=True)
        report.append(f"未解决事件: {len(unresolved_events)}")
        
        for event in unresolved_events[:10]:
            report.append(f"\n  事件: {event.event_type}")
            report.append(f"    级别: {event.level}")
            report.append(f"    来源: {event.source}")
            report.append(f"    消息: {event.message}")
            report.append(f"    时间: {event.timestamp}")
        
        report.append("\n" + "=" * 70)
        return "\n".join(report)


_global_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """获取全局指标收集器"""
    global _global_collector
    if _global_collector is None:
        _global_collector = MetricsCollector()
    return _global_collector
