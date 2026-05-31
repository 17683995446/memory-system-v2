"""
记忆隔离与访问控制系统
基于第一性原理：公私记忆隔离、记忆开关控制、访问权限管理
"""
import time
from typing import Dict, List, Optional, Set
from enum import Enum
from dataclasses import dataclass


class MemoryType(Enum):
    """记忆类型"""
    PUBLIC = "public"      # 公共记忆
    PRIVATE = "private"   # 私有记忆
    SHARED = "shared"     # 共享记忆


class AccessLevel(Enum):
    """访问级别"""
    NONE = 0      # 禁止访问
    READ = 1      # 只读
    WRITE = 2     # 可写
    ADMIN = 3     # 管理员


@dataclass
class MemoryACL:
    """记忆访问控制列表"""
    item_id: str
    memory_type: MemoryType
    owner: str
    allowed_users: Set[str]
    access_level: Dict[str, AccessLevel]  # user -> access level
    created_at: float
    expires_at: Optional[float] = None


class MemoryIsolation:
    """记忆隔离器"""
    
    def __init__(self):
        self._acls: Dict[str, MemoryACL] = {}
        self._user_sessions: Dict[str, Set[str]] = {}  # user -> allowed memory ids
        self._memory_switches: Dict[str, bool] = {}  # user -> memory enabled
    
    def create_memory(
        self,
        item_id: str,
        memory_type: MemoryType,
        owner: str,
        allowed_users: List[str] = None
    ) -> MemoryACL:
        """创建记忆并设置ACL"""
        acl = MemoryACL(
            item_id=item_id,
            memory_type=memory_type,
            owner=owner,
            allowed_users=set(allowed_users) if allowed_users else set(),
            access_level={},
            created_at=time.time()
        )
        
        self._acls[item_id] = acl
        
        if memory_type == MemoryType.PRIVATE:
            self._user_sessions.setdefault(owner, set()).add(item_id)
        elif allowed_users:
            for user in allowed_users:
                self._user_sessions.setdefault(user, set()).add(item_id)
        
        return acl
    
    def check_access(self, item_id: str, user: str, required_level: AccessLevel = AccessLevel.READ) -> bool:
        """检查访问权限"""
        if item_id not in self._acls:
            return True  # 无ACL，默认允许
        
        acl = self._acls[item_id]
        
        # 检查是否过期
        if acl.expires_at and time.time() > acl.expires_at:
            return False
        
        # 所有者总是有权限
        if acl.owner == user:
            return True
        
        # 公共记忆
        if acl.memory_type == MemoryType.PUBLIC:
            return True
        
        # 私有记忆
        if acl.memory_type == MemoryType.PRIVATE:
            return acl.owner == user
        
        # 共享记忆
        if acl.memory_type == MemoryType.SHARED:
            if user in acl.allowed_users:
                user_level = acl.access_level.get(user, AccessLevel.NONE)
                return user_level.value >= required_level.value
        
        return False
    
    def grant_access(self, item_id: str, user: str, level: AccessLevel) -> bool:
        """授予访问权限"""
        if item_id not in self._acls:
            return False
        
        self._acls[item_id].access_level[user] = level
        self._acls[item_id].allowed_users.add(user)
        self._user_sessions.setdefault(user, set()).add(item_id)
        
        return True
    
    def revoke_access(self, item_id: str, user: str) -> bool:
        """撤销访问权限"""
        if item_id not in self._acls:
            return False
        
        if user in self._acls[item_id].access_level:
            del self._acls[item_id].access_level[user]
        
        if user in self._user_sessions:
            self._user_sessions[user].discard(item_id)
        
        return True
    
    def get_accessible_memories(self, user: str) -> List[str]:
        """获取用户可访问的记忆列表"""
        return list(self._user_sessions.get(user, set()))


class MemorySwitch:
    """记忆开关控制器"""
    
    def __init__(self, isolation: MemoryIsolation = None):
        self._isolation = isolation or MemoryIsolation()
        self._global_switch: bool = True  # 全局开关
        self._user_switches: Dict[str, bool] = {}  # 用户开关
        self._memory_switches: Dict[str, bool] = {}  # 记忆开关
        self._history: List[Dict] = []
    
    def enable_global(self) -> None:
        """启用全局记忆"""
        self._global_switch = True
        self._record_event('global', 'enable')
    
    def disable_global(self) -> None:
        """禁用全局记忆"""
        self._global_switch = False
        self._record_event('global', 'disable')
    
    def enable_user(self, user: str) -> None:
        """启用用户记忆"""
        self._user_switches[user] = True
        self._record_event(f'user:{user}', 'enable')
    
    def disable_user(self, user: str) -> None:
        """禁用用户记忆"""
        self._user_switches[user] = False
        self._record_event(f'user:{user}', 'disable')
    
    def enable_memory(self, memory_id: str) -> None:
        """启用特定记忆"""
        self._memory_switches[memory_id] = True
        self._record_event(f'memory:{memory_id}', 'enable')
    
    def disable_memory(self, memory_id: str) -> None:
        """禁用特定记忆"""
        self._memory_switches[memory_id] = False
        self._record_event(f'memory:{memory_id}', 'disable')
    
    def is_enabled(self, user: str = None, memory_id: str = None) -> bool:
        """检查是否启用"""
        # 全局检查
        if not self._global_switch:
            return False
        
        # 用户检查
        if user:
            user_switch = self._user_switches.get(user, True)
            if not user_switch:
                return False
        
        # 特定记忆检查
        if memory_id:
            memory_switch = self._memory_switches.get(memory_id, True)
            if not memory_switch:
                return False
        
        return True
    
    def _record_event(self, target: str, action: str) -> None:
        """记录开关事件"""
        self._history.append({
            'timestamp': time.time(),
            'target': target,
            'action': action
        })
    
    def get_history(self, limit: int = 100) -> List[Dict]:
        """获取开关历史"""
        return self._history[-limit:]


# 全局单例
_memory_isolation = None
_memory_switch = None


def get_memory_isolation() -> MemoryIsolation:
    global _memory_isolation
    if _memory_isolation is None:
        _memory_isolation = MemoryIsolation()
    return _memory_isolation


def get_memory_switch() -> MemorySwitch:
    global _memory_switch
    if _memory_switch is None:
        _memory_switch = MemorySwitch(get_memory_isolation())
    return _memory_switch
