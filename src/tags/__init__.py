"""
记忆标签/分类功能模块
基于第一性原理：确定性、简洁性、可扩展性
"""

import os
import json
import time
from typing import Dict, List, Optional, Set, Any
from collections import defaultdict
from ..utils.logger import get_logger



class TagManager:
    """标签管理器"""

    def __init__(self, storage_path: str = "./data/tags.json"):
        self._logger = get_logger()
        self.storage_path = storage_path
        self._memory_tags: Dict[str, Set[str]] = defaultdict(set)  # memory_id -> tags
        self._tag_memories: Dict[str, Set[str]] = defaultdict(set)  # tag -> memory_ids
        self._tag_metadata: Dict[str, Dict[str, Any]] = {}  # tag -> metadata
        self._lock = None  # 简化实现，不使用复杂锁机制

        # 确保存储目录存在
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        self._load()

    def add_tags(self, memory_id: str, tags: List[str]) -> int:
        """
        给记忆添加标签

        Args:
            memory_id: 记忆ID
            tags: 标签列表

        Returns:
            实际添加的新标签数
        """
        tags = [tag.strip().lower() for tag in tags if tag.strip()]
        if not tags or not memory_id:
            return 0

        added_count = 0

        for tag in tags:
            if tag not in self._memory_tags[memory_id]:
                self._memory_tags[memory_id].add(tag)
                self._tag_memories[tag].add(memory_id)
                added_count += 1

                # 更新标签元数据
                if tag not in self._tag_metadata:
                    self._tag_metadata[tag] = {
                        "created_at": time.time(),
                        "usage_count": 0
                    }
                self._tag_metadata[tag]["usage_count"] = len(self._tag_memories[tag])

        if added_count > 0:
            self._save()

        return added_count

    def remove_tags(self, memory_id: str, tags: List[str]) -> int:
        """
        从记忆移除标签

        Args:
            memory_id: 记忆ID
            tags: 标签列表

        Returns:
            实际移除的标签数
        """
        tags = [tag.strip().lower() for tag in tags if tag.strip()]
        if not tags or not memory_id:
            return 0

        removed_count = 0

        for tag in tags:
            if tag in self._memory_tags[memory_id]:
                self._memory_tags[memory_id].remove(tag)
                self._tag_memories[tag].remove(memory_id)
                removed_count += 1

                # 更新标签元数据
                if tag in self._tag_metadata:
                    self._tag_metadata[tag]["usage_count"] = len(self._tag_memories[tag])
                    if len(self._tag_memories[tag]) == 0:
                        del self._tag_memories[tag]
                        del self._tag_metadata[tag]

        if not self._memory_tags[memory_id]:
            del self._memory_tags[memory_id]

        if removed_count > 0:
            self._save()

        return removed_count

    def get_tags(self, memory_id: str) -> List[str]:
        """获取记忆的标签"""
        return sorted(list(self._memory_tags.get(memory_id, set())))

    def get_memories_by_tag(self, tag: str) -> List[str]:
        """获取具有指定标签的所有记忆ID"""
        tag = tag.strip().lower()
        return sorted(list(self._tag_memories.get(tag, set())))

    def get_all_tags(self) -> List[str]:
        """获取所有标签"""
        return sorted(list(self._tag_memories.keys()))

    def get_tag_statistics(self) -> List[Dict[str, Any]]:
        """获取标签统计信息"""
        stats = []
        for tag in sorted(self._tag_memories.keys()):
            stats.append({
                "tag": tag,
                "memory_count": len(self._tag_memories[tag]),
                "created_at": self._tag_metadata.get(tag, {}).get("created_at", 0)
            })
        # 按使用量排序
        stats.sort(key=lambda x: x["memory_count"], reverse=True)
        return stats

    def get_memory_tag_map(self) -> Dict[str, List[str]]:
        """获取记忆到标签的映射"""
        return {
            mem_id: sorted(tags)
            for mem_id, tags in self._memory_tags.items()
        }

    def delete_memory_tags(self, memory_id: str) -> int:
        """删除记忆的所有标签"""
        if memory_id not in self._memory_tags:
            return 0

        tags = list(self._memory_tags[memory_id])
        count = len(tags)
        self.remove_tags(memory_id, tags)
        return count

    def clear_all(self) -> int:
        """清空所有标签数据"""
        count = sum(len(tags) for tags in self._memory_tags.values())
        self._memory_tags.clear()
        self._tag_memories.clear()
        self._tag_metadata.clear()
        self._save()
        return count

    def _save(self) -> None:
        """保存到文件"""
        data = {
            "version": "1.0",
            "saved_at": time.time(),
            "memory_tags": {
                mem_id: sorted(tags)
                for mem_id, tags in self._memory_tags.items()
            },
            "tag_metadata": self._tag_metadata
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

            if "memory_tags" in data:
                for mem_id, tags in data["memory_tags"].items():
                    self._memory_tags[mem_id] = set(tags)
                    for tag in tags:
                        self._tag_memories[tag].add(mem_id)

            if "tag_metadata" in data:
                self._tag_metadata = data["tag_metadata"]
        except Exception as e:
            logger.info(f"加载标签数据失败: {e}")


class EnhancedMemorySystem:
    """
    增强的记忆系统（带标签功能）

    这是一个装饰器模式的实现，为现有记忆系统添加标签功能
    """

    def __init__(self, memory_system, tag_manager: Optional[TagManager] = None):
        self.memory_system = memory_system
        self.tag_manager = tag_manager or TagManager()

    def add_with_tags(
        self,
        text: str,
        session_id: str = "default",
        tags: Optional[List[str]] = None,
        level: Optional[str] = None
    ) -> str:
        """
        添加记忆并同时添加标签

        Args:
            text: 记忆内容
            session_id: 会话ID
            tags: 标签列表
            level: 记忆层级

        Returns:
            记忆ID
        """
        memory_id = self.memory_system.add(text, session_id, level)

        if tags and memory_id:
            self.tag_manager.add_tags(memory_id, tags)

        return memory_id

    def add_tags_to_memory(self, memory_id: str, tags: List[str]) -> int:
        """给现有记忆添加标签"""
        return self.tag_manager.add_tags(memory_id, tags)

    def remove_tags_from_memory(self, memory_id: str, tags: List[str]) -> int:
        """从记忆移除标签"""
        return self.tag_manager.remove_tags(memory_id, tags)

    def get_memory_tags(self, memory_id: str) -> List[str]:
        """获取记忆的标签"""
        return self.tag_manager.get_tags(memory_id)

    def recall_by_tag(
        self,
        tag: str,
        session_id: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """
        按标签召回记忆

        Args:
            tag: 标签
            session_id: 可选的会话过滤

        Returns:
            记忆ID列表
        """
        memory_ids = self.tag_manager.get_memories_by_tag(tag)
        return {
            "tag": tag,
            "memory_ids": memory_ids,
            "count": len(memory_ids)
        }

    def get_all_tags(self) -> List[str]:
        """获取所有标签"""
        return self.tag_manager.get_all_tags()

    def get_tag_statistics(self) -> List[Dict[str, Any]]:
        """获取标签统计"""
        return self.tag_manager.get_tag_statistics()
