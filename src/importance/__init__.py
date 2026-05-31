"""
记忆重要性/评分功能模块
基于第一性原理：确定性、简洁性、可扩展性
"""

import os
import json
import time
from typing import Dict, List, Optional, Set, Any, Union
from enum import Enum
from collections import defaultdict


class ImportanceLevel(Enum):
    """重要性等级枚举"""
    TRIVIAL = 1  # 琐碎的，可能会被遗忘
    LOW = 2  # 低重要性
    MEDIUM = 3  # 中等重要性（默认）
    HIGH = 4  # 高重要性
    CRITICAL = 5  # 极其重要


class ImportanceManager:
    """记忆重要性管理器"""

    def __init__(self, storage_path: str = "./data/importance.json"):
        self.storage_path = storage_path
        # 记忆ID -> 重要性数据
        self._memory_importance: Dict[str, Dict[str, Any]] = {}
        # 重要性等级 -> 记忆ID集合
        self._importance_memories: Dict[int, Set[str]] = defaultdict(set)
        # 评分 -> 记忆ID集合（可选的连续评分）
        self._score_memories: Dict[float, Set[str]] = defaultdict(set)

        # 确保存储目录存在
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        self._load()

    def set_importance(
        self,
        memory_id: str,
        level: Union[ImportanceLevel, int],
        score: Optional[float] = None,
        reason: Optional[str] = None
    ) -> bool:
        """
        设置记忆的重要性

        Args:
            memory_id: 记忆ID
            level: 重要性等级（枚举或整数1-5）
            score: 可选的连续评分（0.0-10.0）
            reason: 可选的重要性原因说明

        Returns:
            是否成功设置
        """
        # 标准化重要性等级
        if isinstance(level, ImportanceLevel):
            level_value = level.value
        else:
            level_value = max(1, min(5, int(level)))

        # 如果记忆已有重要性，先从旧索引中移除
        if memory_id in self._memory_importance:
            old_level = self._memory_importance[memory_id]['level']
            self._importance_memories[old_level].discard(memory_id)
            old_score = self._memory_importance[memory_id].get('score')
            if old_score is not None:
                self._score_memories[old_score].discard(memory_id)

        # 存储新的重要性数据
        importance_data = {
            'level': level_value,
            'score': score,
            'reason': reason,
            'updated_at': time.time()
        }

        self._memory_importance[memory_id] = importance_data
        self._importance_memories[level_value].add(memory_id)

        if score is not None:
            score = max(0.0, min(10.0, float(score)))
            importance_data['score'] = score
            self._score_memories[score].add(memory_id)

        self._save()
        return True

    def get_importance(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        获取记忆的重要性数据

        Args:
            memory_id: 记忆ID

        Returns:
            重要性数据字典或None
        """
        return self._memory_importance.get(memory_id)

    def get_importance_level(self, memory_id: str) -> int:
        """
        获取记忆的重要性等级（默认为MEDIUM）

        Args:
            memory_id: 记忆ID

        Returns:
            重要性等级（1-5）
        """
        data = self._memory_importance.get(memory_id)
        return data['level'] if data else 3

    def get_memories_by_importance(
        self,
        level: Union[ImportanceLevel, int],
        min_level: bool = False
    ) -> List[str]:
        """
        获取指定重要性等级的记忆

        Args:
            level: 重要性等级
            min_level: 如果为True，则获取>=该等级的所有记忆

        Returns:
            记忆ID列表
        """
        if isinstance(level, ImportanceLevel):
            level_value = level.value
        else:
            level_value = max(1, min(5, int(level)))

        if min_level:
            memories = set()
            for l in range(level_value, 6):
                memories.update(self._importance_memories.get(l, set()))
            return sorted(memories)
        else:
            return sorted(self._importance_memories.get(level_value, set()))

    def get_memories_by_score(
        self,
        min_score: float,
        max_score: float = 10.0
    ) -> List[str]:
        """
        获取评分在指定范围内的记忆

        Args:
            min_score: 最低评分（包含）
            max_score: 最高评分（包含）

        Returns:
            记忆ID列表
        """
        memories = set()
        for score in self._score_memories:
            if min_score <= score <= max_score:
                memories.update(self._score_memories[score])
        return sorted(memories)

    def get_importance_statistics(self) -> Dict[str, Any]:
        """
        获取重要性统计信息

        Returns:
            统计信息字典
        """
        total_memories = len(self._memory_importance)

        level_counts = {}
        for level in range(1, 6):
            level_counts[level] = len(self._importance_memories.get(level, set()))

        # 计算平均评分
        scores = [
            data['score']
            for data in self._memory_importance.values()
            if data.get('score') is not None
        ]
        avg_score = sum(scores) / len(scores) if scores else None

        return {
            'total_memories_with_importance': total_memories,
            'level_counts': level_counts,
            'average_score': avg_score,
            'memories_with_score': len(scores)
        }

    def remove_importance(self, memory_id: str) -> bool:
        """
        移除记忆的重要性标记

        Args:
            memory_id: 记忆ID

        Returns:
            是否成功移除
        """
        if memory_id not in self._memory_importance:
            return False

        data = self._memory_importance[memory_id]
        self._importance_memories[data['level']].discard(memory_id)

        if data.get('score') is not None:
            self._score_memories[data['score']].discard(memory_id)

        del self._memory_importance[memory_id]
        self._save()
        return True

    def clear_all(self) -> int:
        """
        清空所有重要性数据

        Returns:
            清理的记忆数量
        """
        count = len(self._memory_importance)
        self._memory_importance.clear()
        self._importance_memories.clear()
        self._score_memories.clear()
        self._save()
        return count

    def _save(self) -> None:
        """保存到文件"""
        data = {
            'version': '1.0',
            'saved_at': time.time(),
            'memory_importance': self._memory_importance
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

            if 'memory_importance' in data:
                self._memory_importance = data['memory_importance']

                # 重建索引
                for mem_id, importance_data in self._memory_importance.items():
                    level = importance_data['level']
                    self._importance_memories[level].add(mem_id)

                    score = importance_data.get('score')
                    if score is not None:
                        self._score_memories[score].add(mem_id)

        except Exception as e:
            print(f"加载重要性数据失败: {e}")


class EnhancedMemoryWithImportance:
    """
    增强的记忆系统（带重要性功能）

    装饰器模式实现
    """

    def __init__(
        self,
        memory_system,
        importance_manager: Optional[ImportanceManager] = None
    ):
        self.memory_system = memory_system
        self.importance_manager = importance_manager or ImportanceManager()

    def add_with_importance(
        self,
        text: str,
        task_id: str = "default",
        level: Union[ImportanceLevel, int] = ImportanceLevel.MEDIUM,
        score: Optional[float] = None,
        reason: Optional[str] = None,
        memory_level: Optional[str] = None
    ) -> str:
        """
        添加记忆并同时设置重要性

        Args:
            text: 记忆内容
            task_id: 任务/会话ID
            level: 重要性等级
            score: 可选评分
            reason: 可选的重要性原因
            memory_level: 记忆层级

        Returns:
            记忆ID
        """
        memory_id = self.memory_system.add(text, task_id, memory_level)
        self.importance_manager.set_importance(memory_id, level, score, reason)
        return memory_id

    def set_importance(
        self,
        memory_id: str,
        level: Union[ImportanceLevel, int],
        score: Optional[float] = None,
        reason: Optional[str] = None
    ) -> bool:
        """设置记忆的重要性"""
        return self.importance_manager.set_importance(memory_id, level, score, reason)

    def get_importance(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """获取记忆的重要性"""
        return self.importance_manager.get_importance(memory_id)

    def recall_by_importance(
        self,
        level: Union[ImportanceLevel, int],
        min_level: bool = False,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        按重要性召回记忆

        Args:
            level: 重要性等级
            min_level: 是否获取>=该等级的所有记忆
            task_id: 可选的任务/会话过滤

        Returns:
            召回结果字典
        """
        memory_ids = self.importance_manager.get_memories_by_importance(
            level, min_level
        )

        return {
            'level': level.value if isinstance(level, ImportanceLevel) else level,
            'min_level': min_level,
            'memory_ids': memory_ids,
            'count': len(memory_ids)
        }

    def get_importance_statistics(self) -> Dict[str, Any]:
        """获取重要性统计"""
        return self.importance_manager.get_importance_statistics()
