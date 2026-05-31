"""
性能监控与基准测试
"""

import time
import statistics
from typing import Dict, Any, List, Callable
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class PerformanceStats:
    """性能统计"""
    min_ms: float = float('inf')
    max_ms: float = 0.0
    avg_ms: float = 0.0
    p50_ms: float = 0.0
    p95_ms: float = 0.0
    p99_ms: float = 0.0
    total_ops: int = 0
    throughput_ops_sec: float = 0.0
    total_time_ms: float = 0.0


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self._operation_times: Dict[str, List[float]] = defaultdict(list)
        self._start_times: Dict[str, float] = {}
        self._operation_counts: Dict[str, int] = defaultdict(int)
    
    def start_operation(self, operation_name: str) -> str:
        """开始操作计时"""
        op_id = f"{operation_name}_{int(time.time() * 1000)}"
        self._start_times[op_id] = time.perf_counter()
        return op_id
    
    def end_operation(self, op_id: str) -> float:
        """结束操作计时"""
        if op_id not in self._start_times:
            return 0.0
        
        duration_ms = (time.perf_counter() - self._start_times[op_id]) * 1000
        
        operation_name = op_id.rsplit('_', 1)[0]
        self._operation_times[operation_name].append(duration_ms)
        self._operation_counts[operation_name] += 1
        
        del self._start_times[op_id]
        return duration_ms
    
    def measure(self, operation_name: str, func: Callable, *args, **kwargs) -> Any:
        """测量函数执行时间"""
        op_id = self.start_operation(operation_name)
        try:
            return func(*args, **kwargs)
        finally:
            self.end_operation(op_id)
    
    def get_stats(self, operation_name: str) -> PerformanceStats:
        """获取操作统计"""
        times = self._operation_times.get(operation_name, [])
        if not times:
            return PerformanceStats()
        
        times_sorted = sorted(times)
        n = len(times)
        
        total_ms = sum(times)
        total_sec = total_ms / 1000
        
        return PerformanceStats(
            min_ms=min(times),
            max_ms=max(times),
            avg_ms=total_ms / n,
            p50_ms=times_sorted[int(n * 0.5)],
            p95_ms=times_sorted[int(n * 0.95)],
            p99_ms=times_sorted[int(n * 0.99)],
            total_ops=n,
            throughput_ops_sec=n / total_sec if total_sec > 0 else 0,
            total_time_ms=total_ms
        )
    
    def get_all_stats(self) -> Dict[str, PerformanceStats]:
        """获取所有操作统计"""
        return {
            name: self.get_stats(name)
            for name in self._operation_times.keys()
        }
    
    def reset(self):
        """重置监控"""
        self._operation_times.clear()
        self._start_times.clear()
        self._operation_counts.clear()


_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """获取性能监控器"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def benchmark_function(
    func: Callable,
    *args,
    iterations: int = 1000,
    warmup: int = 100,
    **kwargs
) -> PerformanceStats:
    """基准测试函数"""
    monitor = PerformanceMonitor()
    
    for i in range(warmup):
        func(*args, **kwargs)
    
    for i in range(iterations):
        monitor.measure("benchmark", func, *args, **kwargs)
    
    return monitor.get_stats("benchmark")


def format_stats(stats: PerformanceStats, name: str = "") -> str:
    """格式化统计输出"""
    lines = []
    if name:
        lines.append(f"{'=' * 60}")
        lines.append(f"{name}")
        lines.append(f"{'=' * 60}")
    
    lines.append(f"操作次数: {stats.total_ops:,}")
    lines.append(f"总耗时: {stats.total_time_ms:.2f} ms")
    lines.append(f"吞吐量: {stats.throughput_ops_sec:,.1f} ops/sec")
    lines.append("")
    lines.append(f"最小: {stats.min_ms:.3f} ms")
    lines.append(f"平均: {stats.avg_ms:.3f} ms")
    lines.append(f"中位数: {stats.p50_ms:.3f} ms")
    lines.append(f"P95: {stats.p95_ms:.3f} ms")
    lines.append(f"P99: {stats.p99_ms:.3f} ms")
    lines.append(f"最大: {stats.max_ms:.3f} ms")
    
    return '\n'.join(lines)
