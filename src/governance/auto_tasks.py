"""
定时自治任务系统
基于第一性原理：自动执行清理、更新、优化任务
"""
import time
import threading
from typing import Callable, Dict, List
from dataclasses import dataclass
from enum import Enum


class TaskType(Enum):
    """任务类型"""
    CLEANUP = "cleanup"
    OPTIMIZE = "optimize"
    BACKUP = "backup"
    CHECK = "check"
    CUSTOM = "custom"


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ScheduledTask:
    """定时任务"""
    task_id: str
    task_type: TaskType
    interval_seconds: int
    last_run: float
    next_run: float
    status: TaskStatus
    handler: Callable
    enabled: bool = True
    error_count: int = 0
    last_error: str = ""


class AutoTaskScheduler:
    """自动任务调度器"""
    
    def __init__(self):
        self._tasks: Dict[str, ScheduledTask] = {}
        self._running = False
        self._thread = None
    
    def register_task(
        self,
        task_id: str,
        task_type: TaskType,
        interval_seconds: int,
        handler: Callable,
        enabled: bool = True
    ) -> None:
        """注册定时任务"""
        now = time.time()
        
        task = ScheduledTask(
            task_id=task_id,
            task_type=task_type,
            interval_seconds=interval_seconds,
            last_run=0,
            next_run=now + interval_seconds,
            status=TaskStatus.PENDING,
            handler=handler,
            enabled=enabled
        )
        
        self._tasks[task_id] = task
    
    def start(self) -> None:
        """启动调度器"""
        if self._running:
            return
        
        self._running = True
        
        def run_loop():
            while self._running:
                now = time.time()
                
                for task in self._tasks.values():
                    if not task.enabled:
                        continue
                    
                    if now >= task.next_run:
                        self._execute_task(task)
                
                time.sleep(1)  # 每秒检查一次
        
        self._thread = threading.Thread(target=run_loop, daemon=True)
        self._thread.start()
    
    def stop(self) -> None:
        """停止调度器"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
    
    def _execute_task(self, task: ScheduledTask) -> None:
        """执行任务"""
        task.status = TaskStatus.RUNNING
        
        try:
            task.handler()
            task.status = TaskStatus.COMPLETED
            task.last_run = time.time()
            task.next_run = task.last_run + task.interval_seconds
            task.error_count = 0
            task.last_error = ""
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_count += 1
            task.last_error = str(e)
            
            # 指数退避
            task.next_run = time.time() + min(task.interval_seconds * (2 ** task.error_count), 3600)
    
    def enable_task(self, task_id: str) -> bool:
        """启用任务"""
        if task_id in self._tasks:
            self._tasks[task_id].enabled = True
            return True
        return False
    
    def disable_task(self, task_id: str) -> bool:
        """禁用任务"""
        if task_id in self._tasks:
            self._tasks[task_id].enabled = False
            return True
        return False
    
    def get_task_status(self, task_id: str) -> Dict:
        """获取任务状态"""
        if task_id not in self._tasks:
            return None
        
        task = self._tasks[task_id]
        return {
            'task_id': task.task_id,
            'type': task.task_type.value,
            'enabled': task.enabled,
            'status': task.status.value,
            'last_run': task.last_run,
            'next_run': task.next_run,
            'error_count': task.error_count,
            'last_error': task.last_error
        }
    
    def get_all_tasks(self) -> List[Dict]:
        """获取所有任务"""
        return [self.get_task_status(tid) for tid in self._tasks]


class ExperienceToRuleConverter:
    """经验转规则转换器"""
    
    def __init__(self):
        self._conversion_history: List[Dict] = []
    
    def extract_rule_from_experience(
        self,
        experience: Dict,
        confidence_threshold: float = 0.7
    ) -> Optional[Dict]:
        """从经验中提取规则"""
        # 检查置信度
        confidence = experience.get('confidence', 0.0)
        if confidence < confidence_threshold:
            return None
        
        # 提取实体和关系
        entity = experience.get('entity')
        attribute = experience.get('attribute')
        value = experience.get('value')
        
        if not all([entity, attribute, value]):
            return None
        
        # 构建规则
        rule = {
            'type': 'derived_rule',
            'entity': entity,
            'attribute': attribute,
            'value': value,
            'confidence': confidence,
            'source_experience': experience.get('id'),
            'extracted_at': time.time()
        }
        
        self._conversion_history.append(rule)
        
        return rule
    
    def batch_convert(
        self,
        experiences: List[Dict],
        confidence_threshold: float = 0.7
    ) -> List[Dict]:
        """批量转换经验为规则"""
        rules = []
        
        for exp in experiences:
            rule = self.extract_rule_from_experience(exp, confidence_threshold)
            if rule:
                rules.append(rule)
        
        return rules
    
    def get_conversion_history(self, limit: int = 100) -> List[Dict]:
        """获取转换历史"""
        return self._conversion_history[-limit:]


# 全局单例
_auto_task_scheduler = None
_experience_converter = None


def get_auto_task_scheduler() -> AutoTaskScheduler:
    global _auto_task_scheduler
    if _auto_task_scheduler is None:
        _auto_task_scheduler = AutoTaskScheduler()
    return _auto_task_scheduler


def get_experience_converter() -> ExperienceToRuleConverter:
    global _experience_converter
    if _experience_converter is None:
        _experience_converter = ExperienceToRuleConverter()
    return _experience_converter
