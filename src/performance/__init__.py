"""
性能监控与分析模块
用于收集、分析和报告系统性能指标
"""

import time
import threading
import psutil
import os
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
from datetime import datetime


class PerformanceMetricType(Enum):
    """性能指标类型"""
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DISK_IO = "disk_io"
    NETWORK_IO = "network_io"
    LATENCY = "latency"
    CONCURRENT_REQUESTS = "concurrent_requests"


class PerformanceStatus(Enum):
    """性能状态"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class PerformanceMetric:
    """性能指标"""
    metric_id: str
    name: str
    metric_type: PerformanceMetricType
    value: float
    unit: str
    timestamp: datetime
    status: PerformanceStatus = PerformanceStatus.GOOD
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceSnapshot:
    """性能快照"""
    snapshot_id: str
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_sent_mb: float
    network_recv_mb: float
    active_connections: int
    thread_count: int


@dataclass
class PerformanceThreshold:
    """性能阈值"""
    threshold_id: str
    metric_type: PerformanceMetricType
    warning_threshold: float
    critical_threshold: float
    unit: str
    enabled: bool = True


@dataclass
class PerformanceAlert:
    """性能告警"""
    alert_id: str
    metric_type: PerformanceMetricType
    metric_name: str
    value: float
    threshold: float
    severity: str
    timestamp: datetime
    message: str
    resolved: bool = False


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics: Dict[str, PerformanceMetric] = {}
        self.snapshots: List[PerformanceSnapshot] = []
        self.thresholds: Dict[str, PerformanceThreshold] = {}
        self.alerts: Dict[str, PerformanceAlert] = {}
        self._metric_counter: int = 0
        self._snapshot_counter: int = 0
        self._threshold_counter: int = 0
        self._alert_counter: int = 0
        self._lock: threading.Lock = threading.Lock()
        self._monitoring: bool = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._baseline: Optional[Dict[str, float]] = None
    
    def create_metric(
        self,
        name: str,
        metric_type: PerformanceMetricType,
        value: float,
        unit: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """创建性能指标"""
        with self._lock:
            self._metric_counter += 1
            metric_id = f"PERF-METRIC-{self._metric_counter:06d}"
            
            status = self._evaluate_status(metric_type, value)
            
            metric = PerformanceMetric(
                metric_id=metric_id,
                name=name,
                metric_type=metric_type,
                value=value,
                unit=unit,
                timestamp=datetime.now(),
                status=status,
                metadata=metadata or {}
            )
            
            self.metrics[name] = metric
            
            if status in [PerformanceStatus.POOR, PerformanceStatus.CRITICAL]:
                self._create_performance_alert(metric, status)
            
            return metric_id
    
    def _evaluate_status(self, metric_type: PerformanceMetricType, value: float) -> PerformanceStatus:
        """评估性能状态"""
        thresholds = [t for t in self.thresholds.values() 
                     if t.metric_type == metric_type and t.enabled]
        
        if not thresholds:
            if value < 50:
                return PerformanceStatus.EXCELLENT
            elif value < 70:
                return PerformanceStatus.GOOD
            elif value < 85:
                return PerformanceStatus.FAIR
            else:
                return PerformanceStatus.POOR
        
        for threshold in thresholds:
            if value >= threshold.critical_threshold:
                return PerformanceStatus.CRITICAL
            elif value >= threshold.warning_threshold:
                return PerformanceStatus.POOR
        
        if value < 50:
            return PerformanceStatus.EXCELLENT
        elif value < 70:
            return PerformanceStatus.GOOD
        elif value < 85:
            return PerformanceStatus.FAIR
        else:
            return PerformanceStatus.POOR
    
    def _create_performance_alert(self, metric: PerformanceMetric, status: PerformanceStatus) -> None:
        """创建性能告警"""
        with self._lock:
            self._alert_counter += 1
            alert_id = f"PERF-ALERT-{self._alert_counter:06d}"
            
            severity = "warning" if status == PerformanceStatus.POOR else "critical"
            
            alert = PerformanceAlert(
                alert_id=alert_id,
                metric_type=metric.metric_type,
                metric_name=metric.name,
                value=metric.value,
                threshold=self._get_threshold_value(metric.metric_type),
                severity=severity,
                timestamp=datetime.now(),
                message=f"{metric.name} 性能{('警告' if severity == 'warning' else '严重')}: {metric.value}{metric.unit}"
            )
            
            self.alerts[alert_id] = alert
    
    def _get_threshold_value(self, metric_type: PerformanceMetricType) -> float:
        """获取阈值"""
        for threshold in self.thresholds.values():
            if threshold.metric_type == metric_type:
                return threshold.critical_threshold
        return 100.0
    
    def create_threshold(
        self,
        metric_type: PerformanceMetricType,
        warning_threshold: float,
        critical_threshold: float,
        unit: str
    ) -> str:
        """创建性能阈值"""
        with self._lock:
            self._threshold_counter += 1
            threshold_id = f"THRESHOLD-{self._threshold_counter:06d}"
            
            threshold = PerformanceThreshold(
                threshold_id=threshold_id,
                metric_type=metric_type,
                warning_threshold=warning_threshold,
                critical_threshold=critical_threshold,
                unit=unit
            )
            
            self.thresholds[threshold_id] = threshold
            return threshold_id
    
    def take_snapshot(self) -> str:
        """获取系统性能快照"""
        with self._lock:
            self._snapshot_counter += 1
            snapshot_id = f"SNAPSHOT-{self._snapshot_counter:06d}"
            
            try:
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                disk_io = psutil.disk_io_counters()
                net_io = psutil.net_io_counters()
                
                snapshot = PerformanceSnapshot(
                    snapshot_id=snapshot_id,
                    timestamp=datetime.now(),
                    cpu_percent=cpu_percent,
                    memory_percent=memory.percent,
                    memory_used_mb=memory.used / (1024 * 1024),
                    memory_available_mb=memory.available / (1024 * 1024),
                    disk_io_read_mb=disk_io.read_bytes / (1024 * 1024) if disk_io else 0,
                    disk_io_write_mb=disk_io.write_bytes / (1024 * 1024) if disk_io else 0,
                    network_sent_mb=net_io.bytes_sent / (1024 * 1024) if net_io else 0,
                    network_recv_mb=net_io.bytes_recv / (1024 * 1024) if net_io else 0,
                    active_connections=len(psutil.net_connections()),
                    thread_count=threading.active_count()
                )
            except Exception:
                snapshot = PerformanceSnapshot(
                    snapshot_id=snapshot_id,
                    timestamp=datetime.now(),
                    cpu_percent=0.0,
                    memory_percent=0.0,
                    memory_used_mb=0.0,
                    memory_available_mb=0.0,
                    disk_io_read_mb=0.0,
                    disk_io_write_mb=0.0,
                    network_sent_mb=0.0,
                    network_recv_mb=0.0,
                    active_connections=0,
                    thread_count=0
                )
            
            self.snapshots.append(snapshot)
            
            self.create_metric(
                name="cpu_usage",
                metric_type=PerformanceMetricType.CPU_USAGE,
                value=snapshot.cpu_percent,
                unit="%"
            )
            
            self.create_metric(
                name="memory_usage",
                metric_type=PerformanceMetricType.MEMORY_USAGE,
                value=snapshot.memory_percent,
                unit="%"
            )
            
            return snapshot_id
    
    def record_response_time(
        self,
        operation: str,
        duration: float,
        success: bool = True
    ) -> str:
        """记录响应时间"""
        return self.create_metric(
            name=f"response_time_{operation}",
            metric_type=PerformanceMetricType.RESPONSE_TIME,
            value=duration,
            unit="ms",
            metadata={"success": success, "operation": operation}
        )
    
    def record_throughput(
        self,
        operation: str,
        count: int,
        duration: float
    ) -> str:
        """记录吞吐量"""
        rps = (count / duration) if duration > 0 else 0
        return self.create_metric(
            name=f"throughput_{operation}",
            metric_type=PerformanceMetricType.THROUGHPUT,
            value=rps,
            unit="req/s",
            metadata={"count": count, "duration": duration}
        )
    
    def record_latency(
        self,
        endpoint: str,
        latency: float
    ) -> str:
        """记录延迟"""
        return self.create_metric(
            name=f"latency_{endpoint}",
            metric_type=PerformanceMetricType.LATENCY,
            value=latency,
            unit="ms",
            metadata={"endpoint": endpoint}
        )
    
    def get_metric(self, name: str) -> Optional[PerformanceMetric]:
        """获取性能指标"""
        return self.metrics.get(name)
    
    def get_metrics_by_type(
        self,
        metric_type: PerformanceMetricType
    ) -> List[PerformanceMetric]:
        """按类型获取性能指标"""
        return [
            m for m in self.metrics.values()
            if m.metric_type == metric_type
        ]
    
    def get_active_alerts(self) -> List[PerformanceAlert]:
        """获取活跃告警"""
        return [a for a in self.alerts.values() if not a.resolved]
    
    def resolve_alert(self, alert_id: str) -> bool:
        """解决告警"""
        with self._lock:
            if alert_id not in self.alerts:
                return False
            
            self.alerts[alert_id].resolved = True
            return True
    
    def set_baseline(self) -> Dict[str, float]:
        """设置性能基线"""
        self.take_snapshot()
        
        with self._lock:
            self._baseline = {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory_percent": psutil.virtual_memory().percent,
                "thread_count": threading.active_count()
            }
            
            return self._baseline
    
    def compare_to_baseline(self) -> Dict[str, Any]:
        """与基线比较"""
        if not self._baseline:
            return {"error": "No baseline set"}
        
        current = self.take_snapshot()
        snapshot = self.snapshots[-1]
        
        return {
            "cpu_diff": snapshot.cpu_percent - self._baseline["cpu_percent"],
            "memory_diff": snapshot.memory_percent - self._baseline["memory_percent"],
            "thread_diff": snapshot.thread_count - self._baseline["thread_count"],
            "current": {
                "cpu_percent": snapshot.cpu_percent,
                "memory_percent": snapshot.memory_percent,
                "thread_count": snapshot.thread_count
            },
            "baseline": self._baseline
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        if not self.snapshots:
            self.take_snapshot()
        
        latest = self.snapshots[-1]
        
        avg_cpu = sum(s.cpu_percent for s in self.snapshots[-10:]) / min(len(self.snapshots), 10)
        avg_memory = sum(s.memory_percent for s in self.snapshots[-10:]) / min(len(self.snapshots), 10)
        
        return {
            "timestamp": datetime.now(),
            "latest": {
                "cpu_percent": latest.cpu_percent,
                "memory_percent": latest.memory_percent,
                "thread_count": latest.thread_count,
                "active_connections": latest.active_connections
            },
            "average_10": {
                "cpu_percent": avg_cpu,
                "memory_percent": avg_memory
            },
            "metrics_count": len(self.metrics),
            "active_alerts": len(self.get_active_alerts())
        }
    
    def start_monitoring(self, interval: int = 60) -> None:
        """开始性能监控"""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self._monitor_thread.start()
    
    def stop_monitoring(self) -> None:
        """停止性能监控"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5.0)
    
    def _monitor_loop(self, interval: int) -> None:
        """监控循环"""
        while self._monitoring:
            try:
                self.take_snapshot()
            except Exception:
                pass
            
            time.sleep(interval)


_global_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """获取全局性能监控器"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
    return _global_monitor
