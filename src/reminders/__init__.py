"""
记忆提醒/定时任务功能模块
基于第一性原理：确定性、简洁性、可扩展性
"""

import os
import json
import time
import uuid
import threading
from typing import Dict, List, Optional, Any, Callable
from collections import defaultdict
from enum import Enum


class ReminderStatus(Enum):
    """提醒状态"""
    PENDING = "pending"      # 待执行
    TRIGGERED = "triggered"  # 已触发
    CANCELLED = "cancelled"  # 已取消
    FAILED = "failed"        # 执行失败


class TriggerType(Enum):
    """触发类型"""
    TIME_BASED = "time_based"      # 基于时间
    CONDITION_BASED = "condition"   # 基于条件
    RECURRING = "recurring"        # 重复执行


class Reminder:
    """记忆提醒类"""

    def __init__(
        self,
        memory_id: str,
        trigger_type: TriggerType,
        title: str,
        message: Optional[str] = None,
        trigger_time: Optional[float] = None,
        condition: Optional[Dict[str, Any]] = None,
        recurring_config: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.reminder_id = str(uuid.uuid4())
        self.memory_id = memory_id
        self.trigger_type = trigger_type.value if isinstance(trigger_type, TriggerType) else trigger_type
        self.title = title
        self.message = message or f"提醒：{title}"
        self.trigger_time = trigger_time
        self.condition = condition
        self.recurring_config = recurring_config
        self.metadata = metadata or {}
        self.status = ReminderStatus.PENDING.value
        self.created_at = time.time()
        self.triggered_at = None
        self.last_check = None
        self.execution_count = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reminder_id": self.reminder_id,
            "memory_id": self.memory_id,
            "trigger_type": self.trigger_type,
            "title": self.title,
            "message": self.message,
            "trigger_time": self.trigger_time,
            "condition": self.condition,
            "recurring_config": self.recurring_config,
            "metadata": self.metadata,
            "status": self.status,
            "created_at": self.created_at,
            "triggered_at": self.triggered_at,
            "last_check": self.last_check,
            "execution_count": self.execution_count
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Reminder':
        reminder = cls(
            memory_id=data["memory_id"],
            trigger_type=data["trigger_type"],
            title=data["title"],
            message=data.get("message"),
            trigger_time=data.get("trigger_time"),
            condition=data.get("condition"),
            recurring_config=data.get("recurring_config"),
            metadata=data.get("metadata")
        )
        reminder.reminder_id = data.get("reminder_id", reminder.reminder_id)
        reminder.status = data.get("status", ReminderStatus.PENDING.value)
        reminder.created_at = data.get("created_at", time.time())
        reminder.triggered_at = data.get("triggered_at")
        reminder.last_check = data.get("last_check")
        reminder.execution_count = data.get("execution_count", 0)
        return reminder


class ReminderScheduler:
    """提醒调度器"""

    def __init__(self):
        self.reminders: Dict[str, Reminder] = {}
        self.callbacks: List[Callable] = []
        self.running = False
        self.scheduler_thread = None

    def add_reminder(self, reminder: Reminder) -> str:
        """添加提醒"""
        self.reminders[reminder.reminder_id] = reminder
        return reminder.reminder_id

    def remove_reminder(self, reminder_id: str) -> bool:
        """移除提醒"""
        if reminder_id in self.reminders:
            reminder = self.reminders[reminder_id]
            reminder.status = ReminderStatus.CANCELLED.value
            return True
        return False

    def get_reminder(self, reminder_id: str) -> Optional[Reminder]:
        """获取提醒"""
        return self.reminders.get(reminder_id)

    def get_reminders_by_memory(self, memory_id: str) -> List[Reminder]:
        """获取某个记忆的所有提醒"""
        return [
            r for r in self.reminders.values()
            if r.memory_id == memory_id
        ]

    def get_pending_reminders(self) -> List[Reminder]:
        """获取所有待执行的提醒"""
        return [
            r for r in self.reminders.values()
            if r.status == ReminderStatus.PENDING.value
        ]

    def get_reminders_by_status(self, status: ReminderStatus) -> List[Reminder]:
        """按状态获取提醒"""
        return [
            r for r in self.reminders.values()
            if r.status == status.value
        ]

    def register_callback(self, callback: Callable[[Reminder], None]):
        """注册回调函数"""
        self.callbacks.append(callback)

    def trigger_reminder(self, reminder_id: str) -> bool:
        """触发提醒"""
        reminder = self.reminders.get(reminder_id)
        if not reminder or reminder.status != ReminderStatus.PENDING.value:
            return False

        reminder.status = ReminderStatus.TRIGGERED.value
        reminder.triggered_at = time.time()
        reminder.execution_count += 1

        # 执行回调
        for callback in self.callbacks:
            try:
                callback(reminder)
            except Exception as e:
                print(f"提醒回调执行失败: {e}")
                reminder.status = ReminderStatus.FAILED.value
                return False

        # 处理重复提醒
        if reminder.recurring_config:
            self._schedule_next_recurring(reminder)

        return True

    def _schedule_next_recurring(self, reminder: Reminder):
        """调度下一个重复提醒"""
        config = reminder.recurring_config
        interval = config.get("interval_seconds", 86400)  # 默认每天

        reminder.trigger_time = time.time() + interval
        reminder.status = ReminderStatus.PENDING.value

    def check_time_based_reminders(self) -> List[str]:
        """检查基于时间的提醒"""
        triggered_ids = []
        current_time = time.time()

        for reminder in self.get_pending_reminders():
            if reminder.trigger_type == TriggerType.TIME_BASED.value:
                if reminder.trigger_time and reminder.trigger_time <= current_time:
                    if self.trigger_reminder(reminder.reminder_id):
                        triggered_ids.append(reminder.reminder_id)

        return triggered_ids

    def check_condition_based_reminders(
        self,
        condition_evaluator: Callable[[Dict[str, Any]], bool]
    ) -> List[str]:
        """检查基于条件的提醒"""
        triggered_ids = []
        current_time = time.time()

        for reminder in self.get_pending_reminders():
            if reminder.trigger_type == TriggerType.CONDITION_BASED.value:
                reminder.last_check = current_time

                if condition_evaluator(reminder.condition or {}):
                    if self.trigger_reminder(reminder.reminder_id):
                        triggered_ids.append(reminder.reminder_id)

        return triggered_ids

    def start_scheduler(self, check_interval: float = 60.0):
        """启动调度器线程"""
        if self.running:
            return

        self.running = True

        def scheduler_loop():
            while self.running:
                self.check_time_based_reminders()
                time.sleep(check_interval)

        self.scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
        self.scheduler_thread.start()

    def stop_scheduler(self):
        """停止调度器"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = len(self.reminders)
        pending = len([r for r in self.reminders.values() if r.status == ReminderStatus.PENDING.value])
        triggered = len([r for r in self.reminders.values() if r.status == ReminderStatus.TRIGGERED.value])
        cancelled = len([r for r in self.reminders.values() if r.status == ReminderStatus.CANCELLED.value])

        # 按类型统计
        type_counts = defaultdict(int)
        for r in self.reminders.values():
            type_counts[r.trigger_type] += 1

        return {
            "total_reminders": total,
            "pending": pending,
            "triggered": triggered,
            "cancelled": cancelled,
            "type_distribution": dict(type_counts)
        }


class EnhancedMemoryWithReminders:
    """
    增强的记忆系统（带提醒功能）
    装饰器模式实现
    """

    def __init__(self, memory_system):
        self.memory_system = memory_system
        self.scheduler = ReminderScheduler()

    def create_time_reminder(
        self,
        memory_id: str,
        title: str,
        trigger_time: float,
        message: Optional[str] = None
    ) -> str:
        """创建基于时间的提醒"""
        reminder = Reminder(
            memory_id=memory_id,
            trigger_type=TriggerType.TIME_BASED,
            title=title,
            message=message,
            trigger_time=trigger_time
        )
        return self.scheduler.add_reminder(reminder)

    def create_recurring_reminder(
        self,
        memory_id: str,
        title: str,
        interval_seconds: int,
        message: Optional[str] = None
    ) -> str:
        """创建重复提醒"""
        reminder = Reminder(
            memory_id=memory_id,
            trigger_type=TriggerType.RECURRING,
            title=title,
            message=message,
            recurring_config={"interval_seconds": interval_seconds}
        )
        return self.scheduler.add_reminder(reminder)

    def create_condition_reminder(
        self,
        memory_id: str,
        title: str,
        condition: Dict[str, Any],
        message: Optional[str] = None
    ) -> str:
        """创建基于条件的提醒"""
        reminder = Reminder(
            memory_id=memory_id,
            trigger_type=TriggerType.CONDITION_BASED,
            title=title,
            message=message,
            condition=condition
        )
        return self.scheduler.add_reminder(reminder)

    def cancel_reminder(self, reminder_id: str) -> bool:
        """取消提醒"""
        return self.scheduler.remove_reminder(reminder_id)

    def get_memory_reminders(self, memory_id: str) -> List[Reminder]:
        """获取记忆的提醒"""
        return self.scheduler.get_reminders_by_memory(memory_id)

    def get_all_reminders(self, status: Optional[ReminderStatus] = None) -> List[Reminder]:
        """获取所有提醒"""
        if status:
            return self.scheduler.get_reminders_by_status(status)
        return list(self.scheduler.reminders.values())

    def trigger_reminder(self, reminder_id: str) -> bool:
        """手动触发提醒"""
        return self.scheduler.trigger_reminder(reminder_id)

    def register_reminder_callback(self, callback: Callable[[Reminder], None]):
        """注册提醒回调"""
        self.scheduler.register_callback(callback)

    def start_reminders(self, check_interval: float = 60.0):
        """启动提醒调度"""
        self.scheduler.start_scheduler(check_interval)

    def stop_reminders(self):
        """停止提醒调度"""
        self.scheduler.stop_scheduler()

    def get_reminder_statistics(self) -> Dict[str, Any]:
        """获取提醒统计"""
        return self.scheduler.get_statistics()
