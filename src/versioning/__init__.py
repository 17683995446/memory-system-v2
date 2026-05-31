"""
记忆版本控制功能模块
基于第一性原理：确定性、简洁性、可扩展性
"""

import os
import json
import time
import hashlib
from typing import Dict, List, Optional, Any
from collections import defaultdict


class MemoryVersion:
    """记忆版本类"""

    def __init__(
        self,
        memory_id: str,
        content: str,
        version_number: int,
        comment: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.memory_id = memory_id
        self.content = content
        self.version_number = version_number
        self.comment = comment
        self.metadata = metadata or {}
        self.created_at = time.time()
        self.content_hash = self._compute_hash(content)

    def _compute_hash(self, content: str) -> str:
        """计算内容哈希"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "content": self.content,
            "version_number": self.version_number,
            "comment": self.comment,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "content_hash": self.content_hash
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryVersion':
        version = cls(
            memory_id=data["memory_id"],
            content=data["content"],
            version_number=data["version_number"],
            comment=data.get("comment"),
            metadata=data.get("metadata")
        )
        version.created_at = data.get("created_at", time.time())
        version.content_hash = data.get("content_hash", "")
        return version


class MemoryVersionControl:
    """记忆版本控制器"""

    def __init__(self, storage_path: str = "./data/versions.json"):
        self.storage_path = storage_path
        # 记忆ID -> 版本列表
        self.versions: Dict[str, List[MemoryVersion]] = defaultdict(list)
        # 当前版本号
        self.current_version: Dict[str, int] = {}

        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        self._load()

    def create_version(
        self,
        memory_id: str,
        content: str,
        comment: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MemoryVersion:
        """创建新版本"""
        # 获取下一个版本号
        next_version = self.get_version_count(memory_id) + 1

        # 创建版本对象
        version = MemoryVersion(
            memory_id=memory_id,
            content=content,
            version_number=next_version,
            comment=comment,
            metadata=metadata
        )

        # 保存版本
        self.versions[memory_id].append(version)
        self.current_version[memory_id] = next_version

        self._save()
        return version

    def get_versions(
        self,
        memory_id: str,
        limit: Optional[int] = None
    ) -> List[MemoryVersion]:
        """获取记忆的所有版本（最新在前）"""
        versions = self.versions.get(memory_id, [])
        versions = sorted(versions, key=lambda v: v.version_number, reverse=True)

        if limit:
            versions = versions[:limit]

        return versions

    def get_version(
        self,
        memory_id: str,
        version_number: int
    ) -> Optional[MemoryVersion]:
        """获取指定版本"""
        versions = self.versions.get(memory_id, [])
        for version in versions:
            if version.version_number == version_number:
                return version
        return None

    def get_latest_version(self, memory_id: str) -> Optional[MemoryVersion]:
        """获取最新版本"""
        versions = self.get_versions(memory_id, limit=1)
        return versions[0] if versions else None

    def get_version_count(self, memory_id: str) -> int:
        """获取版本数量"""
        return len(self.versions.get(memory_id, []))

    def compare_versions(
        self,
        memory_id: str,
        version1: int,
        version2: int
    ) -> Dict[str, Any]:
        """比较两个版本"""
        v1 = self.get_version(memory_id, version1)
        v2 = self.get_version(memory_id, version2)

        if not v1 or not v2:
            return {"error": "版本不存在"}

        # 计算差异
        content1 = v1.content
        content2 = v2.content

        # 简单差异计算
        lines1 = content1.split('\n')
        lines2 = content2.split('\n')

        added_lines = [line for line in lines2 if line not in lines1]
        removed_lines = [line for line in lines1 if line not in lines2]
        unchanged_lines = [line for line in lines1 if line in lines2]

        return {
            "memory_id": memory_id,
            "version1": version1,
            "version2": version2,
            "content_hash_changed": v1.content_hash != v2.content_hash,
            "lines_added": len(added_lines),
            "lines_removed": len(removed_lines),
            "lines_unchanged": len(unchanged_lines),
            "size_change": len(content2) - len(content1),
            "time_diff": v2.created_at - v1.created_at
        }

    def rollback_to_version(
        self,
        memory_id: str,
        version_number: int
    ) -> Optional[str]:
        """回滚到指定版本，返回该版本的内容"""
        version = self.get_version(memory_id, version_number)
        if not version:
            return None

        # 创建新版本记录回滚
        new_version = self.create_version(
            memory_id=memory_id,
            content=version.content,
            comment=f"回滚到版本 {version_number}",
            metadata={"rollback_from_version": self.current_version.get(memory_id, 0)}
        )

        return version.content

    def delete_old_versions(
        self,
        memory_id: str,
        keep_latest: int = 10
    ) -> int:
        """删除旧版本，保留最新的N个版本"""
        if memory_id not in self.versions:
            return 0

        versions = self.get_versions(memory_id)

        if len(versions) <= keep_latest:
            return 0

        # 获取要删除的版本
        versions_to_delete = versions[keep_latest:]

        # 从版本列表中删除
        for version in versions_to_delete:
            self.versions[memory_id].remove(version)

        self._save()
        return len(versions_to_delete)

    def get_statistics(self) -> Dict[str, Any]:
        """获取版本统计"""
        total_versions = sum(len(v) for v in self.versions.values())
        memories_with_versions = len(self.versions)

        memory_version_counts = {
            mem_id: len(versions)
            for mem_id, versions in self.versions.items()
        }

        most_versions = sorted(
            memory_version_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        return {
            "total_versions": total_versions,
            "memories_with_versions": memories_with_versions,
            "average_versions_per_memory": total_versions / memories_with_versions if memories_with_versions > 0 else 0,
            "most_versions_memories": most_versions
        }

    def clear_memory_versions(self, memory_id: str) -> int:
        """清空某个记忆的所有版本"""
        if memory_id not in self.versions:
            return 0

        count = len(self.versions[memory_id])
        del self.versions[memory_id]
        if memory_id in self.current_version:
            del self.current_version[memory_id]

        self._save()
        return count

    def _save(self) -> None:
        """保存到文件"""
        data = {
            "version": "1.0",
            "saved_at": time.time(),
            "versions": {
                mem_id: [v.to_dict() for v in versions]
                for mem_id, versions in self.versions.items()
            },
            "current_version": self.current_version
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

            if "versions" in data:
                for mem_id, version_list in data["versions"].items():
                    self.versions[mem_id] = [
                        MemoryVersion.from_dict(v) for v in version_list
                    ]

            if "current_version" in data:
                self.current_version = data["current_version"]

        except Exception as e:
            print(f"加载版本数据失败: {e}")


class EnhancedMemoryWithVersionControl:
    """
    增强的记忆系统（带版本控制功能）
    装饰器模式实现
    """

    def __init__(self, memory_system):
        self.memory_system = memory_system
        self.version_control = MemoryVersionControl()

    def add_with_version(
        self,
        text: str,
        task_id: str = "default",
        memory_level: Optional[str] = None,
        comment: Optional[str] = None
    ) -> str:
        """添加记忆并创建初始版本"""
        memory_id = self.memory_system.add(text, task_id, memory_level)

        # 创建初始版本
        self.version_control.create_version(
            memory_id=memory_id,
            content=text,
            comment=comment or "初始版本",
            metadata={"task_id": task_id, "level": memory_level}
        )

        return memory_id

    def update_with_version(
        self,
        memory_id: str,
        new_content: str,
        comment: Optional[str] = None
    ) -> Optional[MemoryVersion]:
        """更新记忆并创建新版本"""
        # 检查记忆是否存在
        if memory_id not in self.version_control.versions:
            return None

        # 创建新版本
        version = self.version_control.create_version(
            memory_id=memory_id,
            content=new_content,
            comment=comment or "更新版本"
        )

        return version

    def get_memory_versions(
        self,
        memory_id: str,
        limit: Optional[int] = None
    ) -> List[MemoryVersion]:
        """获取记忆的版本历史"""
        return self.version_control.get_versions(memory_id, limit)

    def get_version_details(
        self,
        memory_id: str,
        version_number: int
    ) -> Optional[Dict[str, Any]]:
        """获取特定版本的详细信息"""
        version = self.version_control.get_version(memory_id, version_number)
        if not version:
            return None

        return {
            "memory_id": version.memory_id,
            "version_number": version.version_number,
            "content": version.content,
            "comment": version.comment,
            "metadata": version.metadata,
            "created_at": version.created_at,
            "content_hash": version.content_hash
        }

    def compare_versions(
        self,
        memory_id: str,
        version1: int,
        version2: int
    ) -> Dict[str, Any]:
        """比较两个版本"""
        return self.version_control.compare_versions(memory_id, version1, version2)

    def rollback_to_version(
        self,
        memory_id: str,
        version_number: int
    ) -> Optional[str]:
        """回滚记忆到指定版本"""
        return self.version_control.rollback_to_version(memory_id, version_number)

    def get_version_statistics(self) -> Dict[str, Any]:
        """获取版本统计"""
        return self.version_control.get_statistics()
