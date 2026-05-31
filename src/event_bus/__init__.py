"""
事件总线
用于系统内部事件通信
"""

import time
import threading
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Event:
    """事件"""
    event_id: str
    event_type: str
    data: Any
    timestamp: datetime
    source: str = "system"


@dataclass
class EventHandler:
    """事件处理器"""
    handler_id: str
    event_type: str
    callback: Callable
    enabled: bool = True


class EventBus:
    """事件总线"""
    
    def __init__(self):
        self.handlers: Dict[str, List[EventHandler]] = {}
        self.events: List[Event] = []
        self._handler_counter: int = 0
        self._event_counter: int = 0
        self._lock = threading.Lock()
    
    def subscribe(
        self,
        event_type: str,
        callback: Callable
    ) -> str:
        """订阅事件"""
        with self._lock:
            self._handler_counter += 1
            handler_id = f"HANDLER-{self._handler_counter:06d}"
            
            handler = EventHandler(
                handler_id=handler_id,
                event_type=event_type,
                callback=callback
            )
            
            if event_type not in self.handlers:
                self.handlers[event_type] = []
            self.handlers[event_type].append(handler)
            
            return handler_id
    
    def unsubscribe(self, handler_id: str) -> bool:
        """取消订阅"""
        with self._lock:
            for handlers in self.handlers.values():
                for i, handler in enumerate(handlers):
                    if handler.handler_id == handler_id:
                        handlers.pop(i)
                        return True
            return False
    
    def publish(
        self,
        event_type: str,
        data: Any,
        source: str = "system"
    ) -> str:
        """发布事件"""
        with self._lock:
            self._event_counter += 1
            event_id = f"EVENT-{self._event_counter:06d}"
            
            event = Event(
                event_id=event_id,
                event_type=event_type,
                data=data,
                timestamp=datetime.now(),
                source=source
            )
            
            self.events.append(event)
            if len(self.events) > 1000:
                self.events = self.events[-1000:]
        
        handlers = self.handlers.get(event_type, [])
        for handler in handlers:
            if handler.enabled:
                try:
                    handler.callback(event)
                except Exception:
                    pass
        
        return event_id
    
    def get_events(
        self,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Event]:
        """获取事件"""
        with self._lock:
            if event_type:
                events = [e for e in self.events if e.event_type == event_type]
            else:
                events = list(self.events)
            return events[-limit:]


_global_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """获取全局事件总线"""
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus
