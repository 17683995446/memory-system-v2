"""
记忆关联/关系网络功能模块
基于第一性原理：确定性、简洁性、可扩展性
"""

import os
import json
import time
from typing import Dict, List, Optional, Set, Any
from collections import defaultdict


class MemoryRelation:
    """记忆关系类"""

    def __init__(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        description: Optional[str] = None
    ):
        self.source_id = source_id
        self.target_id = target_id
        self.relation_type = relation_type
        self.description = description
        self.created_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation_type": self.relation_type,
            "description": self.description,
            "created_at": self.created_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryRelation':
        return cls(
            source_id=data["source_id"],
            target_id=data["target_id"],
            relation_type=data["relation_type"],
            description=data.get("description")
        )


class MemoryRelationNetwork:
    """记忆关系网络类"""

    def __init__(self, storage_path: str = "./data/relations.json"):
        self.storage_path = storage_path
        self.relations: List[MemoryRelation] = []
        # 索引：源记忆 -> 关系列表
        self.source_index: Dict[str, List[MemoryRelation]] = defaultdict(list)
        # 索引：目标记忆 -> 关系列表
        self.target_index: Dict[str, List[MemoryRelation]] = defaultdict(list)
        # 索引：关系类型 -> 关系列表
        self.type_index: Dict[str, List[MemoryRelation]] = defaultdict(list)

        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        self._load()

    def add_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: str = "related_to",
        description: Optional[str] = None
    ) -> MemoryRelation:
        """添加记忆关系"""
        # 检查是否已存在相同的关系（避免重复）
        if self._relation_exists(source_id, target_id, relation_type):
            # 返回已存在的关系
            for relation in self.source_index.get(source_id, []):
                if relation.target_id == target_id and relation.relation_type == relation_type:
                    return relation

        relation = MemoryRelation(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            description=description
        )

        self.relations.append(relation)
        self.source_index[source_id].append(relation)
        self.target_index[target_id].append(relation)
        self.type_index[relation_type].append(relation)

        self._save()
        return relation

    def _relation_exists(self, source_id: str, target_id: str, relation_type: str) -> bool:
        """检查关系是否已存在"""
        for relation in self.source_index.get(source_id, []):
            if relation.target_id == target_id and relation.relation_type == relation_type:
                return True
        return False

    def get_relations_from(self, memory_id: str) -> List[MemoryRelation]:
        """获取从指定记忆出发的所有关系"""
        return self.source_index.get(memory_id, [])

    def get_relations_to(self, memory_id: str) -> List[MemoryRelation]:
        """获取指向指定记忆的所有关系"""
        return self.target_index.get(memory_id, [])

    def get_all_relations(self, memory_id: str) -> List[MemoryRelation]:
        """获取与指定记忆相关的所有关系"""
        result = []
        result.extend(self.source_index.get(memory_id, []))
        result.extend(self.target_index.get(memory_id, []))
        return result

    def get_relations_by_type(self, relation_type: str) -> List[MemoryRelation]:
        """获取指定类型的所有关系"""
        return self.type_index.get(relation_type, [])

    def remove_relation(self, relation: MemoryRelation) -> bool:
        """移除指定关系"""
        if relation not in self.relations:
            return False

        self.relations.remove(relation)

        # 从索引中移除
        if relation in self.source_index.get(relation.source_id, []):
            self.source_index[relation.source_id].remove(relation)

        if relation in self.target_index.get(relation.target_id, []):
            self.target_index[relation.target_id].remove(relation)

        if relation in self.type_index.get(relation.relation_type, []):
            self.type_index[relation.relation_type].remove(relation)

        self._save()
        return True

    def remove_relations_related_to(self, memory_id: str) -> int:
        """移除与指定记忆相关的所有关系"""
        relations_to_remove = self.get_all_relations(memory_id)
        count = len(relations_to_remove)
        for relation in relations_to_remove.copy():
            self.remove_relation(relation)
        return count

    def traverse(
        self,
        start_id: str,
        max_depth: int = 3,
        include_self: bool = False
    ) -> Dict[str, List[str]]:
        """
        广度优先遍历记忆关系网络

        Args:
            start_id: 起始记忆ID
            max_depth: 最大遍历深度
            include_self: 是否包含起始记忆

        Returns:
            字典，键为深度，值为该深度的记忆ID列表
        """
        visited = set()
        result = defaultdict(list)
        queue = [(start_id, 0)]

        if include_self:
            visited.add(start_id)
            result[0].append(start_id)

        while queue:
            current_id, depth = queue.pop(0)

            if depth >= max_depth:
                continue

            # 查看从当前记忆出发的关系
            for relation in self.get_relations_from(current_id):
                next_id = relation.target_id
                if next_id not in visited:
                    visited.add(next_id)
                    result[depth + 1].append(next_id)
                    queue.append((next_id, depth + 1))

        return dict(result)

    def get_statistics(self) -> Dict[str, Any]:
        """获取关系网络统计信息"""
        # 统计关系类型分布
        type_counts = {}
        for rel_type, relations in self.type_index.items():
            type_counts[rel_type] = len(relations)

        # 统计最活跃的记忆（关系最多的）
        memory_relation_count = defaultdict(int)
        for relation in self.relations:
            memory_relation_count[relation.source_id] += 1
            memory_relation_count[relation.target_id] += 1

        top_memories = sorted(
            memory_relation_count.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        return {
            "total_relations": len(self.relations),
            "relation_types": sorted(list(self.type_index.keys())),
            "type_distribution": type_counts,
            "top_connected_memories": top_memories
        }

    def clear_all(self) -> int:
        """清空所有关系"""
        count = len(self.relations)
        self.relations = []
        self.source_index.clear()
        self.target_index.clear()
        self.type_index.clear()
        self._save()
        return count

    def _save(self) -> None:
        """保存到文件"""
        data = {
            "version": "1.0",
            "saved_at": time.time(),
            "relations": [relation.to_dict() for relation in self.relations]
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

            if "relations" in data:
                for rel_data in data["relations"]:
                    relation = MemoryRelation.from_dict(rel_data)
                    self.relations.append(relation)
                    self.source_index[relation.source_id].append(relation)
                    self.target_index[relation.target_id].append(relation)
                    self.type_index[relation.relation_type].append(relation)

        except Exception as e:
            print(f"加载关系数据失败: {e}")


class EnhancedMemoryWithRelations:
    """
    增强的记忆系统（带关系网络）
    装饰器模式实现
    """

    def __init__(self, memory_system):
        self.memory_system = memory_system
        self.relation_network = MemoryRelationNetwork()

    def add_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: str = "related_to",
        description: Optional[str] = None
    ) -> MemoryRelation:
        """添加记忆关系"""
        return self.relation_network.add_relation(
            source_id, target_id, relation_type, description
        )

    def get_related_memories(
        self,
        memory_id: str,
        relation_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取与指定记忆相关的所有记忆"""
        relations = self.relation_network.get_all_relations(memory_id)

        if relation_type:
            relations = [r for r in relations if r.relation_type == relation_type]

        # 获取相关记忆的内容
        result = []
        for relation in relations:
            other_id = relation.target_id if relation.source_id == memory_id else relation.source_id
            result.append({
                "memory_id": other_id,
                "relation_type": relation.relation_type,
                "direction": "outgoing" if relation.source_id == memory_id else "incoming",
                "description": relation.description
            })

        return result

    def get_relation_statistics(self) -> Dict[str, Any]:
        """获取关系网络统计"""
        return self.relation_network.get_statistics()
