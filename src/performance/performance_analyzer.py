"""
性能分析器
用于分析性能数据和生成报告
"""

import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class PerformanceTrend:
    """性能趋势"""
    metric_name: str
    trend: str
    change_percent: float
    avg_value: float
    min_value: float
    max_value: float


@dataclass
class PerformanceAnalysis:
    """性能分析结果"""
    timestamp: datetime
    overall_health: str
    metrics_analyzed: int
    alerts_triggered: int
    trends: List[PerformanceTrend]
    recommendations: List[str]


class PerformanceAnalyzer:
    """性能分析器"""
    
    def __init__(self, monitor):
        self.monitor = monitor
        self._history: List[Dict[str, Any]] = []
    
    def analyze_current_performance(self) -> PerformanceAnalysis:
        """分析当前性能"""
        summary = self.monitor.get_performance_summary()
        snapshots = self.monitor.snapshots
        
        if not snapshots:
            return PerformanceAnalysis(
                timestamp=datetime.now(),
                overall_health="unknown",
                metrics_analyzed=0,
                alerts_triggered=0,
                trends=[],
                recommendations=["No performance data available"]
            )
        
        latest = snapshots[-1]
        overall_health = self._calculate_health(latest)
        trends = self._calculate_trends(snapshots)
        recommendations = self._generate_recommendations(latest, trends)
        
        return PerformanceAnalysis(
            timestamp=datetime.now(),
            overall_health=overall_health,
            metrics_analyzed=len(self.monitor.metrics),
            alerts_triggered=len(self.monitor.get_active_alerts()),
            trends=trends,
            recommendations=recommendations
        )
    
    def _calculate_health(self, snapshot) -> str:
        """计算健康度"""
        score = 0
        
        if snapshot.cpu_percent < 50:
            score += 25
        elif snapshot.cpu_percent < 70:
            score += 20
        elif snapshot.cpu_percent < 85:
            score += 10
        else:
            score += 0
        
        if snapshot.memory_percent < 50:
            score += 25
        elif snapshot.memory_percent < 70:
            score += 20
        elif snapshot.memory_percent < 85:
            score += 10
        else:
            score += 0
        
        if snapshot.thread_count < 50:
            score += 25
        elif snapshot.thread_count < 100:
            score += 20
        elif snapshot.thread_count < 200:
            score += 10
        else:
            score += 0
        
        active_alerts = len(self.monitor.get_active_alerts())
        if active_alerts == 0:
            score += 25
        elif active_alerts < 3:
            score += 15
        elif active_alerts < 5:
            score += 5
        else:
            score += 0
        
        if score >= 90:
            return "excellent"
        elif score >= 70:
            return "good"
        elif score >= 50:
            return "fair"
        elif score >= 25:
            return "poor"
        else:
            return "critical"
    
    def _calculate_trends(self, snapshots: List) -> List[PerformanceTrend]:
        """计算性能趋势"""
        if len(snapshots) < 2:
            return []
        
        trends = []
        
        cpu_values = [s.cpu_percent for s in snapshots[-10:]]
        memory_values = [s.memory_percent for s in snapshots[-10:]]
        
        if cpu_values:
            cpu_trend = self._analyze_trend(cpu_values, "cpu_usage")
            trends.append(cpu_trend)
        
        if memory_values:
            memory_trend = self._analyze_trend(memory_values, "memory_usage")
            trends.append(memory_trend)
        
        return trends
    
    def _analyze_trend(self, values: List[float], name: str) -> PerformanceTrend:
        """分析单个指标的趋势"""
        if len(values) < 2:
            return PerformanceTrend(
                metric_name=name,
                trend="stable",
                change_percent=0.0,
                avg_value=sum(values) / len(values),
                min_value=values[0] if values else 0,
                max_value=values[-1] if values else 0
            )
        
        first = values[0]
        last = values[-1]
        
        if first == 0:
            change_percent = 0.0
        else:
            change_percent = ((last - first) / first) * 100
        
        if change_percent > 10:
            trend = "increasing"
        elif change_percent < -10:
            trend = "decreasing"
        else:
            trend = "stable"
        
        return PerformanceTrend(
            metric_name=name,
            trend=trend,
            change_percent=change_percent,
            avg_value=sum(values) / len(values),
            min_value=min(values),
            max_value=max(values)
        )
    
    def _generate_recommendations(
        self,
        snapshot,
        trends: List[PerformanceTrend]
    ) -> List[str]:
        """生成建议"""
        recommendations = []
        
        if snapshot.cpu_percent > 80:
            recommendations.append("CPU使用率过高，建议优化计算密集型任务或扩展计算资源")
        
        if snapshot.memory_percent > 80:
            recommendations.append("内存使用率过高，建议增加内存或优化内存使用")
        
        for trend in trends:
            if trend.trend == "increasing" and trend.change_percent > 20:
                if trend.metric_name == "cpu_usage":
                    recommendations.append(f"CPU使用率持续上升({trend.change_percent:.1f}%)，建议立即关注")
                elif trend.metric_name == "memory_usage":
                    recommendations.append(f"内存使用率持续上升({trend.change_percent:.1f}%)，可能存在内存泄漏")
        
        if snapshot.thread_count > 200:
            recommendations.append("线程数过多，建议优化线程管理或使用线程池")
        
        active_alerts = len(self.monitor.get_active_alerts())
        if active_alerts > 5:
            recommendations.append(f"存在{active_alerts}个活跃告警，建议尽快处理")
        
        if not recommendations:
            recommendations.append("系统性能良好，无需特殊处理")
        
        return recommendations
    
    def analyze_performance_window(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """分析特定时间窗口的性能"""
        snapshots = [
            s for s in self.monitor.snapshots
            if start_time <= s.timestamp <= end_time
        ]
        
        if not snapshots:
            return {"error": "No data in specified time window"}
        
        cpu_values = [s.cpu_percent for s in snapshots]
        memory_values = [s.memory_percent for s in snapshots]
        thread_values = [s.thread_count for s in snapshots]
        
        return {
            "time_window": {
                "start": start_time,
                "end": end_time
            },
            "sample_count": len(snapshots),
            "cpu": {
                "avg": sum(cpu_values) / len(cpu_values),
                "min": min(cpu_values),
                "max": max(cpu_values)
            },
            "memory": {
                "avg": sum(memory_values) / len(memory_values),
                "min": min(memory_values),
                "max": max(memory_values)
            },
            "threads": {
                "avg": sum(thread_values) / len(thread_values),
                "min": min(thread_values),
                "max": max(thread_values)
            }
        }
    
    def generate_performance_report(self) -> str:
        """生成性能报告"""
        analysis = self.analyze_current_performance()
        
        report = []
        report.append("=" * 70)
        report.append("性能分析报告")
        report.append("=" * 70)
        
        report.append(f"\n生成时间: {analysis.timestamp}")
        report.append(f"总体健康度: {analysis.overall_health.upper()}")
        report.append(f"分析指标数: {analysis.metrics_analyzed}")
        report.append(f"活跃告警数: {analysis.alerts_triggered}")
        
        if analysis.trends:
            report.append("\n性能趋势:")
            for trend in analysis.trends:
                report.append(f"  {trend.metric_name}:")
                report.append(f"    趋势: {trend.trend}")
                report.append(f"    变化: {trend.change_percent:+.1f}%")
                report.append(f"    平均值: {trend.avg_value:.2f}")
                report.append(f"    范围: {trend.min_value:.2f} - {trend.max_value:.2f}")
        
        if analysis.recommendations:
            report.append("\n建议:")
            for i, rec in enumerate(analysis.recommendations, 1):
                report.append(f"  {i}. {rec}")
        
        report.append("\n" + "=" * 70)
        return "\n".join(report)
    
    def compare_time_windows(
        self,
        window1_start: datetime,
        window1_end: datetime,
        window2_start: datetime,
        window2_end: datetime
    ) -> Dict[str, Any]:
        """比较两个时间窗口的性能"""
        analysis1 = self.analyze_performance_window(window1_start, window1_end)
        analysis2 = self.analyze_performance_window(window2_start, window2_end)
        
        if "error" in analysis1 or "error" in analysis2:
            return {"error": "Unable to compare time windows"}
        
        return {
            "window1": analysis1,
            "window2": analysis2,
            "comparison": {
                "cpu_change": analysis2["cpu"]["avg"] - analysis1["cpu"]["avg"],
                "memory_change": analysis2["memory"]["avg"] - analysis1["memory"]["avg"],
                "thread_change": analysis2["threads"]["avg"] - analysis1["threads"]["avg"]
            }
        }
