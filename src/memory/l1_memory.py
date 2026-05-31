"""
L1 瞬时工作记忆 - 单任务实时运行上下文
基于第一性原理：低延迟、易销毁、不落地、高读写
"""
import time
from collections import deque
from threading import Lock
from typing import Dict, List, Optional


class L1MemoryItem:
    """L1记忆项"""
    def __init__(self, text: str, task_id: str, timestamp: Optional[float] = None):
        self.text = text
        self.task_id = task_id
        self.timestamp = timestamp or time.time()
    
    def to_dict(self) -> Dict:
        return {
            "text": self.text,
            "task_id": self.task_id,
            "timestamp": self.timestamp
        }


class L1Memory:
    """L1瞬时工作记忆 - 内存字典 + 队列实现"""
    
    def __init__(self, max_items_per_task: int = 100, max_tasks: int = 1000):
        self._lock = Lock()
        self._task_memories: Dict[str, deque] = {}
        self._max_items_per_task = max_items_per_task
        self._max_tasks = max_tasks
    
    def add(self, text: str, task_id: str) -> bool:
        """添加记忆项"""
        with self._lock:
            # 清理过期任务，防止内存溢出
            self._cleanup_old_tasks()
            
            if task_id not in self._task_memories:
                self._task_memories[task_id] = deque(maxlen=self._max_items_per_task)
            
            item = L1MemoryItem(text, task_id)
            self._task_memories[task_id].append(item)
            return True
    
    def get(self, task_id: str, limit: Optional[int] = None) -> List[Dict]:
        """获取任务相关记忆"""
        with self._lock:
            if task_id not in self._task_memories:
                return []
            
            items = list(self._task_memories[task_id])
            if limit:
                items = items[-limit:]
            return [item.to_dict() for item in items]
    
    def clear(self, task_id: str) -> bool:
        """清空任务记忆（任务结束自动调用）"""
        with self._lock:
            if task_id in self._task_memories:
                del self._task_memories[task_id]
                return True
            return False
    
    def clear_all(self) -> None:
        """清空所有记忆"""
        with self._lock:
            self._task_memories.clear()
    
    def _cleanup_old_tasks(self) -> None:
        """清理旧任务，防止内存溢出"""
        if len(self._task_memories) > self._max_tasks:
            # 移除最旧的任务
            oldest_tasks = sorted(
                self._task_memories.keys(),
                key=lambda t: self._task_memories[t][0].timestamp if self._task_memories[t] else float('inf')
            )
            for task in oldest_tasks[:len(self._task_memories) - self._max_tasks]:
                del self._task_memories[task]
    
    def size(self) -> int:
        """获取当前记忆总数"""
        with self._lock:
            return sum(len(queue) for queue in self._task_memories.values())
    
    def task_count(self) -> int:
        """获取当前任务数"""
        with self._lock:
            return len(self._task_memories)
    
    def get_all(self) -> List[Dict]:
        """获取所有记忆"""
        with self._lock:
            all_items = []
            for task_id, queue in self._task_memories.items():
                for item in queue:
                    item_dict = item.to_dict()
                    item_dict["session_id"] = task_id
                    all_items.append(item_dict)
            return all_items
    
    def clear(self) -> None:
        """清空所有记忆"""
        with self._lock:
            self._task_memories.clear()
