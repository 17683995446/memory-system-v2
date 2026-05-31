"""
记忆时间线/历史记录功能模块
基于第一性原理：确定性、简洁性、可扩展性
"""

import os
import json
import time
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from collections import defaultdict


class MemoryEventType(Enum):
    """记忆事件类型"""
    CREATED = "created"
    MODIFIED = "modified"
    ACCESSED = "accessed"
    DELETED = "deleted"
    TAG_ADDED = "tag_added"
    TAG_REMOVED = "tag_removed"
    RELATION_ADDED = "relation_added"
    RELATION_REMOVED = "relation_removed"
    IMPORTANCE_CHANGED = "importance_changed"


class MemoryEvent:
    """记忆事件"""

    def __init__(
        self,
        memory_id: str,
        event_type: Union[MemoryEventType, str],
        details: Optional[Dict[str, Any]] = None,
        timestamp: Optional[float] = None
    ):
        self.memory_id = memory_id
        self.event_type = event_type.value if isinstance(event_type, MemoryEventType) else event_type
        self.details = details or {}
        self.timestamp = timestamp or time.time()
        self.event_id = f"{self.memory_id}_{self.timestamp:.6f}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "memory_id": self.memory_id,
            "event_type": self.event_type,
            "details": self.details,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryEvent":
        return cls(
            memory_id=data["memory_id"],
            event_type=data["event_type"],
            details=data.get("details"),
            timestamp=data.get("timestamp")
        )


class MemoryTimeline:
    """记忆时间线管理器"""

    def __init__(self, storage_path: str = "./data/timeline.json"):
        self.storage_path = storage_path
        self.events: List[MemoryEvent] = []
        # 索引
        self.memory_events: Dict[str, List[MemoryEvent]] = defaultdict(list)
        self.type_events: Dict[str, List[MemoryEvent]] = defaultdict(list)
        # 确保存储目录存在
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        self._load()

    def record_event(
        self,
        memory_id: str,
        event_type: Union[MemoryEventType, str],
        details: Optional[Dict[str, Any]] = None
    ) -> MemoryEvent:
        """记录记忆事件"""
        event = MemoryEvent(memory_id, event_type, details)
        self.events.append(event)
        self.memory_events[memory_id].append(event)
        self.type_events[event.event_type].append(event)
        self._save()
        return event

    def get_memory_timeline(
        self,
        memory_id: str,
        limit: Optional[int] = None,
        event_types: Optional[List[Union[MemoryEventType, str]]] = None
    ) -> List[MemoryEvent]:
        """获取单个记忆的时间线"""
        events = self.memory_events.get(memory_id, [])

        # 按类型过滤
        if event_types:
            type_set = {
                et.value if isinstance(et, MemoryEventType) else et
                for et in event_types
            }
            events = [e for e in events if e.event_type in type_set]

        # 按时间排序（最新的在前）
        events = sorted(events, key=lambda e: e.timestamp, reverse=True)

        # 限制数量
        if limit:
            events = events[:limit]

        return events

    def get_global_timeline(
        self,
        limit: Optional[int] = None,
        event_types: Optional[List[Union[MemoryEventType, str]]] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> List[MemoryEvent]:
        """获取全局时间线"""
        events = self.events.copy()

        # 按类型过滤
        if event_types:
            type_set = {
                et.value if isinstance(et, MemoryEventType) else et
                for et in event_types
            }
            events = [e for e in events if e.event_type in type_set]

        # 按时间过滤
        if start_time:
            events = [e for e in events if e.timestamp >= start_time]
        if end_time:
            events = [e for e in events if e.timestamp <= end_time]

        # 按时间排序（最新的在前）
        events = sorted(events, key=lambda e: e.timestamp, reverse=True)

        # 限制数量
        if limit:
            events = events[:limit]

        return events

    def get_event_statistics(self) -> Dict[str, Any]:
        """获取事件统计信息"""
        total_events = len(self.events)

        # 按类型统计
        type_counts = {
            et.value: len(self.type_events.get(et.value, []))
            for et in MemoryEventType
        }

        # 按记忆统计（最活跃的记忆）
        memory_activity = {
            mem_id: len(events)
            for mem_id, events in self.memory_events.items()
        }
        most_active = sorted(
            memory_activity.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        # 时间统计
        if self.events:
            first_time = min(e.timestamp for e in self.events)
            last_time = max(e.timestamp for e in self.events)
            time_span = last_time - first_time
        else:
            first_time = None
            last_time = None
            time_span = None

        return {
            "total_events": total_events,
            "event_type_counts": type_counts,
            "most_active_memories": most_active,
            "first_event_time": first_time,
            "last_event_time": last_time,
            "time_span_seconds": time_span
        }

    def get_activity_summary(
        self,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> Dict[str, Any]:
        """获取活动摘要"""
        events = self.get_global_timeline(
            event_types=None,
            start_time=start_time,
            end_time=end_time
        )

        # 按小时统计活动
        hourly_activity = defaultdict(int)
        for event in events:
            hour_key = time.strftime("%Y-%m-%d %H:00", time.localtime(event.timestamp))
            hourly_activity[hour_key] += 1

        return {
            "period_events": len(events),
            "hourly_activity": dict(sorted(hourly_activity.items())),
            "start_time": start_time,
            "end_time": end_time
        }

    def clear_events(self) -> int:
        """清空所有事件"""
        count = len(self.events)
        self.events = []
        self.memory_events.clear()
        self.type_events.clear()
        self._save()
        return count

    def _save(self) -> None:
        """保存到文件"""
        data = {
            "version": "1.0",
            "saved_at": time.time(),
            "events": [e.to_dict() for e in self.events]
        }

        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load(self) -> None:
        """从文件加载"""
        if not os.path.exists(self.storage_path):
            return

        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if "events" in data:
                for event_data in data["events"]:
                    event = MemoryEvent.from_dict(event_data)
                    self.events.append(event)
                    self.memory_events[event.memory_id].append(event)
                    self.type_events[event.event_type].append(event)

        except Exception as e:
            print(f"加载时间线数据失败: {e}")


class EnhancedMemoryWithTimeline:
    """
    增强的记忆系统（带时间线功能）
    装饰器模式实现
    """

    def __init__(self, memory_system):
        self.memory_system = memory_system
        self.timeline = MemoryTimeline()

    def add_with_tracking(
        self,
        text: str,
        task_id: str = "default",
        memory_level: Optional[str] = None
    ) -> str:
        """添加记忆并记录事件"""
        memory_id = self.memory_system.add(text, task_id, memory_level)
        self.timeline.record_event(
            memory_id,
            MemoryEventType.CREATED,
            {"text": text[:100], "task_id": task_id, "level": memory_level}
        )
        return memory_id

    def track_access(self, memory_id: str, query: Optional[str] = None) -> None:
        """记录访问事件"""
        self.timeline.record_event(
            memory_id,
            MemoryEventType.ACCESSED,
            {"query": query}
        )

    def get_timeline(
        self,
        memory_id: Optional[str] = None,
        limit: Optional[int] = None,
        event_types: Optional[List[Union[MemoryEventType, str]]] = None
    ) -> List[MemoryEvent]:
        """获取时间线"""
        if memory_id:
            return self.timeline.get_memory_timeline(memory_id, limit, event_types)
        else:
            return self.timeline.get_global_timeline(limit, event_types)

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.timeline.get_event_statistics()
