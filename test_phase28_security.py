"""
第28阶段测试：记忆安全与访问控制功能
"""

import sys
import os
import time
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.memory import get_memory_system
from src.security import (
    Permission,
    Role,
    EncryptionManager,
    AccessControlManager,
    AccessLogger,
    EnhancedMemoryWithSecurity
)


def test_encryption():
    """测试加密解密功能"""
    print("\n" + "=" * 60)
    print("测试 1：加密解密功能")
    print("=" * 60)

    encryption = EncryptionManager("test-secret-key")
    
    # 测试数据
    plaintext = "这是一条机密的记忆内容，需要加密保护！"
    print(f"\n原文: {plaintext}")
    
    # 加密
    ciphertext = encryption.encrypt(plaintext)
    print(f"加密后: {ciphertext[:50]}...")
    assert ciphertext != plaintext
    print("  ✓ 加密成功")
    
    # 解密
    decrypted = encryption.decrypt(ciphertext)
    print(f"解密后: {decrypted}")
    assert decrypted == plaintext
    print("  ✓ 解密成功")
    
    # 测试哈希
    hash1 = encryption.hash(plaintext)
    hash2 = encryption.hash(plaintext)
    assert hash1 == hash2
    print("  ✓ 哈希功能正常")
    
    # 测试签名
    signature = encryption.sign(plaintext)
    assert encryption.verify(plaintext, signature)
    assert not encryption.verify(plaintext + "x", signature)
    print("  ✓ 签名验证功能正常")
    
    print("\n✓ 加密解密测试通过！")
    return True


def test_access_control():
    """测试访问控制功能"""
    print("\n" + "=" * 60)
    print("测试 2：访问控制功能")
    print("=" * 60)

    # 清理测试数据
    test_path = "./data/test_security"
    if os.path.exists(test_path):
        shutil.rmtree(test_path)
    
    ac = AccessControlManager(test_path)
    
    # 测试角色分配
    ac.assign_role("user1", Role.GUEST)
    ac.assign_role("user2", Role.USER)
    ac.assign_role("user3", Role.EDITOR)
    ac.assign_role("user4", Role.ADMIN)
    
    assert ac.get_user_role("user1") == Role.GUEST
    assert ac.get_user_role("user2") == Role.USER
    assert ac.get_user_role("user3") == Role.EDITOR
    assert ac.get_user_role("user4") == Role.ADMIN
    print("  ✓ 角色分配功能正常")
    
    # 测试角色权限
    assert not ac.has_permission("user1", Permission.WRITE)
    assert ac.has_permission("user2", Permission.WRITE)
    assert not ac.has_permission("user2", Permission.DELETE)
    assert ac.has_permission("user3", Permission.DELETE)
    assert ac.has_permission("user4", Permission.ADMIN)
    print("  ✓ 角色权限检查正常")
    
    # 测试额外权限授予
    ac.grant_permission("user1", Permission.WRITE)
    assert ac.has_permission("user1", Permission.WRITE)
    print("  ✓ 额外权限授予正常")
    
    # 测试权限撤销
    ac.revoke_permission("user1", Permission.WRITE)
    assert not ac.has_permission("user1", Permission.WRITE)
    print("  ✓ 权限撤销正常")
    
    # 测试记忆级权限
    mem_id = "test-memory-001"
    ac.set_memory_permission(mem_id, "user2", Permission.READ, allow=False)
    assert ac.check_memory_permission(mem_id, "user1", Permission.READ)
    assert not ac.check_memory_permission(mem_id, "user2", Permission.READ)
    print("  ✓ 记忆级权限控制正常")
    
    print("\n✓ 访问控制测试通过！")
    return True


def test_access_logger():
    """测试访问日志功能"""
    print("\n" + "=" * 60)
    print("测试 3：访问日志功能")
    print("=" * 60)

    # 清理测试数据
    test_path = "./data/test_security_logs"
    if os.path.exists(test_path):
        shutil.rmtree(test_path)
    
    logger = AccessLogger(test_path)
    
    # 记录一些日志
    logger.log_access("user1", "add", "mem1", True, {"source": "test"})
    logger.log_access("user1", "get", "mem1", True)
    logger.log_access("user2", "get", "mem1", False, {"reason": "permission denied"})
    logger.log_access("user1", "delete", "mem1", True)
    time.sleep(0.1)  # 确保时间戳不同
    
    print("  ✓ 日志记录成功")
    
    # 获取日志
    logs = logger.get_logs()
    assert len(logs) == 4
    print(f"  ✓ 获取到 {len(logs)} 条日志")
    
    # 按用户过滤
    user1_logs = logger.get_logs(user_id="user1")
    assert len(user1_logs) == 3
    print(f"  ✓ 用户过滤正常，user1有 {len(user1_logs)} 条日志")
    
    # 按操作过滤
    add_logs = logger.get_logs(action="add")
    assert len(add_logs) == 1
    print(f"  ✓ 操作过滤正常，add有 {len(add_logs)} 条日志")
    
    # 检查日志内容
    last_log = logs[0]
    assert "log_id" in last_log
    assert "timestamp" in last_log
    assert "user_id" in last_log
    assert "action" in last_log
    assert "success" in last_log
    print("  ✓ 日志内容完整")
    
    print("\n✓ 访问日志测试通过！")
    return True


def test_enhanced_memory():
    """测试增强记忆系统（带安全功能）"""
    print("\n" + "=" * 60)
    print("测试 4：增强记忆系统（带安全功能）")
    print("=" * 60)

    # 清理测试数据
    if os.path.exists("./data/security"):
        shutil.rmtree("./data/security")
    if os.path.exists("./data/test_security_logs"):
        shutil.rmtree("./data/test_security_logs")
    
    # 创建记忆系统
    memory = get_memory_system()
    
    # 清空现有数据
    memory.l1.clear()
    if hasattr(memory.l2, 'clear'):
        memory.l2.clear()
    
    # 创建访问控制管理器并分配角色
    ac = AccessControlManager()
    ac.assign_role("guest_user", Role.GUEST)
    ac.assign_role("normal_user", Role.USER)
    ac.assign_role("editor_user", Role.EDITOR)
    
    # 测试正常用户添加记忆
    normal_memory = EnhancedMemoryWithSecurity(memory, user_id="normal_user")
    mem_id1 = normal_memory.add("这是普通用户添加的记忆", "test", "l2")
    assert mem_id1 is not None
    print("  ✓ 普通用户可以添加记忆")
    
    # 测试加密添加
    mem_id2 = normal_memory.add("这是加密的机密记忆", "test", "l2", encrypt=True)
    assert mem_id2 is not None
    print("  ✓ 加密记忆添加成功")
    
    # 测试读取记忆
    mem1 = normal_memory.get(mem_id1)
    assert mem1 is not None
    print("  ✓ 正常读取记忆成功")
    
    # 测试访客用户（只有读权限）
    guest_memory = EnhancedMemoryWithSecurity(memory, user_id="guest_user")
    mem1_guest = guest_memory.get(mem_id1)
    assert mem1_guest is not None
    print("  ✓ 访客用户可以读取记忆")
    
    # 访客用户不能添加记忆
    guest_add_result = guest_memory.add("访客尝试添加记忆", "test", "l2")
    assert guest_add_result is None
    print("  ✓ 访客用户不能添加记忆（权限控制正常）")
    
    # 测试编辑用户删除
    editor_memory = EnhancedMemoryWithSecurity(memory, user_id="editor_user")
    delete_success = editor_memory.delete(mem_id1)
    assert delete_success
    print("  ✓ 编辑用户可以删除记忆")
    
    # 检查访问日志
    logger = AccessLogger()
    logs = logger.get_logs()
    assert len(logs) >= 5
    print(f"  ✓ 访问日志记录正常，共 {len(logs)} 条")
    
    print("\n✓ 增强记忆系统测试通过！")
    return True


def test_integration():
    """测试完整集成流程"""
    print("\n" + "=" * 60)
    print("测试 5：完整集成测试")
    print("=" * 60)

    # 清理测试数据
    if os.path.exists("./data/security"):
        shutil.rmtree("./data/security")
    
    # 创建记忆系统
    memory = get_memory_system()
    
    # 清空
    memory.l1.clear()
    if hasattr(memory.l2, 'clear'):
        memory.l2.clear()
    
    # 设置访问控制
    ac = AccessControlManager()
    ac.assign_role("admin", Role.ADMIN)
    ac.assign_role("alice", Role.USER)
    ac.assign_role("bob", Role.GUEST)
    
    # Admin添加一些记忆
    admin_memory = EnhancedMemoryWithSecurity(memory, user_id="admin")
    
    mem_ids = []
    contents = [
        "项目计划 Q3 2026",
        "客户会议记录",
        "机密财务数据"
    ]
    
    for i, content in enumerate(contents):
        encrypt = (i == 2)  # 第三条加密
        mem_id = admin_memory.add(content, "integration", "l2", encrypt=encrypt)
        mem_ids.append(mem_id)
        print(f"  ✓ 添加记忆 {i+1}: {mem_id} (加密: {encrypt})")
    
    assert len(mem_ids) == 3
    
    # 设置记忆级权限：Bob不能看财务数据
    ac.set_memory_permission(mem_ids[2], "bob", Permission.READ, allow=False)
    
    # Alice尝试操作
    alice_memory = EnhancedMemoryWithSecurity(memory, user_id="alice")
    
    # Alice可以读前两条
    mem1 = alice_memory.get(mem_ids[0])
    mem2 = alice_memory.get(mem_ids[1])
    assert mem1 is not None
    assert mem2 is not None
    print("  ✓ Alice可以读取正常记忆")
    
    # Alice可以添加
    alice_mem = alice_memory.add("Alice的笔记", "alice", "l2")
    assert alice_mem is not None
    print("  ✓ Alice可以添加记忆")
    
    # Bob尝试操作
    bob_memory = EnhancedMemoryWithSecurity(memory, user_id="bob")
    
    # Bob可以读前两条
    bob_mem1 = bob_memory.get(mem_ids[0])
    assert bob_mem1 is not None
    print("  ✓ Bob可以读取公开记忆")
    
    # Bob不能读第三条
    bob_mem3 = bob_memory.get(mem_ids[2])
    assert bob_mem3 is None
    print("  ✓ Bob不能读取机密记忆（记忆级权限控制正常）")
    
    # Bob不能添加
    bob_add = bob_memory.add("Bob尝试添加", "bob", "l2")
    assert bob_add is None
    print("  ✓ Bob不能添加记忆（角色权限控制正常）")
    
    # 检查完整日志
    logger = AccessLogger()
    all_logs = logger.get_logs(limit=50)
    print(f"  ✓ 完整日志记录正常，共 {len(all_logs)} 条")
    
    print("\n✓ 集成测试通过！")
    return True


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("第28阶段测试：记忆安全与访问控制功能")
    print("=" * 60)

    all_passed = True

    try:
        passed = test_encryption()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试1失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_access_control()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试2失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_access_logger()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试3失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_enhanced_memory()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试4失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_integration()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试5失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("✓ 所有测试通过！")
    else:
        print("✗ 部分测试失败")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
