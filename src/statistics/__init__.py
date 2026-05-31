"""
记忆系统统计与报告系统
基于第一性原理：数据驱动决策、清晰可视化、持续优化
"""
import time
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class ReportType(Enum):
    """报告类型"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class StatisticType(Enum):
    """统计类型"""
    MEMORY_USAGE = "memory_usage"
    OPERATION_STATS = "operation_stats"
    SESSION_STATS = "session_stats"
    PERFORMANCE_STATS = "performance_stats"


@dataclass
class MemoryStatistic:
    """记忆统计"""
    level: str
    count: int
    size_bytes: int
    growth_rate: float = 0.0
    last_update: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OperationStatistic:
    """操作统计"""
    operation: str
    total_count: int
    success_count: int
    failure_count: int
    avg_duration: float = 0.0
    min_duration: float = 0.0
    max_duration: float = 0.0
    success_rate: float = 0.0


@dataclass
class SystemReport:
    """系统报告"""
    report_id: str
    report_type: ReportType
    generated_at: float
    period_start: float
    period_end: float
    memory_stats: Dict[str, Any]
    operation_stats: Dict[str, Any]
    session_stats: Dict[str, Any]
    trends: Dict[str, Any]
    insights: List[str]
    recommendations: List[str]
    summary: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class StatisticsCollector:
    """统计收集器"""

    def __init__(self):
        self._memory_operations: List[Dict[str, Any]] = []
        self._session_data: Dict[str, List[Dict]] = defaultdict(list)
        self._operation_counts: Counter = Counter()
        self._operation_durations: Dict[str, List[float]] = defaultdict(list)
        self._memory_growth: List[Tuple[float, int]] = []
        self._max_history = 10000

    def record_operation(
        self,
        operation: str,
        success: bool = True,
        duration: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """记录操作"""
        record = {
            "operation": operation,
            "success": success,
            "duration": duration,
            "timestamp": time.time(),
            "metadata": metadata or {}
        }
        self._memory_operations.append(record)

        # 更新操作计数
        status = "success" if success else "failure"
        self._operation_counts[f"{operation}_{status}"] += 1

        # 记录持续时间
        if duration > 0:
            self._operation_durations[operation].append(duration)

        # 限制历史大小
        if len(self._memory_operations) > self._max_history:
            self._memory_operations.pop(0)

    def record_session_activity(
        self,
        session_id: str,
        activity_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """记录会话活动"""
        record = {
            "activity_type": activity_type,
            "timestamp": time.time(),
            "metadata": metadata or {}
        }
        self._session_data[session_id].append(record)

    def record_memory_growth(self, level: str, count: int) -> None:
        """记录记忆增长"""
        self._memory_growth.append((time.time(), count))

        # 限制历史大小
        if len(self._memory_growth) > self._max_history:
            self._memory_growth.pop(0)

    def get_operation_stats(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """获取操作统计"""
        if operation:
            success_count = self._operation_counts.get(f"{operation}_success", 0)
            failure_count = self._operation_counts.get(f"{operation}_failure", 0)
            total = success_count + failure_count

            durations = self._operation_durations.get(operation, [])
            avg_duration = sum(durations) / len(durations) if durations else 0
            min_duration = min(durations) if durations else 0
            max_duration = max(durations) if durations else 0

            return {
                "operation": operation,
                "total_count": total,
                "success_count": success_count,
                "failure_count": failure_count,
                "success_rate": success_count / total if total > 0 else 0,
                "avg_duration": avg_duration,
                "min_duration": min_duration,
                "max_duration": max_duration
            }

        # 返回所有操作统计
        all_stats = {}
        operations = set()
        for key in self._operation_counts.keys():
            op = key.rsplit("_", 1)[0]
            operations.add(op)

        for op in operations:
            all_stats[op] = self.get_operation_stats(op)

        return all_stats

    def get_session_stats(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """获取会话统计"""
        if session_id:
            activities = self._session_data.get(session_id, [])
            activity_types = Counter(a["activity_type"] for a in activities)

            return {
                "session_id": session_id,
                "total_activities": len(activities),
                "activity_breakdown": dict(activity_types),
                "first_activity": activities[0]["timestamp"] if activities else None,
                "last_activity": activities[-1]["timestamp"] if activities else None
            }

        # 返回所有会话统计
        return {
            "total_sessions": len(self._session_data),
            "sessions": {
                sid: self.get_session_stats(sid)
                for sid in self._session_data.keys()
            }
        }

    def get_memory_growth_stats(self) -> Dict[str, Any]:
        """获取记忆增长统计"""
        if len(self._memory_growth) < 2:
            return {
                "total_records": len(self._memory_growth),
                "current_count": self._memory_growth[-1][1] if self._memory_growth else 0,
                "growth_rate": 0.0
            }

        # 计算增长率
        first = self._memory_growth[0]
        last = self._memory_growth[-1]
        time_diff = last[0] - first[0]
        count_diff = last[1] - first[1]

        growth_rate = (count_diff / time_diff) if time_diff > 0 else 0

        return {
            "total_records": len(self._memory_growth),
            "first_count": first[1],
            "last_count": last[1],
            "current_count": last[1],
            "growth_rate": growth_rate,
            "total_growth": count_diff,
            "time_span_seconds": time_diff
        }

    def get_recent_operations(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取最近操作"""
        return self._memory_operations[-limit:]

    def reset(self) -> None:
        """重置统计"""
        self._memory_operations.clear()
        self._session_data.clear()
        self._operation_counts.clear()
        self._operation_durations.clear()
        self._memory_growth.clear()


class TrendAnalyzer:
    """趋势分析器"""

    def __init__(self, statistics_collector: StatisticsCollector):
        self.collector = statistics_collector

    def analyze_memory_trends(self, period_days: int = 7) -> Dict[str, Any]:
        """分析记忆趋势"""
        growth_stats = self.collector.get_memory_growth_stats()

        # 计算日均增长
        time_span_days = growth_stats.get("time_span_seconds", 0) / 86400
        daily_avg = growth_stats.get("total_growth", 0) / time_span_days if time_span_days > 0 else 0

        # 趋势判断
        if daily_avg > 10:
            trend = "rapid_growth"
            trend_desc = "快速增长"
        elif daily_avg > 0:
            trend = "steady_growth"
            trend_desc = "稳定增长"
        elif daily_avg < 0:
            trend = "decline"
            trend_desc = "下降"
        else:
            trend = "stable"
            trend_desc = "稳定"

        return {
            "trend": trend,
            "trend_description": trend_desc,
            "daily_average": daily_avg,
            "growth_rate": growth_stats.get("growth_rate", 0),
            "total_growth": growth_stats.get("total_growth", 0),
            "projection_7_days": growth_stats.get("current_count", 0) + (daily_avg * 7)
        }

    def analyze_operation_trends(self) -> Dict[str, Any]:
        """分析操作趋势"""
        op_stats = self.collector.get_operation_stats()

        # 找出最频繁的操作
        most_active = sorted(
            op_stats.items(),
            key=lambda x: x[1].get("total_count", 0),
            reverse=True
        )[:5]

        # 找出成功率最低的操作
        lowest_success = sorted(
            op_stats.items(),
            key=lambda x: x[1].get("success_rate", 0)
        )[:3]

        return {
            "most_active_operations": [
                {"operation": op, "count": stats["total_count"]}
                for op, stats in most_active
            ],
            "lowest_success_rate": [
                {"operation": op, "rate": stats["success_rate"]}
                for op, stats in lowest_success
            ],
            "total_operations": sum(stats["total_count"] for _, stats in op_stats.items()),
            "overall_success_rate": sum(stats["success_count"] for _, stats in op_stats.items()) /
                                   max(sum(stats["total_count"] for _, stats in op_stats.items()), 1)
        }

    def analyze_session_trends(self) -> Dict[str, Any]:
        """分析会话趋势"""
        session_stats = self.collector.get_session_stats()

        return {
            "total_sessions": session_stats.get("total_sessions", 0),
            "active_sessions": len([
                sid for sid, stats in session_stats.get("sessions", {}).items()
                if stats.get("total_activities", 0) > 0
            ])
        }


class ReportGenerator:
    """报告生成器"""

    def __init__(self, statistics_collector: StatisticsCollector):
        self.collector = statistics_collector
        self.trend_analyzer = TrendAnalyzer(statistics_collector)

    def generate_report(
        self,
        report_type: ReportType = ReportType.WEEKLY,
        period_start: Optional[float] = None,
        period_end: Optional[float] = None
    ) -> SystemReport:
        """生成系统报告"""
        now = time.time()

        # 确定时间段
        if period_start is None:
            if report_type == ReportType.DAILY:
                period_start = now - 86400
            elif report_type == ReportType.WEEKLY:
                period_start = now - 86400 * 7
            elif report_type == ReportType.MONTHLY:
                period_start = now - 86400 * 30
            else:
                period_start = now - 86400 * 7

        if period_end is None:
            period_end = now

        # 收集统计
        memory_stats = self._collect_memory_stats()
        operation_stats = self._collect_operation_stats()
        session_stats = self._collect_session_stats()

        # 分析趋势
        memory_trends = self.trend_analyzer.analyze_memory_trends()
        operation_trends = self.trend_analyzer.analyze_operation_trends()
        session_trends = self.trend_analyzer.analyze_session_trends()

        trends = {
            "memory": memory_trends,
            "operations": operation_trends,
            "sessions": session_trends
        }

        # 生成洞察
        insights = self._generate_insights(memory_trends, operation_trends, session_trends)

        # 生成建议
        recommendations = self._generate_recommendations(memory_trends, operation_trends, session_trends)

        # 生成摘要
        summary = self._generate_summary(report_type, memory_trends, operation_trends, session_trends)

        return SystemReport(
            report_id=f"report_{int(now * 1000)}",
            report_type=report_type,
            generated_at=now,
            period_start=period_start,
            period_end=period_end,
            memory_stats=memory_stats,
            operation_stats=operation_stats,
            session_stats=session_stats,
            trends=trends,
            insights=insights,
            recommendations=recommendations,
            summary=summary
        )

    def _collect_memory_stats(self) -> Dict[str, Any]:
        """收集记忆统计"""
        growth_stats = self.collector.get_memory_growth_stats()

        return {
            "current_count": growth_stats.get("current_count", 0),
            "total_growth": growth_stats.get("total_growth", 0),
            "growth_rate": growth_stats.get("growth_rate", 0),
            "total_records": growth_stats.get("total_records", 0)
        }

    def _collect_operation_stats(self) -> Dict[str, Any]:
        """收集操作统计"""
        return self.collector.get_operation_stats()

    def _collect_session_stats(self) -> Dict[str, Any]:
        """收集会话统计"""
        return self.collector.get_session_stats()

    def _generate_insights(
        self,
        memory_trends: Dict[str, Any],
        operation_trends: Dict[str, Any],
        session_trends: Dict[str, Any]
    ) -> List[str]:
        """生成洞察"""
        insights = []

        # 记忆洞察
        if memory_trends["trend"] == "rapid_growth":
            insights.append(f"记忆数量增长迅速，日均增长 {memory_trends['daily_average']:.1f} 条")
        elif memory_trends["trend"] == "steady_growth":
            insights.append(f"记忆数量稳步增长，日均增长 {memory_trends['daily_average']:.1f} 条")

        # 操作洞察
        total_ops = operation_trends.get("total_operations", 0)
        if total_ops > 1000:
            insights.append(f"系统活跃度高，共执行 {total_ops} 次操作")
        elif total_ops > 100:
            insights.append(f"系统运行正常，执行 {total_ops} 次操作")

        # 会话洞察
        total_sessions = session_trends.get("total_sessions", 0)
        if total_sessions > 10:
            insights.append(f"多会话运行活跃，共 {total_sessions} 个会话")

        if not insights:
            insights.append("系统运行正常，各项指标稳定")

        return insights

    def _generate_recommendations(
        self,
        memory_trends: Dict[str, Any],
        operation_trends: Dict[str, Any],
        session_trends: Dict[str, Any]
    ) -> List[str]:
        """生成建议"""
        recommendations = []

        # 记忆建议
        if memory_trends["trend"] == "rapid_growth":
            recommendations.append("建议定期清理不再需要的记忆，避免存储压力")
            recommendations.append("考虑启用自动归档策略，将旧记忆归档到L3")

        # 操作建议
        lowest_success = operation_trends.get("lowest_success_rate", [])
        for item in lowest_success:
            if item["rate"] < 0.8:
                recommendations.append(f"注意：'{item['operation']}' 操作成功率较低 ({item['rate']*100:.1f}%)，建议检查")

        # 会话建议
        total_sessions = session_trends.get("total_sessions", 0)
        if total_sessions > 50:
            recommendations.append("会话数量较多，建议定期清理过期会话")

        if not recommendations:
            recommendations.append("继续保持当前的良好使用习惯")

        return recommendations

    def _generate_summary(
        self,
        report_type: ReportType,
        memory_trends: Dict[str, Any],
        operation_trends: Dict[str, Any],
        session_trends: Dict[str, Any]
    ) -> str:
        """生成摘要"""
        period_map = {
            ReportType.DAILY: "今日",
            ReportType.WEEKLY: "本周",
            ReportType.MONTHLY: "本月",
            ReportType.CUSTOM: "当前"
        }

        period = period_map.get(report_type, "当前")

        summary_parts = [
            f"{period}记忆系统运行报告",
            f"记忆总数：{memory_trends.get('current_count', 0)}，较上周期{'增加' if memory_trends.get('total_growth', 0) > 0 else '减少'} {abs(memory_trends.get('total_growth', 0))} 条",
            f"操作总数：{operation_trends.get('total_operations', 0)}，成功率 {operation_trends.get('overall_success_rate', 0)*100:.1f}%",
            f"会话数：{session_trends.get('total_sessions', 0)}"
        ]

        return " | ".join(summary_parts)

    def export_report_json(self, report: SystemReport) -> str:
        """导出报告为JSON"""
        return json.dumps({
            "report_id": report.report_id,
            "report_type": report.report_type.value,
            "generated_at": report.generated_at,
            "period": {
                "start": report.period_start,
                "end": report.period_end
            },
            "memory_stats": report.memory_stats,
            "operation_stats": report.operation_stats,
            "session_stats": report.session_stats,
            "trends": report.trends,
            "insights": report.insights,
            "recommendations": report.recommendations,
            "summary": report.summary
        }, ensure_ascii=False, indent=2)

    def export_report_text(self, report: SystemReport) -> str:
        """导出报告为文本"""
        lines = [
            "=" * 60,
            f"记忆系统 {report.report_type.value.upper()} 报告",
            "=" * 60,
            f"报告ID: {report.report_id}",
            f"生成时间: {datetime.fromtimestamp(report.generated_at).isoformat()}",
            f"时间段: {datetime.fromtimestamp(report.period_start).isoformat()} - {datetime.fromtimestamp(report.period_end).isoformat()}",
            "",
            "【摘要】",
            report.summary,
            "",
            "【记忆统计】",
            f"  当前数量: {report.memory_stats.get('current_count', 0)}",
            f"  总增长: {report.memory_stats.get('total_growth', 0)}",
            f"  增长率: {report.memory_stats.get('growth_rate', 0):.4f}",
            "",
            "【趋势分析】",
            f"  记忆趋势: {report.trends['memory']['trend_description']}",
            f"  日均增长: {report.trends['memory']['daily_average']:.2f}",
            "",
            "【洞察】",
        ]

        for i, insight in enumerate(report.insights, 1):
            lines.append(f"  {i}. {insight}")

        lines.extend([
            "",
            "【建议】",
        ])

        for i, rec in enumerate(report.recommendations, 1):
            lines.append(f"  {i}. {rec}")

        lines.extend([
            "",
            "=" * 60,
            f"总操作数: {report.operation_stats.get('add', {}).get('total_count', 0) + report.operation_stats.get('recall', {}).get('total_count', 0)}" if isinstance(report.operation_stats, dict) else "",
            "=" * 60
        ])

        return "\n".join(lines)


# 全局单例
_global_statistics_collector: Optional[StatisticsCollector] = None
_global_report_generator: Optional[ReportGenerator] = None


def get_statistics_collector() -> StatisticsCollector:
    """获取统计收集器单例"""
    global _global_statistics_collector
    if _global_statistics_collector is None:
        _global_statistics_collector = StatisticsCollector()
    return _global_statistics_collector


def get_report_generator() -> ReportGenerator:
    """获取报告生成器单例"""
    global _global_report_generator
    if _global_report_generator is None:
        collector = get_statistics_collector()
        _global_report_generator = ReportGenerator(collector)
    return _global_report_generator
