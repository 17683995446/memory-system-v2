"""
记忆统计分析/仪表盘功能模块
基于第一性原理：确定性、简洁性、可扩展性
"""

import time
from typing import Dict, List, Optional, Any
from collections import defaultdict
from datetime import datetime, timedelta


class MemoryStatistics:
    """记忆统计类"""

    def __init__(self):
        self.total_memories = 0
        self.total_accesses = 0
        self.total_words = 0
        self.avg_memory_size = 0
        self.memory_level_distribution = {}
        self.tag_distribution = {}
        self.importance_distribution = {}
        self.hourly_activity = defaultdict(int)
        self.daily_activity = defaultdict(int)
        self.weekly_activity = defaultdict(int)
        self.monthly_activity = defaultdict(int)


class TrendAnalyzer:
    """趋势分析器"""

    @staticmethod
    def calculate_growth_rate(values: List[float], window: int = 7) -> Dict[str, Any]:
        """计算增长率"""
        if len(values) < 2:
            return {"growth_rate": 0, "trend": "stable"}

        recent = values[-window:] if len(values) >= window else values
        if len(recent) < 2:
            return {"growth_rate": 0, "trend": "stable"}

        first_half_avg = sum(recent[:len(recent)//2]) / (len(recent)//2)
        second_half_avg = sum(recent[len(recent)//2:]) / (len(recent) - len(recent)//2)

        if first_half_avg == 0:
            growth_rate = 0
        else:
            growth_rate = ((second_half_avg - first_half_avg) / first_half_avg) * 100

        if growth_rate > 5:
            trend = "increasing"
        elif growth_rate < -5:
            trend = "decreasing"
        else:
            trend = "stable"

        return {
            "growth_rate": growth_rate,
            "trend": trend,
            "first_half_avg": first_half_avg,
            "second_half_avg": second_half_avg
        }

    @staticmethod
    def detect_anomalies(values: List[float], threshold: float = 2.0) -> List[int]:
        """检测异常值"""
        if len(values) < 3:
            return []

        avg = sum(values) / len(values)
        variance = sum((x - avg) ** 2 for x in values) / len(values)
        std_dev = variance ** 0.5

        anomalies = []
        for i, value in enumerate(values):
            if abs(value - avg) > threshold * std_dev:
                anomalies.append(i)

        return anomalies


class MemoryDashboard:
    """记忆仪表盘"""

    def __init__(self, memory_system=None):
        self.memory_system = memory_system
        self.statistics = MemoryStatistics()
        self.trend_analyzer = TrendAnalyzer()

    def collect_statistics(self) -> Dict[str, Any]:
        """收集记忆统计信息"""
        if not self.memory_system:
            return {}

        # 基础统计
        l1_memories = getattr(self.memory_system, 'l1', None)
        l2_memories = getattr(self.memory_system, 'l2', None)
        l3_memories = getattr(self.memory_system, 'l3', None)

        # L1 统计
        l1_count = 0
        l1_accesses = 0
        if l1_memories:
            l1_data = l1_memories.get_all() if hasattr(l1_memories, 'get_all') else []
            l1_count = len(l1_data)
            l1_accesses = sum(1 for m in l1_data if hasattr(m, 'access_count'))

        # L2 统计
        l2_count = 0
        l2_accesses = 0
        l2_words = 0
        if l2_memories:
            l2_data = l2_memories.get_all() if hasattr(l2_memories, 'get_all') else []
            l2_count = len(l2_data)
            l2_accesses = sum(1 for m in l2_data if hasattr(m, 'access_count'))
            l2_words = sum(len(getattr(m, 'text', '').split()) for m in l2_data)

        # L3 统计
        l3_count = 0
        l3_accesses = 0
        if l3_memories:
            l3_data = l3_memories.get_all() if hasattr(l3_memories, 'get_all') else []
            l3_count = len(l3_data)
            l3_accesses = sum(1 for m in l3_data if hasattr(m, 'access_count'))

        # 更新统计对象
        self.statistics.total_memories = l1_count + l2_count + l3_count
        self.statistics.total_accesses = l1_accesses + l2_accesses + l3_accesses
        self.statistics.total_words = l2_words
        self.statistics.avg_memory_size = l2_words / l2_count if l2_count > 0 else 0
        self.statistics.memory_level_distribution = {
            "l1": l1_count,
            "l2": l2_count,
            "l3": l3_count
        }

        return self.get_summary()

    def get_summary(self) -> Dict[str, Any]:
        """获取统计摘要"""
        return {
            "total_memories": self.statistics.total_memories,
            "total_accesses": self.statistics.total_accesses,
            "total_words": self.statistics.total_words,
            "avg_memory_size": self.statistics.avg_memory_size,
            "memory_level_distribution": self.statistics.memory_level_distribution
        }

    def get_detailed_stats(self) -> Dict[str, Any]:
        """获取详细统计"""
        return {
            "summary": self.get_summary(),
            "importance_distribution": self.statistics.importance_distribution,
            "tag_distribution": self.statistics.tag_distribution,
            "hourly_activity": dict(self.statistics.hourly_activity),
            "daily_activity": dict(self.statistics.daily_activity)
        }

    def generate_report(self) -> str:
        """生成统计报告"""
        summary = self.get_summary()

        report_lines = [
            "=" * 60,
            "记忆系统统计报告",
            "=" * 60,
            f"总记忆数: {summary['total_memories']}",
            f"总访问次数: {summary['total_accesses']}",
            f"总字数: {summary['total_words']}",
            f"平均记忆大小: {summary['avg_memory_size']:.1f} 字",
            "",
            "记忆层级分布:",
        ]

        for level, count in summary['memory_level_distribution'].items():
            report_lines.append(f"  {level.upper()}: {count} 条")

        report_lines.append("=" * 60)

        return "\n".join(report_lines)

    def export_statistics(self, format: str = "dict") -> Any:
        """导出统计数据"""
        if format == "dict":
            return self.get_detailed_stats()
        elif format == "summary":
            return self.get_summary()
        elif format == "report":
            return self.generate_report()
        else:
            return {}


class ActivityTracker:
    """活动追踪器"""

    def __init__(self):
        self.events = []
        self.trend_analyzer = TrendAnalyzer()

    def track_event(self, event_type: str, memory_id: str, metadata: Optional[Dict[str, Any]] = None):
        """追踪事件"""
        event = {
            "type": event_type,
            "memory_id": memory_id,
            "timestamp": time.time(),
            "metadata": metadata or {}
        }
        self.events.append(event)

    def get_recent_activity(self, hours: int = 24) -> List[Dict[str, Any]]:
        """获取最近活动"""
        cutoff = time.time() - (hours * 3600)
        return [e for e in self.events if e["timestamp"] >= cutoff]

    def get_activity_by_type(self, event_type: str) -> List[Dict[str, Any]]:
        """按类型获取活动"""
        return [e for e in self.events if e["type"] == event_type]

    def get_hourly_stats(self, hours: int = 24) -> Dict[int, int]:
        """获取小时统计"""
        cutoff = time.time() - (hours * 3600)
        hourly_counts = defaultdict(int)

        for event in self.events:
            if event["timestamp"] >= cutoff:
                hour = datetime.fromtimestamp(event["timestamp"]).hour
                hourly_counts[hour] += 1

        return dict(hourly_counts)

    def get_daily_stats(self, days: int = 7) -> Dict[str, int]:
        """获取每日统计"""
        cutoff = time.time() - (days * 86400)
        daily_counts = defaultdict(int)

        for event in self.events:
            if event["timestamp"] >= cutoff:
                date = datetime.fromtimestamp(event["timestamp"]).strftime("%Y-%m-%d")
                daily_counts[date] += 1

        return dict(sorted(daily_counts.items()))

    def analyze_productivity(self, days: int = 7) -> Dict[str, Any]:
        """分析生产力"""
        daily_stats = self.get_daily_stats(days)

        if not daily_stats:
            return {
                "avg_daily_activity": 0,
                "most_active_day": None,
                "least_active_day": None,
                "trend": "no_data"
            }

        values = list(daily_stats.values())
        avg_daily = sum(values) / len(values)

        most_active = max(daily_stats.items(), key=lambda x: x[1])
        least_active = min(daily_stats.items(), key=lambda x: x[1])

        trend_info = self.trend_analyzer.calculate_growth_rate(values)

        return {
            "avg_daily_activity": avg_daily,
            "most_active_day": most_active[0],
            "most_active_count": most_active[1],
            "least_active_day": least_active[0],
            "least_active_count": least_active[1],
            "trend": trend_info["trend"],
            "growth_rate": trend_info["growth_rate"],
            "daily_breakdown": daily_stats
        }


class EnhancedMemoryWithAnalytics:
    """
    增强的记忆系统（带统计分析功能）
    装饰器模式实现
    """

    def __init__(self, memory_system):
        self.memory_system = memory_system
        self.dashboard = MemoryDashboard(memory_system)
        self.activity_tracker = ActivityTracker()

    def collect_stats(self) -> Dict[str, Any]:
        """收集统计信息"""
        return self.dashboard.collect_statistics()

    def get_dashboard(self) -> Dict[str, Any]:
        """获取仪表盘数据"""
        return self.dashboard.get_detailed_stats()

    def generate_report(self) -> str:
        """生成统计报告"""
        return self.dashboard.generate_report()

    def track_activity(self, event_type: str, memory_id: str, metadata: Optional[Dict[str, Any]] = None):
        """追踪活动"""
        self.activity_tracker.track_event(event_type, memory_id, metadata)

    def get_recent_activity(self, hours: int = 24) -> List[Dict[str, Any]]:
        """获取最近活动"""
        return self.activity_tracker.get_recent_activity(hours)

    def analyze_productivity(self, days: int = 7) -> Dict[str, Any]:
        """分析生产力"""
        return self.activity_tracker.analyze_productivity(days)

    def export_analytics(self, format: str = "dict") -> Any:
        """导出分析数据"""
        return {
            "dashboard": self.dashboard.export_statistics(format),
            "productivity": self.activity_tracker.analyze_productivity(),
            "activity": {
                "recent_24h": len(self.activity_tracker.get_recent_activity(24)),
                "recent_7d": len(self.activity_tracker.get_recent_activity(168))
            }
        }
