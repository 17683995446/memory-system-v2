"""
L1 瞬时工作记忆 - 单任务实时运行上下文
基于第一性原理：低延迟、易销毁、不落地、高读写
优化：细粒度锁（按task_id分片），减少并发冲突
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
    """L1瞬时工作记忆 - 内存字典 + 队列实现
    
    并发优化策略：
    1. 使用全局锁保护任务字典结构（增删task）
    2. 每个task使用独立锁保护其队列内容
    3. 读操作（get）使用task级锁，不同task可并行
    """

    def __init__(self, max_items_per_task: int = 100, max_tasks: int = 1000):
        self._global_lock = Lock()
        self._task_locks: Dict[str, Lock] = {}
        self._task_memories: Dict[str, deque] = {}
        self._max_items_per_task = max_items_per_task
        self._max_tasks = max_tasks

    def _get_task_lock(self, task_id: str) -> Lock:
        """获取或创建task级锁（需在外部持有全局锁时调用）"""
        if task_id not in self._task_locks:
            self._task_locks[task_id] = Lock()
        return self._task_locks[task_id]

    def add(self, text: str, task_id: str) -> bool:
        """添加记忆项"""
        with self._global_lock:
            # 清理过期任务，防止内存溢出
            self._cleanup_old_tasks()

            if task_id not in self._task_memories:
                self._task_memories[task_id] = deque(maxlen=self._max_items_per_task)
                self._task_locks[task_id] = Lock()

            task_lock = self._task_locks[task_id]
            task_queue = self._task_memories[task_id]

        # 释放全局锁后，只锁定目标task的队列
        with task_lock:
            item = L1MemoryItem(text, task_id)
            task_queue.append(item)
            return True

    def get(self, task_id: str, limit: Optional[int] = None) -> List[Dict]:
        """获取任务相关记忆"""
        with self._global_lock:
            if task_id not in self._task_memories:
                return []
            task_lock = self._task_locks[task_id]
            task_queue = self._task_memories[task_id]

        # 只锁定目标task的队列进行读取
        with task_lock:
            items = list(task_queue)
            if limit:
                items = items[-limit:]
            return [item.to_dict() for item in items]

    def clear(self, task_id: str) -> bool:
        """清空任务记忆（任务结束自动调用）"""
        with self._global_lock:
            if task_id in self._task_memories:
                del self._task_memories[task_id]
                if task_id in self._task_locks:
                    del self._task_locks[task_id]
                return True
            return False

    def delete_by_key(self, key: str) -> bool:
        """根据key删除记忆"""
        with self._global_lock:
            task_ids = list(self._task_memories.keys())

        for task_id in task_ids:
            with self._global_lock:
                if task_id not in self._task_memories:
                    continue
                task_lock = self._task_locks[task_id]
                task_queue = self._task_memories[task_id]

            with task_lock:
                memory_list = list(task_queue)
                for i, memory in enumerate(memory_list):
                    if memory.text == key:
                        memory_list.pop(i)
                        # 更新deque需要重新赋值
                        with self._global_lock:
                            if task_id in self._task_memories:
                                self._task_memories[task_id] = deque(memory_list, maxlen=self._max_items_per_task)
                        return True
        return False

    def clear_all(self) -> None:
        """清空所有记忆"""
        with self._global_lock:
            self._task_memories.clear()
            self._task_locks.clear()

    def _cleanup_old_tasks(self) -> None:
        """清理旧任务，防止内存溢出（调用者必须持有全局锁）"""
        if len(self._task_memories) > self._max_tasks:
            # 移除最旧的任务
            oldest_tasks = sorted(
                self._task_memories.keys(),
                key=lambda t: self._task_memories[t][0].timestamp if self._task_memories[t] else float('inf')
            )
            for task in oldest_tasks[:len(self._task_memories) - self._max_tasks]:
                del self._task_memories[task]
                if task in self._task_locks:
                    del self._task_locks[task]

    def size(self) -> int:
        """获取当前记忆总数"""
        with self._global_lock:
            return sum(len(queue) for queue in self._task_memories.values())

    def task_count(self) -> int:
        """获取当前任务数"""
        with self._global_lock:
            return len(self._task_memories)

    def get_all(self) -> List[Dict]:
        """获取所有记忆"""
        with self._global_lock:
            tasks_snapshot = list(self._task_memories.items())

        all_items = []
        for task_id, queue in tasks_snapshot:
            with self._global_lock:
                lock = self._task_locks.get(task_id)
            if lock:
                with lock:
                    for item in queue:
                        item_dict = item.to_dict()
                        item_dict["session_id"] = task_id
                        all_items.append(item_dict)
        return all_items
