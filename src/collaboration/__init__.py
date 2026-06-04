"""
记忆协作编辑功能模块
基于第一性原理：确定性、简洁性、可扩展性
"""

import os
import json
import time
import uuid
from typing import Dict, List, Optional, Any, Set, Tuple
from collections import defaultdict
from enum import Enum
from ..utils.logger import get_logger



class PermissionLevel(Enum):
    """权限级别"""
    VIEWER = 1  # 仅查看
    EDITOR = 2  # 可编辑
    OWNER = 3   # 所有者，可管理权限


class ShareType(Enum):
    """分享类型"""
    DIRECT = "direct"  # 直接分享给用户
    LINK = "link"      # 分享链接
    PUBLIC = "public"  # 公开分享


class ChangeType(Enum):
    """变更类型"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    PERMISSION_CHANGE = "permission"
    COMMENT = "comment"
    SHARE = "share"


class MemoryChange:
    """记忆变更记录"""

    def __init__(
        self,
        memory_id: str,
        user_id: str,
        change_type: ChangeType,
        content_before: Optional[str] = None,
        content_after: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.change_id = str(uuid.uuid4())
        self.memory_id = memory_id
        self.user_id = user_id
        self.change_type = change_type.value if isinstance(change_type, ChangeType) else change_type
        self.content_before = content_before
        self.content_after = content_after
        self.metadata = metadata or {}
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "change_id": self.change_id,
            "memory_id": self.memory_id,
            "user_id": self.user_id,
            "change_type": self.change_type,
            "content_before": self.content_before,
            "content_after": self.content_after,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryChange':
        change = cls(
            memory_id=data["memory_id"],
            user_id=data["user_id"],
            change_type=data["change_type"],
            content_before=data.get("content_before"),
            content_after=data.get("content_after"),
            metadata=data.get("metadata")
        )
        change.change_id = data.get("change_id", change.change_id)
        change.timestamp = data.get("timestamp", time.time())
        return change


class ShareLink:
    """分享链接"""

    def __init__(
        self,
        memory_id: str,
        creator_id: str,
        permission_level: PermissionLevel = PermissionLevel.VIEWER,
        expires_at: Optional[float] = None,
        max_uses: Optional[int] = None
    ):
        self.link_id = str(uuid.uuid4())
        self.memory_id = memory_id
        self.creator_id = creator_id
        self.permission_level = permission_level
        self.expires_at = expires_at
        self.max_uses = max_uses
        self.use_count = 0
        self.created_at = time.time()
        self.is_active = True

    def is_valid(self) -> bool:
        """检查链接是否有效"""
        if not self.is_active:
            return False
        if self.expires_at and time.time() > self.expires_at:
            return False
        if self.max_uses and self.use_count >= self.max_uses:
            return False
        return True

    def use(self) -> bool:
        """使用链接"""
        if not self.is_valid():
            return False
        self.use_count += 1
        if self.max_uses and self.use_count >= self.max_uses:
            self.is_active = False
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "link_id": self.link_id,
            "memory_id": self.memory_id,
            "creator_id": self.creator_id,
            "permission_level": self.permission_level.value,
            "expires_at": self.expires_at,
            "max_uses": self.max_uses,
            "use_count": self.use_count,
            "created_at": self.created_at,
            "is_active": self.is_active
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ShareLink':
        link = cls(
            memory_id=data["memory_id"],
            creator_id=data["creator_id"],
            permission_level=PermissionLevel(data["permission_level"]),
            expires_at=data.get("expires_at"),
            max_uses=data.get("max_uses")
        )
        link.link_id = data.get("link_id", link.link_id)
        link.use_count = data.get("use_count", 0)
        link.created_at = data.get("created_at", time.time())
        link.is_active = data.get("is_active", True)
        return link


class Comment:
    """评论"""

    def __init__(
        self,
        memory_id: str,
        user_id: str,
        content: str,
        reply_to: Optional[str] = None
    ):
        self.comment_id = str(uuid.uuid4())
        self.memory_id = memory_id
        self.user_id = user_id
        self.content = content
        self.reply_to = reply_to
        self.timestamp = time.time()
        self.is_resolved = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "comment_id": self.comment_id,
            "memory_id": self.memory_id,
            "user_id": self.user_id,
            "content": self.content,
            "reply_to": self.reply_to,
            "timestamp": self.timestamp,
            "is_resolved": self.is_resolved
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Comment':
        comment = cls(
            memory_id=data["memory_id"],
            user_id=data["user_id"],
            content=data["content"],
            reply_to=data.get("reply_to")
        )
        comment.comment_id = data.get("comment_id", comment.comment_id)
        comment.timestamp = data.get("timestamp", time.time())
        comment.is_resolved = data.get("is_resolved", False)
        return comment


class PermissionManager:
    """权限管理器"""

    def __init__(self):
        self._logger = get_logger()
        # 记忆ID -> (用户ID -> 权限级别)
        self.permissions: Dict[str, Dict[str, PermissionLevel]] = defaultdict(dict)

    def set_permission(
        self,
        memory_id: str,
        user_id: str,
        level: PermissionLevel
    ) -> bool:
        """设置用户权限"""
        self.permissions[memory_id][user_id] = level
        return True

    def get_permission(
        self,
        memory_id: str,
        user_id: str
    ) -> PermissionLevel:
        """获取用户权限"""
        return self.permissions.get(memory_id, {}).get(user_id, PermissionLevel.VIEWER)

    def check_permission(
        self,
        memory_id: str,
        user_id: str,
        required_level: PermissionLevel
    ) -> bool:
        """检查用户是否有足够的权限"""
        user_level = self.get_permission(memory_id, user_id)
        return user_level.value >= required_level.value

    def remove_permission(
        self,
        memory_id: str,
        user_id: str
    ) -> bool:
        """移除用户权限"""
        if memory_id in self.permissions and user_id in self.permissions[memory_id]:
            del self.permissions[memory_id][user_id]
            return True
        return False

    def get_users_with_access(
        self,
        memory_id: str
    ) -> Dict[str, PermissionLevel]:
        """获取有访问权限的用户列表"""
        return self.permissions.get(memory_id, {}).copy()

    def clear_permissions(
        self,
        memory_id: str
    ) -> int:
        """清空记忆的所有权限设置"""
        if memory_id in self.permissions:
            count = len(self.permissions[memory_id])
            del self.permissions[memory_id]
            return count
        return 0


class ConflictDetector:
    """冲突检测器"""

    @staticmethod
    def detect_conflict(
        change1: MemoryChange,
        change2: MemoryChange
    ) -> bool:
        """检测两个变更是否冲突"""
        if change1.memory_id != change2.memory_id:
            return False

        # 同一用户的变更不冲突
        if change1.user_id == change2.user_id:
            return False

        # 检查内容变更的重叠
        if (change1.change_type in [ChangeType.UPDATE.value, ChangeType.DELETE.value] and
            change2.change_type in [ChangeType.UPDATE.value, ChangeType.DELETE.value]):
            return True

        return False

    @staticmethod
    def suggest_resolution(
        change1: MemoryChange,
        change2: MemoryChange
    ) -> Dict[str, Any]:
        """提供冲突解决建议"""
        # 简单建议：保留较新的变更
        if change1.timestamp > change2.timestamp:
            return {
                "suggested": "keep_latest",
                "keep": change1.user_id,
                "timestamp": change1.timestamp
            }
        else:
            return {
                "suggested": "keep_latest",
                "keep": change2.user_id,
                "timestamp": change2.timestamp
            }

    @staticmethod
    def merge_changes(
        base: str,
        change1: MemoryChange,
        change2: MemoryChange
    ) -> str:
        """尝试合并两个变更（简单策略）"""
        # 保留两个变更的内容，用分隔符标记
        return f"=== {change1.user_id} ===\n{change1.content_after or base}\n\n=== {change2.user_id} ===\n{change2.content_after or base}"


class MemoryCollaboration:
    """记忆协作控制器"""

    def __init__(self, storage_path: str = "./data/collaboration.json"):
        self.storage_path = storage_path
        self.permission_manager = PermissionManager()
        self.conflict_detector = ConflictDetector()

        # 记忆ID -> 变更列表
        self.change_history: Dict[str, List[MemoryChange]] = defaultdict(list)
        # 当前正在编辑的用户
        self.active_editors: Dict[str, Set[str]] = defaultdict(set)
        # 分享链接
        self.share_links: Dict[str, ShareLink] = {}
        # 记忆ID -> 评论列表
        self.comments: Dict[str, List[Comment]] = defaultdict(list)

        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        self._load()

    def create_share_link(
        self,
        memory_id: str,
        creator_id: str,
        permission_level: PermissionLevel = PermissionLevel.VIEWER,
        expires_in_hours: Optional[int] = 24,
        max_uses: Optional[int] = None
    ) -> ShareLink:
        """创建分享链接"""
        # 检查创建者权限
        if not self.permission_manager.check_permission(memory_id, creator_id, PermissionLevel.OWNER):
            raise PermissionError("没有权限创建分享链接")

        expires_at = None
        if expires_in_hours:
            expires_at = time.time() + expires_in_hours * 3600

        link = ShareLink(
            memory_id=memory_id,
            creator_id=creator_id,
            permission_level=permission_level,
            expires_at=expires_at,
            max_uses=max_uses
        )

        self.share_links[link.link_id] = link
        self._save()

        # 记录分享事件
        self.make_change(
            memory_id=memory_id,
            user_id=creator_id,
            change_type=ChangeType.SHARE,
            metadata={
                "share_type": ShareType.LINK.value,
                "link_id": link.link_id
            }
        )

        return link

    def use_share_link(
        self,
        link_id: str,
        user_id: str
    ) -> Tuple[bool, Optional[str]]:
        """使用分享链接"""
        if link_id not in self.share_links:
            return False, "链接不存在"

        link = self.share_links[link_id]
        if not link.is_valid():
            return False, "链接已失效"

        # 使用链接
        if not link.use():
            return False, "链接使用失败"

        # 设置权限
        self.permission_manager.set_permission(link.memory_id, user_id, link.permission_level)
        self._save()

        return True, f"成功获取 {link.memory_id} 的访问权限"

    def revoke_share_link(self, link_id: str, revoker_id: str) -> bool:
        """撤销分享链接"""
        if link_id not in self.share_links:
            return False

        link = self.share_links[link_id]

        # 检查撤销者权限
        if not self.permission_manager.check_permission(link.memory_id, revoker_id, PermissionLevel.OWNER):
            return False

        link.is_active = False
        self._save()
        return True

    def get_share_links(self, memory_id: str) -> List[ShareLink]:
        """获取记忆的所有分享链接"""
        return [
            link for link in self.share_links.values()
            if link.memory_id == memory_id
        ]

    def add_comment(
        self,
        memory_id: str,
        user_id: str,
        content: str,
        reply_to: Optional[str] = None
    ) -> Optional[Comment]:
        """添加评论"""
        # 检查用户是否有访问权限
        if not self.permission_manager.check_permission(memory_id, user_id, PermissionLevel.VIEWER):
            return None

        comment = Comment(memory_id, user_id, content, reply_to)
        self.comments[memory_id].append(comment)

        # 记录评论变更
        self.make_change(
            memory_id=memory_id,
            user_id=user_id,
            change_type=ChangeType.COMMENT,
            metadata={"comment_id": comment.comment_id}
        )

        self._save()
        return comment

    def resolve_comment(self, comment_id: str, resolver_id: str) -> bool:
        """标记评论为已解决"""
        for memory_id, comments in self.comments.items():
            for comment in comments:
                if comment.comment_id == comment_id:
                    # 检查是否有编辑权限
                    if self.permission_manager.check_permission(memory_id, resolver_id, PermissionLevel.EDITOR):
                        comment.is_resolved = True
                        self._save()
                        return True
        return False

    def get_comments(
        self,
        memory_id: str,
        include_resolved: bool = False
    ) -> List[Comment]:
        """获取评论列表"""
        comments = self.comments.get(memory_id, [])
        if not include_resolved:
            comments = [c for c in comments if not c.is_resolved]
        # 按时间排序（最新在前）
        return sorted(comments, key=lambda c: c.timestamp, reverse=True)

    def start_editing(
        self,
        memory_id: str,
        user_id: str
    ) -> bool:
        """开始编辑"""
        if not self.permission_manager.check_permission(memory_id, user_id, PermissionLevel.EDITOR):
            return False

        self.active_editors[memory_id].add(user_id)
        return True

    def end_editing(
        self,
        memory_id: str,
        user_id: str
    ) -> bool:
        """结束编辑"""
        if user_id in self.active_editors.get(memory_id, set()):
            self.active_editors[memory_id].remove(user_id)
            return True
        return False

    def make_change(
        self,
        memory_id: str,
        user_id: str,
        change_type: ChangeType,
        content_before: Optional[str] = None,
        content_after: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[MemoryChange]:
        """记录变更"""
        # 检查权限
        required_level = PermissionLevel.EDITOR
        if change_type == ChangeType.PERMISSION_CHANGE:
            required_level = PermissionLevel.OWNER

        if not self.permission_manager.check_permission(memory_id, user_id, required_level):
            return None

        # 检测冲突
        change = MemoryChange(
            memory_id=memory_id,
            user_id=user_id,
            change_type=change_type,
            content_before=content_before,
            content_after=content_after,
            metadata=metadata
        )

        # 检查与最近变更的冲突
        last_change = self.get_latest_change(memory_id)
        if last_change and self.conflict_detector.detect_conflict(change, last_change):
            conflict_info = {
                "conflict": True,
                "suggestion": self.conflict_detector.suggest_resolution(change, last_change)
            }
            change.metadata["conflict_info"] = conflict_info

        # 保存变更
        self.change_history[memory_id].append(change)
        self._save()

        return change

    def get_change_history(
        self,
        memory_id: str,
        limit: Optional[int] = None,
        user_id: Optional[str] = None,
        change_types: Optional[List[ChangeType]] = None
    ) -> List[MemoryChange]:
        """获取变更历史"""
        changes = self.change_history.get(memory_id, [])

        # 按用户过滤
        if user_id:
            changes = [c for c in changes if c.user_id == user_id]

        # 按类型过滤
        if change_types:
            type_values = [t.value if isinstance(t, ChangeType) else t for t in change_types]
            changes = [c for c in changes if c.change_type in type_values]

        # 按时间排序（最新在前）
        changes = sorted(changes, key=lambda c: c.timestamp, reverse=True)

        # 限制数量
        if limit:
            changes = changes[:limit]

        return changes

    def get_latest_change(self, memory_id: str) -> Optional[MemoryChange]:
        """获取最新变更"""
        changes = self.get_change_history(memory_id, limit=1)
        return changes[0] if changes else None

    def get_active_editors(self, memory_id: str) -> Set[str]:
        """获取当前正在编辑的用户"""
        return self.active_editors.get(memory_id, set()).copy()

    def get_statistics(self) -> Dict[str, Any]:
        """获取协作统计"""
        total_changes = sum(len(changes) for changes in self.change_history.values())
        memories_with_changes = len(self.change_history)
        total_editors = sum(len(editors) for editors in self.active_editors.values())
        total_comments = sum(len(cmts) for cmts in self.comments.values())
        total_share_links = len(self.share_links)

        # 按用户统计变更数
        user_changes = defaultdict(int)
        for changes in self.change_history.values():
            for change in changes:
                user_changes[change.user_id] += 1

        most_active_users = sorted(
            user_changes.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        return {
            "total_changes": total_changes,
            "memories_with_changes": memories_with_changes,
            "current_active_editors": total_editors,
            "total_comments": total_comments,
            "total_share_links": total_share_links,
            "most_active_users": most_active_users
        }

    def revert_to_change(self, memory_id: str, change_id: str, user_id: str) -> Optional[MemoryChange]:
        """恢复到某个变更"""
        changes = self.change_history.get(memory_id, [])
        target_change = None

        for change in changes:
            if change.change_id == change_id:
                target_change = change
                break

        if not target_change:
            return None

        # 检查权限
        if not self.permission_manager.check_permission(memory_id, user_id, PermissionLevel.EDITOR):
            return None

        # 创建恢复变更
        current_content = None
        latest = self.get_latest_change(memory_id)
        if latest:
            current_content = latest.content_after

        reverted_content = target_change.content_after
        revert_change = self.make_change(
            memory_id=memory_id,
            user_id=user_id,
            change_type=ChangeType.UPDATE,
            content_before=current_content,
            content_after=reverted_content,
            metadata={"reverted_from": change_id}
        )

        return revert_change

    def _save(self) -> None:
        """保存到文件"""
        data = {
            "version": "2.0",
            "saved_at": time.time(),
            "change_history": {
                mem_id: [c.to_dict() for c in changes]
                for mem_id, changes in self.change_history.items()
            },
            "permissions": {
                mem_id: {uid: level.value for uid, level in perms.items()}
                for mem_id, perms in self.permission_manager.permissions.items()
            },
            "share_links": {
                link_id: link.to_dict()
                for link_id, link in self.share_links.items()
            },
            "comments": {
                mem_id: [c.to_dict() for c in cmts]
                for mem_id, cmts in self.comments.items()
            }
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

            if "change_history" in data:
                for mem_id, change_list in data["change_history"].items():
                    self.change_history[mem_id] = [
                        MemoryChange.from_dict(c) for c in change_list
                    ]

            if "permissions" in data:
                for mem_id, perms in data["permissions"].items():
                    for uid, level_val in perms.items():
                        self.permission_manager.set_permission(
                            mem_id, uid, PermissionLevel(level_val)
                        )

            if "share_links" in data:
                for link_id, link_data in data["share_links"].items():
                    self.share_links[link_id] = ShareLink.from_dict(link_data)

            if "comments" in data:
                for mem_id, comment_list in data["comments"].items():
                    self.comments[mem_id] = [
                        Comment.from_dict(c) for c in comment_list
                    ]

        except Exception as e:
            logger.info(f"加载协作数据失败: {e}")


class EnhancedMemoryWithCollaboration:
    """
    增强的记忆系统（带协作编辑功能）
    装饰器模式实现
    """

    def __init__(self, memory_system):
        self.memory_system = memory_system
        self.collaboration = MemoryCollaboration()

    def add_with_permission(
        self,
        text: str,
        task_id: str = "default",
        memory_level: Optional[str] = None,
        owner_id: str = "owner"
    ) -> str:
        """添加记忆并设置所有者权限"""
        memory_id = self.memory_system.add(text, task_id, memory_level)

        # 设置所有者权限
        self.collaboration.permission_manager.set_permission(
            memory_id, owner_id, PermissionLevel.OWNER
        )

        # 记录创建变更
        self.collaboration.make_change(
            memory_id=memory_id,
            user_id=owner_id,
            change_type=ChangeType.CREATE,
            content_after=text,
            metadata={"task_id": task_id, "level": memory_level}
        )

        return memory_id

    def collaborate_edit(
        self,
        memory_id: str,
        user_id: str,
        new_content: str,
        comment: Optional[str] = None
    ) -> Optional[MemoryChange]:
        """协作编辑记忆"""
        # 获取当前内容
        latest_change = self.collaboration.get_latest_change(memory_id)
        content_before = None
        if latest_change and latest_change.change_type in [ChangeType.CREATE.value, ChangeType.UPDATE.value]:
            content_before = latest_change.content_after

        # 记录编辑变更
        change = self.collaboration.make_change(
            memory_id=memory_id,
            user_id=user_id,
            change_type=ChangeType.UPDATE,
            content_before=content_before,
            content_after=new_content,
            metadata={"comment": comment}
        )

        return change

    def share_memory_direct(
        self,
        memory_id: str,
        from_user: str,
        to_user: str,
        level: PermissionLevel = PermissionLevel.VIEWER
    ) -> bool:
        """直接分享记忆给其他用户"""
        # 检查分享者是否有足够权限
        if not self.collaboration.permission_manager.check_permission(
            memory_id, from_user, PermissionLevel.OWNER
        ):
            return False

        # 设置权限
        self.collaboration.permission_manager.set_permission(memory_id, to_user, level)

        # 记录权限变更
        self.collaboration.make_change(
            memory_id=memory_id,
            user_id=from_user,
            change_type=ChangeType.SHARE,
            metadata={
                "share_type": ShareType.DIRECT.value,
                "target_user": to_user,
                "new_level": level.value
            }
        )

        return True

    def create_share_link(
        self,
        memory_id: str,
        creator_id: str,
        permission_level: PermissionLevel = PermissionLevel.VIEWER,
        expires_in_hours: Optional[int] = 24,
        max_uses: Optional[int] = None
    ) -> Optional[ShareLink]:
        """创建分享链接"""
        try:
            return self.collaboration.create_share_link(
                memory_id, creator_id, permission_level, expires_in_hours, max_uses
            )
        except PermissionError:
            return None

    def add_comment(
        self,
        memory_id: str,
        user_id: str,
        content: str,
        reply_to: Optional[str] = None
    ) -> Optional[Comment]:
        """添加评论"""
        return self.collaboration.add_comment(memory_id, user_id, content, reply_to)

    def get_change_history(
        self,
        memory_id: str,
        limit: Optional[int] = None,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取变更历史"""
        changes = self.collaboration.get_change_history(memory_id, limit, user_id)
        return [c.to_dict() for c in changes]

    def get_comments(
        self,
        memory_id: str,
        include_resolved: bool = False
    ) -> List[Dict[str, Any]]:
        """获取评论列表"""
        comments = self.collaboration.get_comments(memory_id, include_resolved)
        return [c.to_dict() for c in comments]

    def get_collaboration_statistics(self) -> Dict[str, Any]:
        """获取协作统计"""
        return self.collaboration.get_statistics()

    def get_shared_memories(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户有访问权限的所有记忆"""
        shared = []
        for memory_id, permissions in self.collaboration.permission_manager.permissions.items():
            if user_id in permissions:
                level = permissions[user_id]
                shared.append({
                    "memory_id": memory_id,
                    "permission_level": level.value,
                    "permission_name": level.name
                })
        return shared


# 全局单例
_global_collaboration: Optional[MemoryCollaboration] = None


def get_collaboration_system(storage_path: str = "./data/collaboration.json") -> MemoryCollaboration:
    """获取协作系统单例"""
    global _global_collaboration
    if _global_collaboration is None:
        _global_collaboration = MemoryCollaboration(storage_path)
    return _global_collaboration
