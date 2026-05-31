"""
第45阶段测试：记忆系统安全性和隐私保护
遵循"图难于其易，为大于其细"原则
"""

import sys
import os
import time
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.security import (
    SecurityManager,
    EncryptionManager,
    AccessControlManager,
    AuditLogger,
    PrivacyManager,
    ThreatMonitor,
    Permission,
    ResourceType,
    AuditAction,
    EncryptionLevel,
    get_security_manager
)


def test_encryption():
    """测试加密和解密"""
    print("\n=== 测试加密和解密 ===")
    
    enc_manager = EncryptionManager()
    
    # 生成密钥
    key = enc_manager.generate_key(EncryptionLevel.STANDARD)
    assert key is not None
    assert key.key_id in enc_manager.keys
    
    # 测试加密和解密
    original_data = b"Secret memory content"
    encrypted = enc_manager.encrypt(original_data, key_id=key.key_id)
    assert encrypted is not None
    assert "encrypted" in encrypted
    assert "key_id" in encrypted
    
    decrypted = enc_manager.decrypt(encrypted)
    assert decrypted == original_data
    print("✓ 加密和解密成功")
    
    # 测试密码派生加密
    password = "mypassword123"
    encrypted_pwd = enc_manager.encrypt(original_data, password=password)
    decrypted_pwd = enc_manager.decrypt(encrypted_pwd, password=password)
    assert decrypted_pwd == original_data
    print("✓ 密码加密和解密成功")
    
    # 测试哈希
    hash_value = enc_manager.hash_data(original_data)
    assert len(hash_value) > 0
    print("✓ 哈希功能正常")
    
    # 测试HMAC
    hmac_value = enc_manager.hmac_sign(original_data, key.key)
    assert hmac_value is not None
    assert enc_manager.verify_hmac(original_data, key.key, hmac_value)
    print("✓ HMAC签名和验证正常")
    
    # 测试密钥轮换
    new_key = enc_manager.rotate_key(key.key_id)
    assert new_key is not None
    assert key.expires_at is not None
    print("✓ 密钥轮换正常")
    
    print("✓ 加密功能测试通过")


def test_access_control():
    """测试访问控制"""
    print("\n=== 测试访问控制 ===")
    
    ac_manager = AccessControlManager()
    
    user1 = "user1"
    user2 = "user2"
    resource_id = "memory123"
    resource_type = ResourceType.MEMORY
    
    # 授予权限
    policy = ac_manager.grant_access(
        user1, resource_id, resource_type, [Permission.READ, Permission.WRITE]
    )
    assert policy is not None
    print("✓ 权限授予成功")
    
    # 检查权限
    assert ac_manager.check_permission(user1, resource_id, Permission.READ)
    assert ac_manager.check_permission(user1, resource_id, Permission.WRITE)
    assert not ac_manager.check_permission(user1, resource_id, Permission.DELETE)
    print("✓ 权限检查正常")
    
    # 获取用户权限
    user_perms = ac_manager.get_user_permissions(user1, resource_id)
    assert len(user_perms) == 2
    assert Permission.READ in user_perms
    print("✓ 用户权限获取正常")
    
    # 检查无权限用户
    assert not ac_manager.check_permission(user2, resource_id, Permission.READ)
    
    # 撤销权限
    ac_manager.revoke_access(resource_id, user1, Permission.WRITE)
    print("✓ 权限撤销成功")
    
    assert not ac_manager.check_permission(user1, resource_id, Permission.WRITE)
    assert ac_manager.check_permission(user1, resource_id, Permission.READ)
    
    # 测试角色
    ac_manager.define_role("editor", [Permission.READ, Permission.WRITE])
    ac_manager.assign_role(user2, "editor")
    print("✓ 角色定义和分配成功")
    
    print("✓ 访问控制功能测试通过")


def test_audit_logger():
    """测试审计日志"""
    print("\n=== 测试审计日志 ===")
    
    audit_logger = AuditLogger()
    
    # 记录日志
    entry1 = audit_logger.log_action(
        AuditAction.CREATE, "user1", "mem123", ResourceType.MEMORY, success=True
    )
    entry2 = audit_logger.log_action(
        AuditAction.READ, "user1", "mem123", ResourceType.MEMORY, success=True
    )
    entry3 = audit_logger.log_action(
        AuditAction.DELETE, "user2", "mem123", ResourceType.MEMORY, success=False
    )
    
    assert entry1 is not None
    assert len(audit_logger.logs) == 3
    print("✓ 日志记录成功")
    
    # 查询日志
    user_logs = audit_logger.query_logs(user_id="user1")
    assert len(user_logs) == 2
    
    read_logs = audit_logger.query_logs(action=AuditAction.READ)
    assert len(read_logs) == 1
    
    # 测试清理旧日志
    audit_logger.retention_period = 0  # 立即过期
    audit_logger.cleanup_old_logs()
    print("✓ 日志查询和清理功能正常")
    
    print("✓ 审计日志功能测试通过")


def test_privacy():
    """测试隐私保护"""
    print("\n=== 测试隐私保护 ===")
    
    privacy_manager = PrivacyManager()
    
    # 测试敏感字段
    privacy_manager.add_sensitive_field("password", "highly_confidential")
    assert "password" in privacy_manager.sensitive_fields
    print("✓ 敏感字段添加成功")
    
    # 测试掩码
    test_data = {
        "email": "test@example.com",
        "phone": "1234567890",
        "name": "John Doe"
    }
    
    privacy_manager.add_mask("user", "email", "partial")
    privacy_manager.add_mask("user", "phone", "full")
    
    masked = privacy_manager.mask_data(test_data, "user")
    assert "*" in masked["email"]
    assert masked["phone"] == "**********"
    print("✓ 数据掩码功能正常")
    
    # 测试匿名化
    anonymized = privacy_manager.anonymize(test_data)
    assert anonymized["email"] != test_data["email"]
    assert anonymized["email"].startswith("anonymized_")
    print("✓ 数据匿名化功能正常")
    
    # 测试隐私报告
    report = privacy_manager.export_privacy_report("user123")
    assert "user_id" in report
    assert "sensitive_fields" in report
    assert "masks" in report
    print("✓ 隐私报告导出正常")
    
    print("✓ 隐私保护功能测试通过")


def test_threat_monitor():
    """测试威胁监控"""
    print("\n=== 测试威胁监控 ===")
    
    monitor = ThreatMonitor()
    
    # 测试正常活动
    for _ in range(3):
        allowed = monitor.monitor_activity("user1", "login")
        assert allowed
    
    # 测试速率限制
    for i in range(10):
        allowed = monitor.monitor_activity("user2", "login")
        if i >= 5:
            assert not allowed
    
    threats = monitor.get_threats(user_id="user2")
    assert len(threats) > 0
    print("✓ 速率限制和威胁监控正常")
    
    # 测试获取所有威胁
    all_threats = monitor.get_threats()
    assert len(all_threats) > 0
    print("✓ 威胁查询功能正常")
    
    print("✓ 威胁监控功能测试通过")


def test_security_manager():
    """测试安全管理器"""
    print("\n=== 测试安全管理器 ===")
    
    security_manager = SecurityManager()
    
    # 测试记忆安全化
    memory_data = {
        "id": "mem123",
        "content": "Sensitive memory content",
        "tags": ["private"]
    }
    
    secured = security_manager.secure_memory(memory_data, "user1", encrypt=True)
    assert secured is not None
    assert "id" in secured
    assert "content" in secured
    assert isinstance(secured["content"], dict)  # 加密后的内容是字典
    print("✓ 记忆安全化成功")
    
    # 测试访问记忆
    security_manager.access_control.grant_access(
        "user1", "mem123", ResourceType.MEMORY, [Permission.READ]
    )
    
    has_access, _ = security_manager.access_memory("mem123", "user1")
    assert has_access
    
    has_access_no_perm, _ = security_manager.access_memory("mem123", "user2")
    assert not has_access_no_perm
    print("✓ 记忆访问控制正常")
    
    # 审计日志应该有记录
    assert len(security_manager.audit.logs) >= 2
    print("✓ 审计记录正常")
    
    print("✓ 安全管理器功能测试通过")


def test_global_instance():
    """测试全局单例"""
    print("\n=== 测试全局单例 ===")
    
    mgr1 = get_security_manager()
    mgr2 = get_security_manager()
    
    assert mgr1 is mgr2
    print("✓ 全局单例测试通过")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("第45阶段测试：记忆系统安全性和隐私保护")
    print("遵循原则：图难于其易，为大于其细")
    print("=" * 60)
    
    try:
        test_encryption()
        test_access_control()
        test_audit_logger()
        test_privacy()
        test_threat_monitor()
        test_security_manager()
        test_global_instance()
        
        print("\n" + "=" * 60)
        print("✓ 所有第45阶段测试通过！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
