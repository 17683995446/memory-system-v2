"""
消息队列
用于异步消息处理
"""

import time
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque


class MessagePriority(Enum):
    """消息优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class Message:
    """消息"""
    message_id: str
    queue_name: str
    data: Any
    priority: MessagePriority
    timestamp: datetime
    retry_count: int = 0


class MessageQueue:
    """消息队列"""
    
    def __init__(self):
        self.queues: Dict[str, deque] = {}
        self.consumers: Dict[str, List[Callable]] = {}
        self._message_counter: int = 0
        self._lock = threading.Lock()
    
    def create_queue(self, queue_name: str) -> bool:
        """创建队列"""
        with self._lock:
            if queue_name not in self.queues:
                self.queues[queue_name] = deque()
                self.consumers[queue_name] = []
                return True
            return False
    
    def enqueue(
        self,
        queue_name: str,
        data: Any,
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> str:
        """入队"""
        if queue_name not in self.queues:
            self.create_queue(queue_name)
        
        with self._lock:
            self._message_counter += 1
            message_id = f"MSG-{self._message_counter:06d}"
            
            message = Message(
                message_id=message_id,
                queue_name=queue_name,
                data=data,
                priority=priority,
                timestamp=datetime.now()
            )
            
            self.queues[queue_name].append(message)
            return message_id
    
    def dequeue(self, queue_name: str) -> Optional[Message]:
        """出队"""
        if queue_name not in self.queues or not self.queues[queue_name]:
            return None
        
        with self._lock:
            if self.queues[queue_name]:
                return self.queues[queue_name].popleft()
            return None
    
    def register_consumer(self, queue_name: str, consumer: Callable) -> bool:
        """注册消费者"""
        if queue_name not in self.queues:
            self.create_queue(queue_name)
        
        with self._lock:
            if queue_name not in self.consumers:
                self.consumers[queue_name] = []
            self.consumers[queue_name].append(consumer)
            return True
    
    def get_queue_size(self, queue_name: str) -> int:
        """获取队列大小"""
        with self._lock:
            if queue_name in self.queues:
                return len(self.queues[queue_name])
            return 0


_global_queue: Optional[MessageQueue] = None


def get_message_queue() -> MessageQueue:
    """获取全局消息队列"""
    global _global_queue
    if _global_queue is None:
        _global_queue = MessageQueue()
    return _global_queue


from enum import Enum
