"""
第38阶段测试：记忆系统协作与共享功能
遵循"图难于其易，为大于其细"原则
"""
import os
import sys
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.collaboration import (
    PermissionLevel,
    ShareType,
    ChangeType,
    MemoryCollaboration,
    EnhancedMemoryWithCollaboration,
    get_collaboration_system
)


def test_permission_system():
    """测试权限系统"""
    print("\n=== 测试权限系统")

    collab = MemoryCollaboration(storage_path="./data/test_collab_perms.json")

    # 创建记忆和设置权限
    memory_id = "test_memory_001"
    owner_id = "user_owner"
    editor_id = "user_editor"
    viewer_id = "user_viewer"

    collab.permission_manager.set_permission(memory_id, owner_id, PermissionLevel.OWNER)
    collab.permission_manager.set_permission(memory_id, editor_id, PermissionLevel.EDITOR)
    collab.permission_manager.set_permission(memory_id, viewer_id, PermissionLevel.VIEWER)

    # 检查权限
    assert collab.permission_manager.check_permission(memory_id, owner_id, PermissionLevel.OWNER)
    assert collab.permission_manager.check_permission(memory_id, owner_id, PermissionLevel.EDITOR)
    assert collab.permission_manager.check_permission(memory_id, editor_id, PermissionLevel.EDITOR)
    assert not collab.permission_manager.check_permission(memory_id, viewer_id, PermissionLevel.EDITOR)
    print("✓ 权限检查功能正常")

    # 获取有访问权限的用户列表
    users = collab.permission_manager.get_users_with_access(memory_id)
    assert len(users) == 3
    print("✓ 用户权限列表获取正常")

    # 移除权限
    collab.permission_manager.remove_permission(memory_id, viewer_id)
    users = collab.permission_manager.get_users_with_access(memory_id)
    assert len(users) == 2
    print("✓ 权限移除功能正常")

    print("✓ 权限系统测试通过")


def test_share_links():
    """测试分享链接"""
    print("\n=== 测试分享链接")

    collab = MemoryCollaboration(storage_path="./data/test_collab_links.json")

    memory_id = "test_memory_002"
    owner_id = "user_owner"

    # 设置所有者权限
    collab.permission_manager.set_permission(memory_id, owner_id, PermissionLevel.OWNER)

    # 创建分享链接
    link = collab.create_share_link(
        memory_id=memory_id,
        creator_id=owner_id,
        permission_level=PermissionLevel.VIEWER,
        expires_in_hours=24,
        max_uses=3
    )
    assert link is not None
    assert link.link_id is not None
    assert link.is_valid()
    print("✓ 分享链接创建成功")

    # 使用分享链接
    new_user_id = "user_new"
    success, message = collab.use_share_link(link.link_id, new_user_id)
    assert success
    assert collab.permission_manager.check_permission(memory_id, new_user_id, PermissionLevel.VIEWER)
    print(f"✓ 分享链接使用成功: {message}")

    # 获取分享链接列表
    links = collab.get_share_links(memory_id)
    assert len(links) == 1
    print("✓ 分享链接列表获取正常")

    # 撤销分享链接
    assert collab.revoke_share_link(link.link_id, owner_id)
    assert not collab.share_links[link.link_id].is_valid()
    print("✓ 分享链接撤销成功")

    print("✓ 分享链接测试通过")


def test_comments():
    """测试评论功能"""
    print("\n=== 测试评论功能")

    collab = MemoryCollaboration(storage_path="./data/test_collab_comments.json")

    memory_id = "test_memory_003"
    user_id = "user_commenter"

    collab.permission_manager.set_permission(memory_id, user_id, PermissionLevel.EDITOR)

    # 添加评论
    comment1 = collab.add_comment(memory_id, user_id, "这是第一条评论")
    assert comment1 is not None
    print("✓ 评论添加成功")

    # 添加回复
    user_id2 = "user_replier"
    collab.permission_manager.set_permission(memory_id, user_id2, PermissionLevel.VIEWER)
    comment2 = collab.add_comment(memory_id, user_id2, "这是一条回复", reply_to=comment1.comment_id)
    assert comment2 is not None
    print("✓ 回复添加成功")

    # 获取评论
    comments = collab.get_comments(memory_id)
    assert len(comments) == 2
    print("✓ 评论列表获取正常")

    # 标记评论为已解决
    resolver_id = "user_resolver"
    collab.permission_manager.set_permission(memory_id, resolver_id, PermissionLevel.EDITOR)
    assert collab.resolve_comment(comment1.comment_id, resolver_id)

    comments = collab.get_comments(memory_id, include_resolved=False)
    assert len(comments) == 1
    print("✓ 评论解决功能正常")

    print("✓ 评论功能测试通过")


def test_change_history():
    """测试变更历史"""
    print("\n=== 测试变更历史")

    collab = MemoryCollaboration(storage_path="./data/test_collab_history.json")

    memory_id = "test_memory_004"
    user_id = "user_editor"

    collab.permission_manager.set_permission(memory_id, user_id, PermissionLevel.OWNER)

    # 记录一些变更
    change1 = collab.make_change(
        memory_id=memory_id,
        user_id=user_id,
        change_type=ChangeType.CREATE,
        content_after="初始内容"
    )
    assert change1 is not None

    change2 = collab.make_change(
        memory_id=memory_id,
        user_id=user_id,
        change_type=ChangeType.UPDATE,
        content_before="初始内容",
        content_after="更新后的内容"
    )
    assert change2 is not None

    print("✓ 变更记录功能正常")

    # 获取变更历史
    history = collab.get_change_history(memory_id)
    assert len(history) == 2
    print("✓ 变更历史获取正常")

    # 按用户过滤
    history_by_user = collab.get_change_history(memory_id, user_id=user_id)
    assert len(history_by_user) == 2
    print("✓ 按用户过滤功能正常")

    # 按类型过滤
    updates = collab.get_change_history(memory_id, change_types=[ChangeType.UPDATE])
    assert len(updates) == 1
    print("✓ 按类型过滤功能正常")

    # 获取最新变更
    latest = collab.get_latest_change(memory_id)
    assert latest.change_id == change2.change_id
    print("✓ 最新变更获取正常")

    # 测试恢复
    revert_change = collab.revert_to_change(memory_id, change1.change_id, user_id)
    assert revert_change is not None
    assert revert_change.content_after == "初始内容"
    print("✓ 恢复功能正常")

    print("✓ 变更历史测试通过")


def test_collaboration_workflow():
    """测试完整的协作流程"""
    print("\n=== 测试完整协作流程")

    # 创建协作系统
    collab = MemoryCollaboration(storage_path="./data/test_collab_workflow.json")

    # 创建模拟记忆系统
    class MockMemorySystem:
        def __init__(self):
            self.memories = {}

        def add(self, text, task_id="default", level=None):
            mem_id = f"mem_{len(self.memories) + 1}"
            self.memories[mem_id] = text
            return mem_id

    memory_system = MockMemorySystem()

    # 创建增强记忆系统
    enhanced = EnhancedMemoryWithCollaboration(memory_system)

    # 用户1添加记忆
    owner_id = "user_1"
    memory_id = enhanced.add_with_permission(
        text="这是一个重要的项目文档",
        task_id="project_x",
        owner_id=owner_id
    )
    print(f"✓ 用户1添加了记忆: {memory_id}")

    # 用户1分享给用户2（编辑权限）
    user2_id = "user_2"
    success = enhanced.share_memory_direct(
        memory_id=memory_id,
        from_user=owner_id,
        to_user=user2_id,
        level=PermissionLevel.EDITOR
    )
    assert success
    print("✓ 用户1分享给用户2成功")

    # 用户2编辑记忆
    change = enhanced.collaborate_edit(
        memory_id=memory_id,
        user_id=user2_id,
        new_content="这是一个重要的项目文档（已更新）",
        comment="添加了重要细节"
    )
    assert change is not None
    print("✓ 用户2编辑记忆成功")

    # 用户2添加评论
    comment = enhanced.add_comment(
        memory_id=memory_id,
        user_id=user2_id,
        content="需要进一步完善这个部分"
    )
    assert comment is not None
    print("✓ 用户2添加评论成功")

    # 创建分享链接给用户3
    link = enhanced.create_share_link(
        memory_id=memory_id,
        creator_id=owner_id,
        permission_level=PermissionLevel.VIEWER,
        expires_in_hours=48,
        max_uses=1
    )
    assert link is not None
    print("✓ 分享链接创建成功")

    # 获取统计
    stats = enhanced.get_collaboration_statistics()
    assert stats["total_changes"] >= 3
    assert stats["total_comments"] >= 1
    print("✓ 统计信息获取正常")
    print(f"  总变更数: {stats['total_changes']}")
    print(f"  总评论数: {stats['total_comments']}")

    # 获取用户分享的记忆
    shared = enhanced.get_shared_memories(user2_id)
    assert len(shared) >= 1
    print("✓ 分享记忆列表获取正常")

    print("✓ 完整协作流程测试通过")


def test_global_instance():
    """测试全局单例"""
    print("\n=== 测试全局单例")

    collab1 = get_collaboration_system("./data/test_collab_global.json")
    collab2 = get_collaboration_system("./data/test_collab_global.json")

    assert collab1 is collab2
    print("✓ 全局单例获取正常")

    print("✓ 全局单例测试通过")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("第38阶段测试：记忆系统协作与共享功能")
    print("遵循原则：图难于其易，为大于其细")
    print("=" * 60)

    try:
        test_permission_system()
        test_share_links()
        test_comments()
        test_change_history()
        test_collaboration_workflow()
        test_global_instance()

        print("\n" + "=" * 60)
        print("✓ 所有第38阶段测试通过！")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # 清理测试文件
        test_files = [
            "./data/test_collab_perms.json",
            "./data/test_collab_links.json",
            "./data/test_collab_comments.json",
            "./data/test_collab_history.json",
            "./data/test_collab_workflow.json",
            "./data/test_collab_global.json"
        ]
        for f in test_files:
            if os.path.exists(f):
                os.remove(f)


if __name__ == "__main__":
    main()
