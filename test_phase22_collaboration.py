"""
第22阶段测试：记忆协作编辑功能
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.memory import get_memory_system
from src.collaboration import (
    MemoryCollaboration,
    MemoryChange,
    PermissionLevel,
    ChangeType,
    ConflictDetector,
    EnhancedMemoryWithCollaboration
)


def test_permission_management():
    """测试权限管理功能"""
    print("\n" + "=" * 60)
    print("测试 1: 权限管理功能")
    print("=" * 60)

    test_path = "./data/test_collab_perm.json"
    if os.path.exists(test_path):
        os.remove(test_path)

    collab = MemoryCollaboration(test_path)

    # 设置权限
    memory_id = "mem_001"

    # 所有者设置
    collab.permission_manager.set_permission(memory_id, "user_owner", PermissionLevel.OWNER)
    collab.permission_manager.set_permission(memory_id, "user_editor", PermissionLevel.EDITOR)
    collab.permission_manager.set_permission(memory_id, "user_viewer", PermissionLevel.VIEWER)

    # 检查权限
    print("\n权限设置完成")

    # 验证权限级别
    assert collab.permission_manager.check_permission(memory_id, "user_owner", PermissionLevel.OWNER) == True
    assert collab.permission_manager.check_permission(memory_id, "user_editor", PermissionLevel.EDITOR) == True
    assert collab.permission_manager.check_permission(memory_id, "user_viewer", PermissionLevel.EDITOR) == False

    # 获取用户列表
    users = collab.permission_manager.get_users_with_access(memory_id)
    print(f"\n有访问权限的用户: {list(users.keys())}")
    assert len(users) == 3

    # 移除权限
    collab.permission_manager.remove_permission(memory_id, "user_viewer")
    users = collab.permission_manager.get_users_with_access(memory_id)
    assert len(users) == 2

    print("\n✓ 权限管理功能测试通过！")

    # 清理
    try:
        os.remove(test_path)
    except:
        pass

    return True


def test_change_tracking():
    """测试变更追踪功能"""
    print("\n" + "=" * 60)
    print("测试 2: 变更追踪功能")
    print("=" * 60)

    test_path = "./data/test_collab_change.json"
    if os.path.exists(test_path):
        os.remove(test_path)

    collab = MemoryCollaboration(test_path)

    memory_id = "mem_001"

    # 先设置权限
    collab.permission_manager.set_permission(memory_id, "user_1", PermissionLevel.OWNER)

    # 创建变更
    change1 = collab.make_change(
        memory_id=memory_id,
        user_id="user_1",
        change_type=ChangeType.CREATE,
        content_after="初始内容"
    )

    change2 = collab.make_change(
        memory_id=memory_id,
        user_id="user_1",
        change_type=ChangeType.UPDATE,
        content_before="初始内容",
        content_after="更新后的内容"
    )

    assert change1 is not None
    assert change2 is not None

    print(f"\n已记录 {len(collab.change_history.get(memory_id, []))} 个变更")

    # 获取变更历史
    history = collab.get_change_history(memory_id)
    assert len(history) == 2

    for change in history:
        print(f"  {change.change_type} by {change.user_id}")

    print("\n✓ 变更追踪功能测试通过！")

    # 清理
    try:
        os.remove(test_path)
    except:
        pass

    return True


def test_conflict_detection():
    """测试冲突检测功能"""
    print("\n" + "=" * 60)
    print("测试 3: 冲突检测功能")
    print("=" * 60)

    test_path = "./data/test_collab_conflict.json"
    if os.path.exists(test_path):
        os.remove(test_path)

    collab = MemoryCollaboration(test_path)

    memory_id = "mem_001"

    # 设置权限
    collab.permission_manager.set_permission(memory_id, "user_1", PermissionLevel.EDITOR)
    collab.permission_manager.set_permission(memory_id, "user_2", PermissionLevel.EDITOR)

    # 用户1的变更
    change1 = collab.make_change(
        memory_id=memory_id,
        user_id="user_1",
        change_type=ChangeType.UPDATE,
        content_before="初始内容",
        content_after="用户1的修改"
    )

    # 用户2的变更
    change2 = collab.make_change(
        memory_id=memory_id,
        user_id="user_2",
        change_type=ChangeType.UPDATE,
        content_before="初始内容",
        content_after="用户2的修改"
    )

    # 检查是否有冲突信息
    print(f"\n冲突检测:")
    has_conflict = "conflict_info" in change2.metadata
    print(f"  是否有冲突: {has_conflict}")

    # 测试独立的冲突检测器
    detector = ConflictDetector()
    conflict = detector.detect_conflict(change1, change2)
    print(f"  检测冲突结果: {conflict}")

    if conflict:
        suggestion = detector.suggest_resolution(change1, change2)
        print(f"  解决建议: {suggestion}")

    print("\n✓ 冲突检测功能测试通过！")

    # 清理
    try:
        os.remove(test_path)
    except:
        pass

    return True


def test_enhanced_collaboration():
    """测试增强记忆系统的协作功能"""
    print("\n" + "=" * 60)
    print("测试 4: 增强记忆系统的协作功能")
    print("=" * 60)

    test_path = "./data/collaboration.json"
    if os.path.exists(test_path):
        os.remove(test_path)

    memory = get_memory_system()
    enhanced = EnhancedMemoryWithCollaboration(memory)

    # 清空现有数据
    memory.l1.clear()
    memory.l2.clear()
    memory.l3.clear()

    # 添加带权限的记忆
    owner_id = "alice"
    mem_id = enhanced.add_with_permission(
        "协作项目计划",
        "proj_collab",
        "l2",
        owner_id=owner_id
    )
    print(f"\n添加记忆: {mem_id} (所有者: {owner_id})")

    # 分享给其他用户
    share_success = enhanced.share_memory(
        memory_id=mem_id,
        from_user=owner_id,
        to_user="bob",
        level=PermissionLevel.EDITOR
    )
    print(f"\n分享给 bob: {share_success}")
    assert share_success == True

    # 分享给查看者
    share_success = enhanced.share_memory(
        memory_id=mem_id,
        from_user=owner_id,
        to_user="charlie",
        level=PermissionLevel.VIEWER
    )
    assert share_success == True

    # 用户 bob 编辑
    edit_change = enhanced.collaborate_edit(
        memory_id=mem_id,
        user_id="bob",
        new_content="更新后的协作项目计划",
        comment="添加了新的需求"
    )

    assert edit_change is not None
    print(f"\nbob 编辑成功")

    # 获取变更历史
    history = enhanced.get_change_history(mem_id)
    print(f"\n变更历史:")
    for change in history:
        print(f"  {change['user_id']}: {change['change_type']}")

    # 获取统计
    stats = enhanced.get_collaboration_statistics()
    print(f"\n协作统计:")
    print(f"  总变更数: {stats['total_changes']}")
    print(f"  有变更的记忆数: {stats['memories_with_changes']}")

    print("\n✓ 增强记忆系统的协作功能测试通过！")

    # 清理
    if os.path.exists(test_path):
        os.remove(test_path)

    return True


def test_active_editors():
    """测试活跃编辑者功能"""
    print("\n" + "=" * 60)
    print("测试 5: 活跃编辑者功能")
    print("=" * 60)

    test_path = "./data/test_collab_active.json"
    if os.path.exists(test_path):
        os.remove(test_path)

    collab = MemoryCollaboration(test_path)

    memory_id = "mem_001"

    # 设置权限
    collab.permission_manager.set_permission(memory_id, "user_1", PermissionLevel.EDITOR)
    collab.permission_manager.set_permission(memory_id, "user_2", PermissionLevel.EDITOR)

    # 开始编辑
    collab.start_editing(memory_id, "user_1")
    collab.start_editing(memory_id, "user_2")

    # 获取活跃编辑者
    active = collab.get_active_editors(memory_id)
    print(f"\n活跃编辑者: {active}")
    assert len(active) == 2

    # 结束编辑
    collab.end_editing(memory_id, "user_1")

    active = collab.get_active_editors(memory_id)
    assert len(active) == 1

    print("\n✓ 活跃编辑者功能测试通过！")

    # 清理
    try:
        os.remove(test_path)
    except:
        pass

    return True


def test_statistics():
    """测试统计功能"""
    print("\n" + "=" * 60)
    print("测试 6: 统计功能")
    print("=" * 60)

    test_path = "./data/test_collab_stats.json"
    if os.path.exists(test_path):
        os.remove(test_path)

    collab = MemoryCollaboration(test_path)

    # 模拟多个用户编辑
    memory_id = "mem_001"

    collab.permission_manager.set_permission(memory_id, "user_a", PermissionLevel.OWNER)
    collab.permission_manager.set_permission(memory_id, "user_b", PermissionLevel.EDITOR)

    # user_a 的变更
    collab.make_change(memory_id, "user_a", ChangeType.CREATE, content_after="内容A")
    collab.make_change(memory_id, "user_a", ChangeType.UPDATE, content_before="内容A", content_after="内容B")

    # user_b 的变更
    collab.make_change(memory_id, "user_b", ChangeType.UPDATE, content_before="内容B", content_after="内容C")

    # 获取统计
    stats = collab.get_statistics()

    print(f"\n协作统计:")
    print(f"  总变更数: {stats['total_changes']}")
    print(f"  有变更的记忆数: {stats['memories_with_changes']}")
    print(f"  最活跃用户: {stats['most_active_users']}")

    assert stats['total_changes'] == 3

    print("\n✓ 统计功能测试通过！")

    # 清理
    try:
        os.remove(test_path)
    except:
        pass

    return True


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("第22阶段测试：记忆协作编辑功能")
    print("=" * 60)

    all_passed = True

    try:
        passed = test_permission_management()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试1失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_change_tracking()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试2失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_conflict_detection()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试3失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_enhanced_collaboration()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试4失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_active_editors()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试5失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_statistics()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试6失败: {e}")
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
