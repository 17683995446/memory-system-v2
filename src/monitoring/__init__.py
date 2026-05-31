"""
记忆系统监控与诊断模块
基于第一性原理：可观测性、可诊断性、实时反馈
"""

import time
import threading
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
from datetime import datetime

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """指标类型"""
    COUNTER = "counter"  # 计数器（累加）
    GAUGE = "gauge"  # 仪表盘（可上下波动）
    HISTOGRAM = "histogram"  # 直方图（分布统计）
    TIMER = "timer"  # 计时器（耗时统计）


class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Metric:
    """指标数据"""
    name: str
    type: MetricType
    value: Any
    timestamp: float = field(default_factory=time.time)
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Alert:
    """告警信息"""
    id: str
    level: AlertLevel
    message: str
    timestamp: float = field(default_factory=time.time)
    source: str = "monitoring"
    metadata: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[float] = None


class MetricsCollector:
    """指标收集器"""

    def __init__(self, max_history: int = 1000):
        self._lock = threading.Lock()
        self._metrics: Dict[str, List[Metric]] = defaultdict(list)
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = defaultdict(float)
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._timers: Dict[str, List[float]] = defaultdict(list)
        self._max_history = max_history
        self._start_times: Dict[str, float] = {}

    def increment(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None) -> None:
        """增加计数器"""
        with self._lock:
            self._counters[name] += value
            metric = Metric(
                name=name,
                type=MetricType.COUNTER,
                value=self._counters[name],
                tags=tags or {}
            )
            self._add_metric(metric)

    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """设置仪表盘值"""
        with self._lock:
            self._gauges[name] = value
            metric = Metric(
                name=name,
                type=MetricType.GAUGE,
                value=value,
                tags=tags or {}
            )
            self._add_metric(metric)

    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """记录直方图数据"""
        with self._lock:
            self._histograms[name].append(value)
            if len(self._histograms[name]) > self._max_history:
                self._histograms[name].pop(0)
            metric = Metric(
                name=name,
                type=MetricType.HISTOGRAM,
                value=value,
                tags=tags or {}
            )
            self._add_metric(metric)

    def start_timer(self, name: str) -> None:
        """开始计时"""
        self._start_times[name] = time.time()

    def stop_timer(self, name: str, tags: Optional[Dict[str, str]] = None) -> float:
        """停止计时并记录"""
        if name not in self._start_times:
            logger.warning(f"Timer {name} not started")
            return 0.0

        elapsed = time.time() - self._start_times[name]
        with self._lock:
            self._timers[name].append(elapsed)
            if len(self._timers[name]) > self._max_history:
                self._timers[name].pop(0)
            metric = Metric(
                name=name,
                type=MetricType.TIMER,
                value=elapsed,
                tags=tags or {}
            )
            self._add_metric(metric)

        del self._start_times[name]
        return elapsed

    def timeit(self, name: str, tags: Optional[Dict[str, str]] = None):
        """计时器装饰器"""
        def decorator(func: Callable):
            def wrapper(*args, **kwargs):
                self.start_timer(name)
                try:
                    return func(*args, **kwargs)
                finally:
                    self.stop_timer(name, tags)
            return wrapper
        return decorator

    def _add_metric(self, metric: Metric) -> None:
        """添加指标到历史记录"""
        self._metrics[metric.name].append(metric)
        if len(self._metrics[metric.name]) > self._max_history:
            self._metrics[metric.name].pop(0)

    def get_counter(self, name: str) -> Optional[int]:
        """获取计数器值"""
        with self._lock:
            return self._counters.get(name)

    def get_gauge(self, name: str) -> Optional[float]:
        """获取仪表盘值"""
        with self._lock:
            return self._gauges.get(name)

    def get_histogram_stats(self, name: str) -> Optional[Dict[str, Any]]:
        """获取直方图统计"""
        with self._lock:
            values = self._histograms.get(name, [])
            if not values:
                return None
            return {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "sum": sum(values)
            }

    def get_timer_stats(self, name: str) -> Optional[Dict[str, Any]]:
        """获取计时器统计"""
        with self._lock:
            values = self._timers.get(name, [])
            if not values:
                return None
            return {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "sum": sum(values),
                "p50": sorted(values)[len(values) // 2],
                "p95": sorted(values)[int(len(values) * 0.95)] if len(values) >= 20 else None,
                "p99": sorted(values)[int(len(values) * 0.99)] if len(values) >= 100 else None
            }

    def get_all_metrics(self) -> Dict[str, Any]:
        """获取所有指标摘要"""
        with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {
                    name: self.get_histogram_stats(name)
                    for name in self._histograms
                },
                "timers": {
                    name: self.get_timer_stats(name)
                    for name in self._timers
                }
            }

    def get_metric_history(self, name: str, limit: int = 100) -> List[Metric]:
        """获取指标历史"""
        with self._lock:
            return self._metrics.get(name, [])[-limit:]

    def reset(self, name: Optional[str] = None) -> None:
        """重置指标"""
        with self._lock:
            if name:
                self._counters.pop(name, None)
                self._gauges.pop(name, None)
                self._histograms.pop(name, None)
                self._timers.pop(name, None)
                self._metrics.pop(name, None)
            else:
                self._counters.clear()
                self._gauges.clear()
                self._histograms.clear()
                self._timers.clear()
                self._metrics.clear()


class AlertManager:
    """告警管理器"""

    def __init__(self, max_alerts: int = 1000):
        self._lock = threading.Lock()
        self._alerts: Dict[str, Alert] = {}
        self._alert_history: deque = deque(maxlen=max_alerts)
        self._alert_listeners: List[Callable[[Alert], None]] = []

    def add_listener(self, listener: Callable[[Alert], None]) -> None:
        """添加告警监听器"""
        self._alert_listeners.append(listener)

    def remove_listener(self, listener: Callable[[Alert], None]) -> None:
        """移除告警监听器"""
        if listener in self._alert_listeners:
            self._alert_listeners.remove(listener)

    def alert(
        self,
        level: AlertLevel,
        message: str,
        source: str = "monitoring",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """触发告警"""
        alert_id = f"alert_{int(time.time() * 1000000)}"
        alert = Alert(
            id=alert_id,
            level=level,
            message=message,
            source=source,
            metadata=metadata or {}
        )

        with self._lock:
            self._alerts[alert_id] = alert
            self._alert_history.append(alert)

        # 通知监听器
        for listener in self._alert_listeners:
            try:
                listener(alert)
            except Exception as e:
                logger.error(f"Alert listener error: {e}")

        # 记录日志
        log_method = {
            AlertLevel.INFO: logger.info,
            AlertLevel.WARNING: logger.warning,
            AlertLevel.ERROR: logger.error,
            AlertLevel.CRITICAL: logger.critical
        }.get(level, logger.error)
        log_method(f"[{level.value.upper()}] {message}")

        return alert_id

    def resolve(self, alert_id: str) -> bool:
        """解决告警"""
        with self._lock:
            if alert_id in self._alerts:
                alert = self._alerts[alert_id]
                alert.resolved = True
                alert.resolved_at = time.time()
                return True
            return False

    def get_active_alerts(self) -> List[Alert]:
        """获取活跃告警"""
        with self._lock:
            return [alert for alert in self._alerts.values() if not alert.resolved]

    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """获取告警历史"""
        with self._lock:
            return list(self._alert_history)[-limit:]

    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """获取特定告警"""
        with self._lock:
            return self._alerts.get(alert_id)


class MemorySystemMonitor:
    """记忆系统监控器"""

    def __init__(self, memory_system=None):
        self.memory_system = memory_system
        self.metrics = MetricsCollector()
        self.alerts = AlertManager()
        self._health_checks: Dict[str, Callable[[], Dict[str, Any]]] = {}
        self._lock = threading.Lock()

        # 注册默认健康检查
        self._register_default_health_checks()

    def _register_default_health_checks(self) -> None:
        """注册默认健康检查"""
        self.register_health_check("memory_sizes", self._check_memory_sizes)
        self.register_health_check("cache_stats", self._check_cache_stats)
        self.register_health_check("backup_status", self._check_backup_status)

    def register_health_check(
        self,
        name: str,
        check_func: Callable[[], Dict[str, Any]]
    ) -> None:
        """注册健康检查"""
        with self._lock:
            self._health_checks[name] = check_func

    def _check_memory_sizes(self) -> Dict[str, Any]:
        """检查记忆系统大小"""
        if not self.memory_system:
            return {"status": "unknown", "reason": "memory_system not set"}

        try:
            stats = self.memory_system.get_statistics()
            return {
                "status": "healthy",
                "l1_size": stats.get("l1", {}).get("size", 0),
                "l2_size": stats.get("l2", {}).get("size", 0),
                "l3_size": stats.get("l3", {}).get("size", 0),
                "total_size": (
                    stats.get("l1", {}).get("size", 0) +
                    stats.get("l2", {}).get("size", 0) +
                    stats.get("l3", {}).get("size", 0)
                )
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    def _check_cache_stats(self) -> Dict[str, Any]:
        """检查缓存统计（如果有）"""
        try:
            # 尝试获取缓存统计
            return {"status": "healthy", "cache_available": False}
        except Exception:
            return {"status": "healthy", "cache_available": False}

    def _check_backup_status(self) -> Dict[str, Any]:
        """检查备份状态"""
        try:
            # 这里可以集成备份系统检查
            return {"status": "healthy", "backup_system_available": False}
        except Exception:
            return {"status": "healthy", "backup_system_available": False}

    def run_health_checks(self) -> Dict[str, Any]:
        """运行所有健康检查"""
        results = {}
        overall_status = "healthy"

        with self._lock:
            for name, check_func in self._health_checks.items():
                try:
                    result = check_func()
                    results[name] = result
                    if result.get("status") == "unhealthy":
                        overall_status = "unhealthy"
                    elif result.get("status") == "degraded" and overall_status == "healthy":
                        overall_status = "degraded"
                except Exception as e:
                    results[name] = {
                        "status": "error",
                        "error": str(e)
                    }
                    overall_status = "unhealthy"

        results["overall"] = {
            "status": overall_status,
            "timestamp": time.time(),
            "datetime": datetime.utcnow().isoformat()
        }

        return results

    def get_status(self) -> Dict[str, Any]:
        """获取完整状态报告"""
        return {
            "timestamp": time.time(),
            "datetime": datetime.utcnow().isoformat(),
            "metrics": self.metrics.get_all_metrics(),
            "alerts": {
                "active": [
                    {
                        "id": a.id,
                        "level": a.level.value,
                        "message": a.message,
                        "source": a.source,
                        "timestamp": a.timestamp
                    }
                    for a in self.alerts.get_active_alerts()
                ]
            },
            "health": self.run_health_checks()
        }

    def record_memory_operation(self, operation: str, success: bool = True) -> None:
        """记录记忆操作"""
        status = "success" if success else "failure"
        self.metrics.increment(f"memory_operations_total", tags={"operation": operation, "status": status})

    def record_query_latency(self, latency: float, query_type: str = "general") -> None:
        """记录查询延迟"""
        self.metrics.record_histogram("query_latency_seconds", latency, tags={"type": query_type})
        self.metrics.record_histogram(f"query_latency_{query_type}_seconds", latency)


# 导出新监控系统的组件
from .metrics_collector import (
    MetricType,
    MetricStatus,
    MetricPoint,
    Metric,
    AlertRule,
    Alert,
    SLO,
    NotificationChannelType,
    NotificationChannel,
    Event,
    MetricsCollector,
    get_metrics_collector
)

# 全局单例
_global_monitor: Optional[MemorySystemMonitor] = None


def get_monitor(memory_system=None) -> MemorySystemMonitor:
    """获取监控器单例"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = MemorySystemMonitor(memory_system)
    elif memory_system is not None and _global_monitor.memory_system is None:
        _global_monitor.memory_system = memory_system
    return _global_monitor
