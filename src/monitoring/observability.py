"""
可观测性系统 - 指标、日志、追踪三位一体
基于第一性原理：可测量才可优化，可观测才可诊断
"""

import time
import threading
import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from collections import deque
from enum import Enum

from ..utils.logger import get_logger

logger = get_logger()


class SLOStatus(Enum):
    """SLO状态"""
    HEALTHY = "healthy"      # 达标
    WARNING = "warning"      # 接近阈值
    BREACH = "breach"        # 违约


@dataclass
class SLI:
    """服务水平指标"""
    name: str
    value: float
    threshold: float
    comparator: str  # 'gt', 'lt', 'eq'
    timestamp: float = field(default_factory=time.time)

    @property
    def status(self) -> SLOStatus:
        if self.comparator == 'lt':
            if self.value <= self.threshold * 0.8:
                return SLOStatus.HEALTHY
            elif self.value <= self.threshold:
                return SLOStatus.WARNING
            return SLOStatus.BREACH
        elif self.comparator == 'gt':
            if self.value >= self.threshold * 1.2:
                return SLOStatus.HEALTHY
            elif self.value >= self.threshold:
                return SLOStatus.WARNING
            return SLOStatus.BREACH
        return SLOStatus.HEALTHY


@dataclass
class TraceSpan:
    """分布式追踪Span"""
    trace_id: str
    span_id: str
    parent_id: Optional[str]
    operation: str
    start_time: float
    end_time: Optional[float] = None
    tags: Dict[str, str] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)

    def finish(self):
        self.end_time = time.time()

    @property
    def duration_ms(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0.0


class PrometheusExporter:
    """Prometheus格式指标导出器"""

    def __init__(self):
        self._counters: Dict[str, Dict[str, Any]] = {}
        self._gauges: Dict[str, Dict[str, Any]] = {}
        self._histograms: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def counter(self, name: str, value: int, labels: Optional[Dict[str, str]] = None, help_text: str = ""):
        """记录计数器"""
        with self._lock:
            key = self._label_key(name, labels)
            if key not in self._counters:
                self._counters[key] = {"name": name, "value": 0, "labels": labels or {}, "help": help_text}
            self._counters[key]["value"] += value

    def gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None, help_text: str = ""):
        """记录仪表盘"""
        with self._lock:
            key = self._label_key(name, labels)
            self._gauges[key] = {"name": name, "value": value, "labels": labels or {}, "help": help_text}

    def histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None,
                  buckets: Optional[List[float]] = None, help_text: str = ""):
        """记录直方图"""
        with self._lock:
            key = self._label_key(name, labels)
            if key not in self._histograms:
                self._histograms[key] = {
                    "name": name, "values": [], "labels": labels or {},
                    "buckets": buckets or [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
                    "help": help_text
                }
            self._histograms[key]["values"].append(value)

    def _label_key(self, name: str, labels: Optional[Dict[str, str]]) -> str:
        if not labels:
            return name
        label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def render(self) -> str:
        """渲染Prometheus格式文本"""
        lines = []

        with self._lock:
            # 计数器
            for key, data in self._counters.items():
                if data["help"]:
                    lines.append(f"# HELP {data['name']} {data['help']}")
                lines.append(f"# TYPE {data['name']} counter")
                label_str = self._format_labels(data["labels"])
                lines.append(f"{data['name']}{label_str} {data['value']}")

            # 仪表盘
            for key, data in self._gauges.items():
                if data["help"]:
                    lines.append(f"# HELP {data['name']} {data['help']}")
                lines.append(f"# TYPE {data['name']} gauge")
                label_str = self._format_labels(data["labels"])
                lines.append(f"{data['name']}{label_str} {data['value']}")

            # 直方图
            for key, data in self._histograms.items():
                if data["help"]:
                    lines.append(f"# HELP {data['name']} {data['help']}")
                lines.append(f"# TYPE {data['name']} histogram")
                values = data["values"]
                buckets = data["buckets"]
                label_str = self._format_labels(data["labels"])

                cumulative = 0
                for bucket in buckets:
                    cumulative = sum(1 for v in values if v <= bucket)
                    lines.append(f'{data["name"]}_bucket{{le="{bucket}"{label_str[1:-1] and "," + label_str[1:-1]}}} {cumulative}')
                lines.append(f'{data["name"]}_bucket{{le="+Inf"{label_str[1:-1] and "," + label_str[1:-1]}}} {len(values)}')
                lines.append(f'{data["name"]}_sum{label_str} {sum(values)}')
                lines.append(f'{data["name"]}_count{label_str} {len(values)}')

        return "\n".join(lines) + "\n"

    def _format_labels(self, labels: Dict[str, str]) -> str:
        if not labels:
            return ""
        return "{" + ",".join(f'{k}="{v}"' for k, v in labels.items()) + "}"


class AlertRule:
    """告警规则"""

    def __init__(self, name: str, condition: Callable[[Dict[str, Any]], bool],
                 level: str, message_template: str, cooldown_seconds: float = 300):
        self.name = name
        self.condition = condition
        self.level = level
        self.message_template = message_template
        self.cooldown_seconds = cooldown_seconds
        self.last_triggered: Optional[float] = None

    def evaluate(self, metrics: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """评估规则"""
        if self.last_triggered and time.time() - self.last_triggered < self.cooldown_seconds:
            return None

        try:
            if self.condition(metrics):
                self.last_triggered = time.time()
                return {
                    "rule": self.name,
                    "level": self.level,
                    "message": self.message_template.format(**metrics),
                    "timestamp": time.time()
                }
        except Exception as e:
            logger.error(f"[AlertRule] {self.name} evaluation error: {e}")

        return None


class AutoAlertEngine:
    """自动告警引擎"""

    def __init__(self):
        self.rules: List[AlertRule] = []
        self._alerts_fired: deque = deque(maxlen=1000)
        self._lock = threading.Lock()
        self._setup_default_rules()

    def _setup_default_rules(self):
        """设置默认告警规则"""
        # 内存使用过高
        self.add_rule(AlertRule(
            name="memory_usage_high",
            condition=lambda m: m.get("l1_size", 0) + m.get("l2_size", 0) + m.get("l3_size", 0) > 100000,
            level="warning",
            message_template="总记忆数过高: {l1_size}+{l2_size}+{l3_size}"
        ))

        # 操作失败率过高
        self.add_rule(AlertRule(
            name="operation_failure_rate_high",
            condition=lambda m: m.get("failure_rate", 0) > 0.05,
            level="critical",
            message_template="操作失败率过高: {failure_rate:.2%}"
        ))

        # 响应时间过长
        self.add_rule(AlertRule(
            name="response_time_high",
            condition=lambda m: m.get("avg_response_time_ms", 0) > 5000,
            level="warning",
            message_template="平均响应时间过长: {avg_response_time_ms:.0f}ms"
        ))

        # 错误数激增
        self.add_rule(AlertRule(
            name="error_spike",
            condition=lambda m: m.get("errors_per_minute", 0) > 100,
            level="error",
            message_template="错误数激增: {errors_per_minute}/分钟"
        ))

    def add_rule(self, rule: AlertRule):
        self.rules.append(rule)

    def evaluate_all(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """评估所有规则"""
        alerts = []
        for rule in self.rules:
            result = rule.evaluate(metrics)
            if result:
                alerts.append(result)
                with self._lock:
                    self._alerts_fired.append(result)
        return alerts

    def get_recent_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._alerts_fired)[-limit:]


class Tracer:
    """分布式追踪器"""

    def __init__(self, max_traces: int = 1000):
        self._traces: Dict[str, List[TraceSpan]] = {}
        self._spans: Dict[str, TraceSpan] = {}
        self._lock = threading.Lock()
        self._max_traces = max_traces

    def start_span(self, trace_id: str, operation: str, parent_id: Optional[str] = None,
                   tags: Optional[Dict[str, str]] = None) -> TraceSpan:
        """开始一个Span"""
        import uuid
        span_id = str(uuid.uuid4())[:16]
        span = TraceSpan(
            trace_id=trace_id,
            span_id=span_id,
            parent_id=parent_id,
            operation=operation,
            start_time=time.time(),
            tags=tags or {}
        )
        with self._lock:
            if trace_id not in self._traces:
                self._traces[trace_id] = []
            self._traces[trace_id].append(span)
            self._spans[span_id] = span
        return span

    def finish_span(self, span_id: str):
        """结束Span"""
        with self._lock:
            if span_id in self._spans:
                self._spans[span_id].finish()

    def get_trace(self, trace_id: str) -> List[Dict[str, Any]]:
        """获取追踪数据"""
        with self._lock:
            spans = self._traces.get(trace_id, [])
            return [{
                "trace_id": s.trace_id,
                "span_id": s.span_id,
                "parent_id": s.parent_id,
                "operation": s.operation,
                "duration_ms": s.duration_ms,
                "tags": s.tags,
                "logs": s.logs
            } for s in spans]

    def trace(self, operation: str):
        """追踪装饰器"""
        import uuid
        def decorator(func: Callable):
            def wrapper(*args, **kwargs):
                trace_id = str(uuid.uuid4())
                span = self.start_span(trace_id, operation)
                try:
                    return func(*args, **kwargs)
                finally:
                    span.finish()
            return wrapper
        return decorator


class ObservabilitySystem:
    """可观测性系统 - 统一入口"""

    def __init__(self):
        self.prometheus = PrometheusExporter()
        self.alerts = AutoAlertEngine()
        self.tracer = Tracer()
        self._slis: List[SLI] = []
        self._lock = threading.Lock()

    def record_counter(self, name: str, value: int = 1, labels: Optional[Dict[str, str]] = None):
        """记录计数器"""
        self.prometheus.counter(name, value, labels)

    def record_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """记录仪表盘"""
        self.prometheus.gauge(name, value, labels)

    def record_latency(self, name: str, duration_ms: float, labels: Optional[Dict[str, str]] = None):
        """记录延迟"""
        self.prometheus.histogram(f"{name}_duration_seconds", duration_ms / 1000.0, labels)

    def record_sli(self, name: str, value: float, threshold: float, comparator: str = 'lt'):
        """记录SLI"""
        sli = SLI(name=name, value=value, threshold=threshold, comparator=comparator)
        with self._lock:
            self._slis.append(sli)
            # 只保留最近的100个
            if len(self._slis) > 100:
                self._slis = self._slis[-100:]
        return sli.status

    def evaluate_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """评估告警"""
        return self.alerts.evaluate_all(metrics)

    def get_prometheus_metrics(self) -> str:
        """获取Prometheus格式指标"""
        return self.prometheus.render()

    def get_slo_report(self) -> Dict[str, Any]:
        """获取SLO报告"""
        with self._lock:
            report = {
                "timestamp": time.time(),
                "slis": []
            }
            for sli in self._slis:
                report["slis"].append({
                    "name": sli.name,
                    "value": sli.value,
                    "threshold": sli.threshold,
                    "status": sli.status.value,
                    "timestamp": sli.timestamp
                })
            # 统计
            healthy = sum(1 for s in self._slis if s.status == SLOStatus.HEALTHY)
            warning = sum(1 for s in self._slis if s.status == SLOStatus.WARNING)
            breach = sum(1 for s in self._slis if s.status == SLOStatus.BREACH)
            report["summary"] = {
                "total": len(self._slis),
                "healthy": healthy,
                "warning": warning,
                "breach": breach
            }
            return report

    def get_health_score(self) -> float:
        """获取健康评分 0-100"""
        with self._lock:
            if not self._slis:
                return 100.0
            healthy = sum(1 for s in self._slis if s.status == SLOStatus.HEALTHY)
            return (healthy / len(self._slis)) * 100


# 全局可观测性实例
_observability: Optional[ObservabilitySystem] = None


def get_observability() -> ObservabilitySystem:
    """获取可观测性系统单例"""
    global _observability
    if _observability is None:
        _observability = ObservabilitySystem()
    return _observability
