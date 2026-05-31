"""
记忆数据统计与异常标记系统
基于第一性原理：读写统计、调用频次、异常检测
"""
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class OperationRecord:
    """操作记录"""
    timestamp: float
    operation: str  # 'read', 'write', 'recall', 'delete'
    memory_level: str  # 'l1', 'l2', 'l3'
    item_id: str
    user: str = 'system'
    success: bool = True
    duration_ms: float = 0.0
    metadata: Dict = field(default_factory=dict)


class StatisticsCollector:
    """统计收集器"""
    
    def __init__(self, max_records: int = 10000):
        self.max_records = max_records
        self._records: List[OperationRecord] = []
        self._counters: Dict[str, int] = defaultdict(int)
        self._counters_by_level: Dict[str, Dict[str, int]] = {
            'l1': defaultdict(int),
            'l2': defaultdict(int),
            'l3': defaultdict(int)
        }
        self._start_time = time.time()
    
    def record_operation(
        self,
        operation: str,
        memory_level: str,
        item_id: str,
        user: str = 'system',
        success: bool = True,
        duration_ms: float = 0.0,
        metadata: Dict = None
    ) -> None:
        """记录操作"""
        record = OperationRecord(
            timestamp=time.time(),
            operation=operation,
            memory_level=memory_level,
            item_id=item_id,
            user=user,
            success=success,
            duration_ms=duration_ms,
            metadata=metadata or {}
        )
        
        self._records.append(record)
        
        # 限制记录数量
        if len(self._records) > self.max_records:
            self._records = self._records[-self.max_records:]
        
        # 更新计数器
        self._counters[operation] += 1
        self._counters_by_level[memory_level][operation] += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """获取统计摘要"""
        uptime = time.time() - self._start_time
        
        return {
            'uptime_seconds': uptime,
            'total_operations': len(self._records),
            'operations_by_type': dict(self._counters),
            'operations_by_level': {
                level: dict(counters)
                for level, counters in self._counters_by_level.items()
            },
            'success_rate': self._calculate_success_rate(),
            'avg_duration_ms': self._calculate_avg_duration(),
            'peak_operations_per_minute': self._calculate_peak_rate()
        }
    
    def get_operations_by_level(self, memory_level: str) -> List[Dict]:
        """获取特定层级的操作记录"""
        return [
            {
                'timestamp': r.timestamp,
                'operation': r.operation,
                'item_id': r.item_id,
                'success': r.success,
                'duration_ms': r.duration_ms
            }
            for r in self._records
            if r.memory_level == memory_level
        ]
    
    def get_user_stats(self, user: str) -> Dict[str, int]:
        """获取用户统计"""
        user_operations = [
            r for r in self._records
            if r.user == user
        ]
        
        return {
            'total_operations': len(user_operations),
            'reads': sum(1 for r in user_operations if r.operation == 'read'),
            'writes': sum(1 for r in user_operations if r.operation == 'write'),
            'success_rate': sum(1 for r in user_operations if r.success) / max(len(user_operations), 1)
        }
    
    def _calculate_success_rate(self) -> float:
        """计算成功率"""
        if not self._records:
            return 0.0
        return sum(1 for r in self._records if r.success) / len(self._records)
    
    def _calculate_avg_duration(self) -> float:
        """计算平均耗时"""
        if not self._records:
            return 0.0
        total = sum(r.duration_ms for r in self._records)
        return total / len(self._records)
    
    def _calculate_peak_rate(self) -> int:
        """计算峰值操作速率（每分钟）"""
        if len(self._records) < 2:
            return 0
        
        # 按分钟分组
        minute_counts = defaultdict(int)
        for r in self._records:
            minute = int(r.timestamp / 60)
            minute_counts[minute] += 1
        
        return max(minute_counts.values()) if minute_counts else 0


class AnomalyMarker:
    """异常标记器"""
    
    def __init__(self, statistics: StatisticsCollector = None):
        self._statistics = statistics or StatisticsCollector()
        self._anomalies: List[Dict] = []
        self._anomaly_thresholds = {
            'error_rate': 0.1,  # 错误率超过10%标记异常
            'avg_duration_ms': 5000,  # 平均耗时超过5秒标记异常
            'write_rate': 100  # 每分钟写入超过100次标记异常
        }
    
    def mark_anomaly(
        self,
        anomaly_type: str,
        description: str,
        severity: str = 'medium',
        metadata: Dict = None
    ) -> str:
        """标记异常"""
        anomaly_id = f"anomaly_{int(time.time() * 1000)}"
        
        anomaly = {
            'id': anomaly_id,
            'type': anomaly_type,
            'description': description,
            'severity': severity,
            'timestamp': time.time(),
            'resolved': False,
            'metadata': metadata or {}
        }
        
        self._anomalies.append(anomaly)
        return anomaly_id
    
    def check_anomalies(self) -> List[Dict]:
        """检查异常"""
        summary = self._statistics.get_summary()
        detected = []
        
        # 检查错误率
        error_rate = 1.0 - summary['success_rate']
        if error_rate > self._anomaly_thresholds['error_rate']:
            detected.append({
                'type': 'high_error_rate',
                'description': f"错误率 {error_rate:.2%} 超过阈值 {self._anomaly_thresholds['error_rate']:.2%}",
                'severity': 'high'
            })
        
        # 检查平均耗时
        avg_duration = summary['avg_duration_ms']
        if avg_duration > self._anomaly_thresholds['avg_duration_ms']:
            detected.append({
                'type': 'high_latency',
                'description': f"平均耗时 {avg_duration:.2f}ms 超过阈值 {self._anomaly_thresholds['avg_duration_ms']}ms",
                'severity': 'medium'
            })
        
        # 标记并返回
        for anomaly in detected:
            self.mark_anomaly(anomaly['type'], anomaly['description'], anomaly['severity'])
        
        return detected
    
    def get_unresolved_anomalies(self) -> List[Dict]:
        """获取未解决的异常"""
        return [a for a in self._anomalies if not a['resolved']]
    
    def resolve_anomaly(self, anomaly_id: str) -> bool:
        """解决异常"""
        for anomaly in self._anomalies:
            if anomaly['id'] == anomaly_id:
                anomaly['resolved'] = True
                anomaly['resolved_at'] = time.time()
                return True
        return False
    
    def get_anomaly_history(self, limit: int = 100) -> List[Dict]:
        """获取异常历史"""
        return self._anomalies[-limit:]


# 全局单例
_statistics_collector = None
_anomaly_marker = None


def get_statistics_collector() -> StatisticsCollector:
    global _statistics_collector
    if _statistics_collector is None:
        _statistics_collector = StatisticsCollector()
    return _statistics_collector


def get_anomaly_marker() -> AnomalyMarker:
    global _anomaly_marker
    if _anomaly_marker is None:
        _anomaly_marker = AnomalyMarker()
    return _anomaly_marker
