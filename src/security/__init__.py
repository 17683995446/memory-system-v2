"""
记忆系统安全性和隐私保护模块
基于第一性原理：安全性、隐私性、可审计性
"""

import base64
import hashlib
import hmac
import json
import time
import secrets
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict


class Permission(Enum):
    """权限类型"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    SHARE = "share"
    ADMIN = "admin"


class ResourceType(Enum):
    """资源类型"""
    MEMORY = "memory"
    USER = "user"
    SYSTEM = "system"
    SETTINGS = "settings"


class AuditAction(Enum):
    """审计动作"""
    READ = "read"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    SHARE = "share"
    GRANT_ACCESS = "grant_access"
    REVOKE_ACCESS = "revoke_access"
    EXPORT_DATA = "export_data"
    IMPORT_DATA = "import_data"


class EncryptionLevel(Enum):
    """加密级别"""
    STANDARD = "standard"  # 标准加密
    ENHANCED = "enhanced"  # 增强加密
    MAXIMUM = "maximum"  # 最高加密


@dataclass
class EncryptionKey:
    """加密密钥"""
    key_id: str
    key: bytes
    salt: bytes
    level: EncryptionLevel
    created_at: float
    expires_at: Optional[float] = None


@dataclass
class AccessPolicy:
    """访问策略"""
    policy_id: str
    resource_id: str
    resource_type: ResourceType
    user_id: str
    permissions: Set[Permission]
    expires_at: Optional[float] = None
    created_at: float = field(default_factory=time.time)


@dataclass
class AuditLogEntry:
    """审计日志条目"""
    log_id: str
    action: AuditAction
    user_id: str
    resource_id: Optional[str] = None
    resource_type: Optional[ResourceType] = None
    timestamp: float = field(default_factory=time.time)
    success: bool = True
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PrivacyMask:
    """隐私掩码"""
    field_name: str
    mask_type: str  # full, partial, regex
    mask_pattern: str = ""
    replacement_char: str = "*"


class EncryptionManager:
    """加密管理器"""
    
    def __init__(self):
        self.keys: Dict[str, EncryptionKey] = {}
        self.derived_keys: Dict[str, bytes] = {}
    
    def generate_key(
        self,
        level: EncryptionLevel = EncryptionLevel.STANDARD,
        expires_in: Optional[float] = None
    ) -> EncryptionKey:
        """生成加密密钥"""
        key_id = secrets.token_urlsafe(16)
        salt = secrets.token_bytes(32)
        key = secrets.token_bytes(32)
        
        expires_at = time.time() + expires_in if expires_in else None
        
        encryption_key = EncryptionKey(
            key_id=key_id,
            key=key,
            salt=salt,
            level=level,
            created_at=time.time(),
            expires_at=expires_at
        )
        
        self.keys[key_id] = encryption_key
        return encryption_key
    
    def derive_key(
        self,
        password: str,
        salt: Optional[bytes] = None
    ) -> Tuple[bytes, bytes]:
        """从密码派生密钥"""
        if salt is None:
            salt = secrets.token_bytes(32)
        
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000,
            dklen=32
        )
        
        cache_key = hashlib.sha256(password.encode() + salt).hexdigest()
        self.derived_keys[cache_key] = key
        
        return key, salt
    
    def encrypt(
        self,
        data: bytes,
        key_id: Optional[str] = None,
        password: Optional[str] = None
    ) -> Dict[str, Any]:
        """加密数据"""
        if key_id and key_id in self.keys:
            key = self.keys[key_id].key
            salt = self.keys[key_id].salt
        elif password:
            key, salt = self.derive_key(password)
        else:
            # 如果没有指定密钥，生成新密钥
            encryption_key = self.generate_key()
            key = encryption_key.key
            salt = encryption_key.salt
            key_id = encryption_key.key_id
        
        # 简单的加密实现（实际使用中应使用AES等加密算法）
        encrypted_data = self._simple_encrypt(data, key)
        
        return {
            "encrypted": base64.b64encode(encrypted_data).decode('utf-8'),
            "key_id": key_id,
            "salt": base64.b64encode(salt).decode('utf-8'),
            "timestamp": time.time()
        }
    
    def decrypt(
        self,
        encrypted_data: Dict[str, Any],
        password: Optional[str] = None
    ) -> bytes:
        """解密数据"""
        try:
            data = base64.b64decode(encrypted_data["encrypted"].encode('utf-8'))
            key_id = encrypted_data.get("key_id")
            salt = base64.b64decode(encrypted_data["salt"].encode('utf-8'))
            
            if key_id and key_id in self.keys:
                key = self.keys[key_id].key
            elif password:
                key, _ = self.derive_key(password, salt)
            else:
                raise ValueError("No key or password provided")
            
            return self._simple_decrypt(data, key)
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")
    
    def _simple_encrypt(self, data: bytes, key: bytes) -> bytes:
        """简单加密（XOR，仅用于演示）"""
        result = bytearray()
        key_len = len(key)
        for i, byte in enumerate(data):
            result.append(byte ^ key[i % key_len])
        return bytes(result)
    
    def _simple_decrypt(self, data: bytes, key: bytes) -> bytes:
        """简单解密（XOR，仅用于演示）"""
        return self._simple_encrypt(data, key)
    
    def hash_data(self, data: bytes) -> str:
        """哈希数据"""
        return hashlib.sha256(data).hexdigest()
    
    def hmac_sign(self, data: bytes, key: bytes) -> str:
        """HMAC签名"""
        signature = hmac.new(key, data, hashlib.sha256).hexdigest()
        return signature
    
    def verify_hmac(self, data: bytes, key: bytes, signature: str) -> bool:
        """验证HMAC签名"""
        expected = self.hmac_sign(data, key)
        return hmac.compare_digest(expected, signature)
    
    def rotate_key(self, old_key_id: str) -> EncryptionKey:
        """轮换密钥"""
        if old_key_id not in self.keys:
            raise ValueError("Key not found")
        
        old_key = self.keys[old_key_id]
        new_key = self.generate_key(old_key.level)
        
        # 标记旧密钥为过期
        old_key.expires_at = time.time()
        
        return new_key


class AccessControlManager:
    """访问控制管理器"""
    
    def __init__(self):
        self.policies: Dict[str, List[AccessPolicy]] = defaultdict(list)
        self.user_roles: Dict[str, List[str]] = defaultdict(list)
        self.role_permissions: Dict[str, Set[Permission]] = defaultdict(set)
    
    def grant_access(
        self,
        user_id: str,
        resource_id: str,
        resource_type: ResourceType,
        permissions: List[Permission]
    ) -> AccessPolicy:
        """授予访问权限"""
        policy_id = secrets.token_urlsafe(16)
        
        policy = AccessPolicy(
            policy_id=policy_id,
            user_id=user_id,
            resource_id=resource_id,
            resource_type=resource_type,
            permissions=set(permissions)
        )
        
        self.policies[resource_id].append(policy)
        return policy
    
    def revoke_access(
        self,
        resource_id: str,
        user_id: Optional[str] = None,
        permission: Optional[Permission] = None
    ) -> int:
        """撤销访问权限"""
        if resource_id not in self.policies:
            return 0
        
        original_count = len(self.policies[resource_id])
        
        if user_id and permission:
            # 撤销特定用户的特定权限
            for policy in self.policies[resource_id]:
                if policy.user_id == user_id and permission in policy.permissions:
                    policy.permissions.remove(permission)
        elif user_id:
            # 撤销特定用户的所有权限
            self.policies[resource_id] = [
                p for p in self.policies[resource_id]
                if p.user_id != user_id
            ]
        else:
            # 撤销所有用户的权限
            self.policies[resource_id] = []
        
        return original_count - len(self.policies[resource_id])
    
    def check_permission(
        self,
        user_id: str,
        resource_id: str,
        permission: Permission
    ) -> bool:
        """检查用户是否有特定权限"""
        if resource_id not in self.policies:
            return False
        
        for policy in self.policies[resource_id]:
            if policy.user_id == user_id:
                # 检查是否过期
                if policy.expires_at and time.time() > policy.expires_at:
                    continue
                
                if permission in policy.permissions:
                    return True
        
        return False
    
    def get_user_permissions(
        self,
        user_id: str,
        resource_id: str
    ) -> Set[Permission]:
        """获取用户的所有权限"""
        permissions = set()
        
        if resource_id in self.policies:
            for policy in self.policies[resource_id]:
                if policy.user_id == user_id:
                    if policy.expires_at and time.time() > policy.expires_at:
                        continue
                    permissions.update(policy.permissions)
        
        return permissions
    
    def assign_role(self, user_id: str, role: str):
        """分配角色给用户"""
        if user_id not in self.user_roles:
            self.user_roles[user_id] = []
        if role not in self.user_roles[user_id]:
            self.user_roles[user_id].append(role)
    
    def define_role(self, role: str, permissions: List[Permission]):
        """定义角色和权限"""
        self.role_permissions[role] = set(permissions)


class AuditLogger:
    """审计日志记录器"""
    
    def __init__(self):
        self.logs: List[AuditLogEntry] = []
        self.listeners: List[callable] = []
        self.retention_period: float = 86400 * 30  # 默认保留30天
    
    def log_action(
        self,
        action: AuditAction,
        user_id: str,
        resource_id: Optional[str] = None,
        resource_type: Optional[ResourceType] = None,
        success: bool = True,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditLogEntry:
        """记录审计日志"""
        entry = AuditLogEntry(
            log_id=secrets.token_urlsafe(16),
            action=action,
            user_id=user_id,
            resource_id=resource_id,
            resource_type=resource_type,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {}
        )
        
        self.logs.append(entry)
        
        # 通知监听器
        for listener in self.listeners:
            try:
                listener(entry)
            except Exception:
                pass
        
        return entry
    
    def query_logs(
        self,
        user_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        resource_id: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        limit: int = 100
    ) -> List[AuditLogEntry]:
        """查询审计日志"""
        results = []
        
        for entry in self.logs:
            if user_id and entry.user_id != user_id:
                continue
            if action and entry.action != action:
                continue
            if resource_id and entry.resource_id != resource_id:
                continue
            if start_time and entry.timestamp < start_time:
                continue
            if end_time and entry.timestamp > end_time:
                continue
            
            results.append(entry)
            if len(results) >= limit:
                break
        
        return results
    
    def add_listener(self, listener: callable):
        """添加日志监听器"""
        self.listeners.append(listener)
    
    def cleanup_old_logs(self) -> int:
        """清理过期日志"""
        cutoff = time.time() - self.retention_period
        original_count = len(self.logs)
        self.logs = [
            entry for entry in self.logs
            if entry.timestamp > cutoff
        ]
        return original_count - len(self.logs)


class PrivacyManager:
    """隐私管理器"""
    
    def __init__(self):
        self.masks: Dict[str, List[PrivacyMask]] = defaultdict(list)
        self.sensitive_fields: Set[str] = set()
        self.data_classification: Dict[str, str] = {}
    
    def add_sensitive_field(self, field_name: str, classification: str = "confidential"):
        """添加敏感字段"""
        self.sensitive_fields.add(field_name)
        self.data_classification[field_name] = classification
    
    def add_mask(
        self,
        resource_type: str,
        field_name: str,
        mask_type: str = "partial",
        mask_pattern: str = "",
        replacement_char: str = "*"
    ):
        """添加隐私掩码"""
        mask = PrivacyMask(
            field_name=field_name,
            mask_type=mask_type,
            mask_pattern=mask_pattern,
            replacement_char=replacement_char
        )
        self.masks[resource_type].append(mask)
    
    def mask_data(
        self,
        data: Dict[str, Any],
        resource_type: str
    ) -> Dict[str, Any]:
        """掩码化数据"""
        if resource_type not in self.masks:
            return data
        
        masked_data = data.copy()
        
        for mask in self.masks[resource_type]:
            if mask.field_name in masked_data:
                original = str(masked_data[mask.field_name])
                
                if mask.mask_type == "full":
                    masked_data[mask.field_name] = mask.replacement_char * len(original)
                elif mask.mask_type == "partial":
                    if len(original) <= 4:
                        masked_data[mask.field_name] = mask.replacement_char * len(original)
                    else:
                        # 保留首尾各2个字符
                        masked_data[mask.field_name] = (
                            original[:2] +
                            mask.replacement_char * (len(original) - 4) +
                            original[-2:]
                        )
        
        return masked_data
    
    def anonymize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """匿名化数据"""
        anonymized = data.copy()
        
        # 移除或替换可能识别身份的字段
        identifiable_fields = ["name", "email", "phone", "address", "user_id"]
        for field in identifiable_fields:
            if field in anonymized:
                anonymized[field] = f"anonymized_{hashlib.md5(str(anonymized[field]).encode()).hexdigest()[:8]}"
        
        return anonymized
    
    def export_privacy_report(self, user_id: str) -> Dict[str, Any]:
        """导出隐私报告"""
        return {
            "user_id": user_id,
            "generated_at": time.time(),
            "sensitive_fields": list(self.sensitive_fields),
            "data_classifications": self.data_classification,
            "masks": {
                rt: [
                    {
                        "field": m.field_name,
                        "type": m.mask_type
                    }
                    for m in masks
                ]
                for rt, masks in self.masks.items()
            }
        }


class SecurityManager:
    """综合安全管理器"""
    
    def __init__(self):
        self.encryption = EncryptionManager()
        self.access_control = AccessControlManager()
        self.audit = AuditLogger()
        self.privacy = PrivacyManager()
        self.threat_monitor = ThreatMonitor()
    
    def secure_memory(
        self,
        memory_data: Dict[str, Any],
        user_id: str,
        encrypt: bool = True
    ) -> Dict[str, Any]:
        """安全化记忆数据"""
        secured = memory_data.copy()
        
        # 加密敏感字段
        if encrypt:
            if "content" in secured:
                content_bytes = json.dumps(secured["content"]).encode('utf-8')
                secured["content"] = self.encryption.encrypt(content_bytes)
        
        # 审计记录
        self.audit.log_action(
            AuditAction.CREATE,
            user_id,
            secured.get("id"),
            ResourceType.MEMORY
        )
        
        return secured
    
    def access_memory(
        self,
        memory_id: str,
        user_id: str,
        permission: Permission = Permission.READ
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """访问记忆（带权限检查）"""
        # 检查权限
        has_permission = self.access_control.check_permission(
            user_id, memory_id, permission
        )
        
        # 审计记录
        self.audit.log_action(
            AuditAction.READ,
            user_id,
            memory_id,
            ResourceType.MEMORY,
            success=has_permission
        )
        
        return has_permission, None


class ThreatMonitor:
    """威胁监控器"""
    
    def __init__(self):
        self.threat_logs: List[Dict[str, Any]] = []
        self.rate_limit_threshold: Dict[str, int] = {
            "login": 5,
            "read": 100,
            "write": 50
        }
        self.user_activity: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    
    def monitor_activity(
        self,
        user_id: str,
        action_type: str,
        check_rate_limit: bool = True
    ) -> bool:
        """监控用户活动"""
        self.user_activity[user_id][action_type] += 1
        
        if check_rate_limit and action_type in self.rate_limit_threshold:
            if self.user_activity[user_id][action_type] > self.rate_limit_threshold[action_type]:
                self._log_threat(
                    user_id,
                    "rate_limit_exceeded",
                    {
                        "action_type": action_type,
                        "count": self.user_activity[user_id][action_type]
                    }
                )
                return False
        
        return True
    
    def _log_threat(
        self,
        user_id: str,
        threat_type: str,
        details: Dict[str, Any]
    ):
        """记录威胁"""
        self.threat_logs.append({
            "user_id": user_id,
            "type": threat_type,
            "details": details,
            "timestamp": time.time()
        })
    
    def get_threats(
        self,
        user_id: Optional[str] = None,
        since: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """获取威胁记录"""
        threats = self.threat_logs
        
        if user_id:
            threats = [t for t in threats if t["user_id"] == user_id]
        
        if since:
            threats = [t for t in threats if t["timestamp"] >= since]
        
        return threats


# 全局安全管理器
_global_security: Optional[SecurityManager] = None


def get_security_manager() -> SecurityManager:
    """获取安全管理器单例"""
    global _global_security
    if _global_security is None:
        _global_security = SecurityManager()
    return _global_security
