"""
BUG追踪与管理系统
"""
import time
from typing import Dict, List
from dataclasses import dataclass, field
from enum import Enum


class BugSeverity(Enum):
    """严重级别"""
    CRITICAL = "critical"   # 致命
    HIGH = "high"          # 高
    MEDIUM = "medium"      # 中
    LOW = "low"            # 低


class BugStatus(Enum):
    """状态"""
    OPEN = "open"          # 打开
    IN_PROGRESS = "in_progress"  # 进行中
    RESOLVED = "resolved"   # 已解决
    CLOSED = "closed"      # 已关闭
    WONT_FIX = "wont_fix"  # 不会修复


@dataclass
class Bug:
    """BUG记录"""
    bug_id: str
    title: str
    description: str
    severity: BugSeverity
    status: BugStatus
    module: str
    created_at: float
    updated_at: float
    resolved_at: float = None
    assigned_to: str = ""
    steps_to_reproduce: List[str] = field(default_factory=list)
    expected_result: str = ""
    actual_result: str = ""
    fix_note: str = ""


class BugTracker:
    """BUG追踪器"""
    
    def __init__(self):
        self._bugs: Dict[str, Bug] = {}
        self._bug_counter = 0
    
    def create_bug(
        self,
        title: str,
        description: str,
        severity: BugSeverity,
        module: str,
        steps_to_reproduce: List[str] = None,
        expected: str = "",
        actual: str = ""
    ) -> str:
        """创建BUG"""
        self._bug_counter += 1
        bug_id = f"BUG-{self._bug_counter:04d}"
        
        bug = Bug(
            bug_id=bug_id,
            title=title,
            description=description,
            severity=severity,
            status=BugStatus.OPEN,
            module=module,
            created_at=time.time(),
            updated_at=time.time(),
            steps_to_reproduce=steps_to_reproduce or [],
            expected_result=expected,
            actual_result=actual
        )
        
        self._bugs[bug_id] = bug
        return bug_id
    
    def update_bug(
        self,
        bug_id: str,
        status: BugStatus = None,
        assigned_to: str = None,
        fix_note: str = None
    ) -> bool:
        """更新BUG"""
        if bug_id not in self._bugs:
            return False
        
        bug = self._bugs[bug_id]
        
        if status:
            bug.status = status
            if status == BugStatus.RESOLVED:
                bug.resolved_at = time.time()
        
        if assigned_to:
            bug.assigned_to = assigned_to
        
        if fix_note:
            bug.fix_note = fix_note
        
        bug.updated_at = time.time()
        return True
    
    def get_bug(self, bug_id: str) -> Bug:
        """获取BUG"""
        return self._bugs.get(bug_id)
    
    def get_bugs_by_status(self, status: BugStatus) -> List[Bug]:
        """按状态获取BUG"""
        return [b for b in self._bugs.values() if b.status == status]
    
    def get_bugs_by_severity(self, severity: BugSeverity) -> List[Bug]:
        """按严重级别获取BUG"""
        return [b for b in self._bugs.values() if b.severity == severity]
    
    def get_bugs_by_module(self, module: str) -> List[Bug]:
        """按模块获取BUG"""
        return [b for b in self._bugs.values() if b.module == module]
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        total = len(self._bugs)
        open_count = len(self.get_bugs_by_status(BugStatus.OPEN))
        in_progress = len(self.get_bugs_by_status(BugStatus.IN_PROGRESS))
        resolved = len(self.get_bugs_by_status(BugStatus.RESOLVED))
        
        critical = len(self.get_bugs_by_severity(BugSeverity.CRITICAL))
        high = len(self.get_bugs_by_severity(BugSeverity.HIGH))
        medium = len(self.get_bugs_by_severity(BugSeverity.MEDIUM))
        low = len(self.get_bugs_by_severity(BugSeverity.LOW))
        
        return {
            'total': total,
            'open': open_count,
            'in_progress': in_progress,
            'resolved': resolved,
            'by_severity': {
                'critical': critical,
                'high': high,
                'medium': medium,
                'low': low
            }
        }
    
    def generate_report(self) -> str:
        """生成报告"""
        stats = self.get_statistics()
        
        report = []
        report.append("=" * 70)
        report.append("BUG追踪报告")
        report.append("=" * 70)
        report.append(f"\n总计: {stats['total']} 个BUG")
        report.append(f"打开: {stats['open']}")
        report.append(f"进行中: {stats['in_progress']}")
        report.append(f"已解决: {stats['resolved']}")
        
        report.append("\n按严重级别:")
        report.append(f"  致命: {stats['by_severity']['critical']}")
        report.append(f"  高: {stats['by_severity']['high']}")
        report.append(f"  中: {stats['by_severity']['medium']}")
        report.append(f"  低: {stats['by_severity']['low']}")
        
        # 列出打开的BUG
        open_bugs = self.get_bugs_by_status(BugStatus.OPEN)
        if open_bugs:
            report.append("\n打开的BUG:")
            for bug in sorted(open_bugs, key=lambda x: x.created_at, reverse=True):
                report.append(f"  [{bug.bug_id}] {bug.title}")
                report.append(f"    模块: {bug.module}, 严重: {bug.severity.value}")
        
        report.append("=" * 70)
        
        return "\n".join(report)


# 全局单例
_bug_tracker = None


def get_bug_tracker() -> BugTracker:
    """获取BUG追踪器"""
    global _bug_tracker
    if _bug_tracker is None:
        _bug_tracker = BugTracker()
    return _bug_tracker
