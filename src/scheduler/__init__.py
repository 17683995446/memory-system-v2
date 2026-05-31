"""
任务调度器
用于定时任务调度
"""

import time
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class ScheduledTask:
    """调度任务"""
    task_id: str
    name: str
    action: Callable
    interval_seconds: int
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None


class TaskScheduler:
    """任务调度器"""
    
    def __init__(self):
        self.tasks: Dict[str, ScheduledTask] = {}
        self._task_counter: int = 0
        self._lock = threading.Lock()
        self._running: bool = False
        self._scheduler_thread: Optional[threading.Thread] = None
    
    def schedule_task(
        self,
        name: str,
        action: Callable,
        interval_seconds: int
    ) -> str:
        """调度任务"""
        with self._lock:
            self._task_counter += 1
            task_id = f"TASK-{self._task_counter:06d}"
            
            task = ScheduledTask(
                task_id=task_id,
                name=name,
                action=action,
                interval_seconds=interval_seconds,
                next_run=datetime.now()
            )
            
            self.tasks[task_id] = task
            return task_id
    
    def start(self):
        """启动调度器"""
        if self._running:
            return
        
        self._running = True
        self._scheduler_thread = threading.Thread(
            target=self._schedule_loop,
            daemon=True
        )
        self._scheduler_thread.start()
    
    def stop(self):
        """停止调度器"""
        self._running = False
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5.0)
    
    def _schedule_loop(self):
        """调度循环"""
        while self._running:
            now = datetime.now()
            
            for task in self.tasks.values():
                if not task.enabled:
                    continue
                
                if task.next_run and now >= task.next_run:
                    try:
                        task.action()
                        task.last_run = now
                        task.next_run = now + timedelta(seconds=task.interval_seconds)
                    except Exception:
                        pass
            
            time.sleep(1)
    
    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """获取任务"""
        return self.tasks.get(task_id)
    
    def enable_task(self, task_id: str) -> bool:
        """启用任务"""
        if task_id not in self.tasks:
            return False
        self.tasks[task_id].enabled = True
        return True
    
    def disable_task(self, task_id: str) -> bool:
        """禁用任务"""
        if task_id not in self.tasks:
            return False
        self.tasks[task_id].enabled = False
        return True


_global_scheduler: Optional[TaskScheduler] = None


def get_task_scheduler() -> TaskScheduler:
    """获取全局任务调度器"""
    global _global_scheduler
    if _global_scheduler is None:
        _global_scheduler = TaskScheduler()
    return _global_scheduler
