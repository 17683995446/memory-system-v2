"""
性能报告生成器
用于生成详细的性能报告
"""

import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json


class PerformanceReportGenerator:
    """性能报告生成器"""
    
    def __init__(self, monitor, analyzer):
        self.monitor = monitor
        self.analyzer = analyzer
        self._report_history: List[Dict[str, Any]] = []
    
    def generate_summary_report(self) -> str:
        """生成摘要报告"""
        summary = self.monitor.get_performance_summary()
        analysis = self.analyzer.analyze_current_performance()
        
        report = []
        report.append("=" * 70)
        report.append("性能摘要报告")
        report.append("=" * 70)
        
        report.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"总体健康度: {analysis.overall_health.upper()}")
        
        report.append("\n系统状态:")
        report.append(f"  CPU使用率: {summary['latest']['cpu_percent']:.2f}%")
        report.append(f"  内存使用率: {summary['latest']['memory_percent']:.2f}%")
        report.append(f"  线程数: {summary['latest']['thread_count']}")
        report.append(f"  活跃连接: {summary['latest']['active_connections']}")
        
        report.append("\n最近10次平均:")
        report.append(f"  CPU使用率: {summary['average_10']['cpu_percent']:.2f}%")
        report.append(f"  内存使用率: {summary['average_10']['memory_percent']:.2f}%")
        
        report.append("\n监控统计:")
        report.append(f"  总指标数: {summary['metrics_count']}")
        report.append(f"  活跃告警: {summary['active_alerts']}")
        
        report.append("\n" + "=" * 70)
        return "\n".join(report)
    
    def generate_detailed_report(self) -> str:
        """生成详细报告"""
        analysis = self.analyzer.analyze_current_performance()
        
        report = []
        report.append("=" * 70)
        report.append("详细性能报告")
        report.append("=" * 70)
        
        report.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"总体健康度: {analysis.overall_health.upper()}")
        
        report.append("\n性能趋势:")
        for trend in analysis.trends:
            report.append(f"  {trend.metric_name}:")
            report.append(f"    趋势: {trend.trend} ({trend.change_percent:+.1f}%)")
            report.append(f"    平均: {trend.avg_value:.2f}")
            report.append(f"    范围: {trend.min_value:.2f} - {trend.max_value:.2f}")
        
        report.append("\n活跃告警:")
        active_alerts = self.monitor.get_active_alerts()
        if active_alerts:
            for alert in active_alerts:
                report.append(f"  [{alert.severity.upper()}] {alert.metric_name}")
                report.append(f"    消息: {alert.message}")
                report.append(f"    时间: {alert.timestamp}")
        else:
            report.append("  无活跃告警")
        
        report.append("\n建议:")
        for i, rec in enumerate(analysis.recommendations, 1):
            report.append(f"  {i}. {rec}")
        
        report.append("\n最近快照:")
        if self.monitor.snapshots:
            latest = self.monitor.snapshots[-1]
            report.append(f"  CPU: {latest.cpu_percent:.2f}%")
            report.append(f"  内存: {latest.memory_percent:.2f}% ({latest.memory_used_mb:.2f}MB)")
            report.append(f"  线程: {latest.thread_count}")
            report.append(f"  连接: {latest.active_connections}")
        
        report.append("\n" + "=" * 70)
        return "\n".join(report)
    
    def generate_json_report(self) -> str:
        """生成JSON格式报告"""
        summary = self.monitor.get_performance_summary()
        analysis = self.analyzer.analyze_current_performance()
        
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "overall_health": analysis.overall_health,
            "metrics_count": summary["metrics_count"],
            "active_alerts": summary["active_alerts"],
            "latest": summary["latest"],
            "average_10": summary["average_10"],
            "trends": [
                {
                    "metric_name": t.metric_name,
                    "trend": t.trend,
                    "change_percent": t.change_percent,
                    "avg_value": t.avg_value,
                    "min_value": t.min_value,
                    "max_value": t.max_value
                }
                for t in analysis.trends
            ],
            "recommendations": analysis.recommendations
        }
        
        return json.dumps(report_data, indent=2, ensure_ascii=False)
    
    def generate_trend_report(self, hours: int = 24) -> str:
        """生成趋势报告"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        analysis = self.analyzer.analyze_performance_window(start_time, end_time)
        
        report = []
        report.append("=" * 70)
        report.append(f"性能趋势报告 (过去{hours}小时)")
        report.append("=" * 70)
        
        report.append(f"\n时间范围: {start_time} 至 {end_time}")
        report.append(f"样本数量: {analysis.get('sample_count', 0)}")
        
        if "error" not in analysis:
            report.append("\nCPU统计:")
            report.append(f"  平均: {analysis['cpu']['avg']:.2f}%")
            report.append(f"  最小: {analysis['cpu']['min']:.2f}%")
            report.append(f"  最大: {analysis['cpu']['max']:.2f}%")
            
            report.append("\n内存统计:")
            report.append(f"  平均: {analysis['memory']['avg']:.2f}%")
            report.append(f"  最小: {analysis['memory']['min']:.2f}%")
            report.append(f"  最大: {analysis['memory']['max']:.2f}%")
            
            report.append("\n线程统计:")
            report.append(f"  平均: {analysis['threads']['avg']:.2f}")
            report.append(f"  最小: {analysis['threads']['min']:.2f}")
            report.append(f"  最大: {analysis['threads']['max']:.2f}")
        else:
            report.append(f"\n错误: {analysis['error']}")
        
        report.append("\n" + "=" * 70)
        return "\n".join(report)
    
    def save_report(self, report_type: str = "summary") -> str:
        """保存报告到历史"""
        if report_type == "summary":
            report = self.generate_summary_report()
        elif report_type == "detailed":
            report = self.generate_detailed_report()
        elif report_type == "json":
            report = self.generate_json_report()
        elif report_type == "trend":
            report = self.generate_trend_report()
        else:
            report = self.generate_summary_report()
        
        report_data = {
            "timestamp": datetime.now(),
            "type": report_type,
            "report": report
        }
        
        self._report_history.append(report_data)
        
        return report
    
    def get_report_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取报告历史"""
        return self._report_history[-limit:]
    
    def export_to_json_file(self, filename: str) -> bool:
        """导出报告到JSON文件"""
        try:
            report = self.generate_json_report()
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
            return True
        except Exception:
            return False
    
    def create_comparison_report(
        self,
        period1_name: str,
        period1_hours: int,
        period2_name: str,
        period2_hours: int
    ) -> str:
        """创建对比报告"""
        now = datetime.now()
        
        p1_end = now
        p1_start = now - timedelta(hours=period1_hours)
        
        p2_end = p1_start - timedelta(hours=1)
        p2_start = p2_end - timedelta(hours=period2_hours)
        
        analysis1 = self.analyzer.analyze_performance_window(p1_start, p1_end)
        analysis2 = self.analyzer.analyze_performance_window(p2_start, p2_end)
        
        report = []
        report.append("=" * 70)
        report.append("性能对比报告")
        report.append("=" * 70)
        
        report.append(f"\n对比时间段:")
        report.append(f"  周期1 ({period1_name}): {p1_start} 至 {p1_end}")
        report.append(f"  周期2 ({period2_name}): {p2_start} 至 {p2_end}")
        
        if "error" not in analysis1 and "error" not in analysis2:
            report.append("\nCPU对比:")
            cpu_diff = analysis1["cpu"]["avg"] - analysis2["cpu"]["avg"]
            report.append(f"  {period1_name}平均: {analysis1['cpu']['avg']:.2f}%")
            report.append(f"  {period2_name}平均: {analysis2['cpu']['avg']:.2f}%")
            report.append(f"  差异: {cpu_diff:+.2f}%")
            
            report.append("\n内存对比:")
            mem_diff = analysis1["memory"]["avg"] - analysis2["memory"]["avg"]
            report.append(f"  {period1_name}平均: {analysis1['memory']['avg']:.2f}%")
            report.append(f"  {period2_name}平均: {analysis2['memory']['avg']:.2f}%")
            report.append(f"  差异: {mem_diff:+.2f}%")
            
            report.append("\n线程对比:")
            thread_diff = analysis1["threads"]["avg"] - analysis2["threads"]["avg"]
            report.append(f"  {period1_name}平均: {analysis1['threads']['avg']:.2f}")
            report.append(f"  {period2_name}平均: {analysis2['threads']['avg']:.2f}")
            report.append(f"  差异: {thread_diff:+.2f}")
        else:
            report.append("\n错误: 无法完成对比分析")
        
        report.append("\n" + "=" * 70)
        return "\n".join(report)
