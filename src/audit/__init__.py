"""
审计日志系统
用于操作审计追踪
"""

import time
import threading
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
from enum import Enum


class AuditLevel(Enum):
    """审计级别"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditLog:
    """审计日志"""
    log_id: str
    timestamp: datetime
    user_id: str
    action: str
    resource: str
    level: AuditLevel
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    success: bool = True


class AuditLogger:
    """审计日志记录器"""
    
    def __init__(self, max_logs: int = 10000):
        self.logs: List[AuditLog] = []
        self.max_logs = max_logs
        self._log_counter: int = 0
        self._lock = threading.Lock()
    
    def log(
        self,
        user_id: str,
        action: str,
        resource: str,
        level: AuditLevel = AuditLevel.INFO,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        success: bool = True
    ) -> str:
        """记录审计日志"""
        with self._lock:
            self._log_counter += 1
            log_id = f"AUDIT-{self._log_counter:010d}"
            
            log = AuditLog(
                log_id=log_id,
                timestamp=datetime.now(),
                user_id=user_id,
                action=action,
                resource=resource,
                level=level,
                details=details or {},
                ip_address=ip_address,
                success=success
            )
            
            self.logs.append(log)
            
            if len(self.logs) > self.max_logs:
                self.logs = self.logs[-self.max_logs:]
            
            return log_id
    
    def query(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        resource: Optional[str] = None,
        level: Optional[AuditLevel] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditLog]:
        """查询审计日志"""
        with self._lock:
            results = list(self.logs)
            
            if user_id:
                results = [r for r in results if r.user_id == user_id]
            
            if action:
                results = [r for r in results if r.action == action]
            
            if resource:
                results = [r for r in results if r.resource == resource]
            
            if level:
                results = [r for r in results if r.level == level]
            
            if start_time:
                results = [r for r in results if r.timestamp >= start_time]
            
            if end_time:
                results = [r for r in results if r.timestamp <= end_time]
            
            return results[-limit:]
    
    def get_logs_by_user(self, user_id: str, limit: int = 100) -> List[AuditLog]:
        """获取用户的审计日志"""
        return self.query(user_id=user_id, limit=limit)
    
    def get_failed_actions(self, limit: int = 100) -> List[AuditLog]:
        """获取失败的操作"""
        return self.query(success=False, limit=limit)
    
    def export_to_json(self) -> str:
        """导出为JSON"""
        with self._lock:
            return json.dumps(
                [
                    {
                        "log_id": log.log_id,
                        "timestamp": log.timestamp.isoformat(),
                        "user_id": log.user_id,
                        "action": log.action,
                        "resource": log.resource,
                        "level": log.level.value,
                        "details": log.details,
                        "ip_address": log.ip_address,
                        "success": log.success
                    }
                    for log in self.logs
                ],
                indent=2
            )
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            total = len(self.logs)
            by_level = {}
            by_action = {}
            by_user = {}
            failed = 0
            
            for log in self.logs:
                level_key = log.level.value
                by_level[level_key] = by_level.get(level_key, 0) + 1
                
                by_action[log.action] = by_action.get(log.action, 0) + 1
                
                by_user[log.user_id] = by_user.get(log.user_id, 0) + 1
                
                if not log.success:
                    failed += 1
            
            return {
                "total_logs": total,
                "by_level": by_level,
                "by_action": by_action,
                "by_user": by_user,
                "failed_count": failed,
                "success_rate": ((total - failed) / total * 100) if total > 0 else 0
            }


_global_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """获取全局审计日志器"""
    global _global_audit_logger
    if _global_audit_logger is None:
        _global_audit_logger = AuditLogger()
    return _global_audit_logger


from enum import Enum
