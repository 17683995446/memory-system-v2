"""
第33阶段测试：数据持久化与备份系统
遵循"图难于其易，为大于其细"原则
"""

import os
import sys
import json
import tempfile
import shutil
import time
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.backup.advanced import (
    AdvancedBackupManager,
    BackupConfig,
    BackupType,
    BackupScheduler,
    DataVerifier,
    VerificationStatus,
    create_backup_system
)
from src.memory import get_memory_system


def test_data_verifier():
    """测试数据验证器"""
    print("\n=== 测试数据验证器 ===")
    
    # 测试校验和计算
    data = "测试数据"
    checksum = DataVerifier.compute_checksum(data)
    print(f"✓ 校验和计算: {checksum[:16]}...")
    
    # 测试校验和验证
    is_valid = DataVerifier.verify_checksum(data, checksum)
    assert is_valid, "校验和验证失败"
    print(f"✓ 校验和验证通过")
    
    # 测试错误校验和
    is_invalid = DataVerifier.verify_checksum(data, "wrong_checksum")
    assert not is_invalid, "错误校验和应该验证失败"
    print(f"✓ 错误校验和正确拒绝")
    
    print("✓ 数据验证器测试通过")


def test_backup_manager():
    """测试备份管理器"""
    print("\n=== 测试备份管理器 ===")
    
    # 创建临时备份目录
    temp_dir = tempfile.mkdtemp()
    try:
        # 创建备份配置
        config = BackupConfig(
            backup_dir=temp_dir,
            max_backups=5,
            compress_backups=False,
            enable_verification=True
        )
        
        # 创建备份管理器
        manager = AdvancedBackupManager(config)
        print(f"✓ 备份管理器创建成功")
        
        # 创建记忆系统并添加数据
        memory_system = get_memory_system()
        
        # 添加测试数据
        memory_system.add("这是L1记忆内容", "test_session_1")
        memory_system.add("这是L2情景记忆内容", "test_session_1")
        memory_system.add_fact("地球", "形状", "圆形", "科学")
        
        # 创建备份
        result = manager.create_backup(
            memory_system,
            BackupType.FULL,
            "测试完整备份"
        )
        assert result["success"], "备份创建失败"
        print(f"✓ 完整备份创建成功: {result['backup_id']}")
        
        # 列出备份
        backups = manager.list_backups()
        assert len(backups) >= 1, "备份列表应该至少有一个备份"
        print(f"✓ 备份列表查询成功，共 {len(backups)} 个备份")
        
        # 验证备份
        verify_result = manager.verify_backup(result["backup_id"])
        assert verify_result["success"], "备份验证失败"
        print(f"✓ 备份验证通过: {verify_result['status']}")
        
        # 恢复备份
        restore_result = manager.restore_backup(
            memory_system,
            result["backup_id"]
        )
        assert restore_result["success"], "备份恢复失败"
        print(f"✓ 备份恢复成功，恢复了 {restore_result['stats']['total_restored']} 条记忆")
        
        # 测试备份统计
        stats = manager.get_backup_stats()
        print(f"✓ 备份统计: {stats}")
        
        print("✓ 备份管理器测试通过")
        
    finally:
        # 清理
        shutil.rmtree(temp_dir)


def test_incremental_backup():
    """测试增量备份"""
    print("\n=== 测试增量备份 ===")
    
    temp_dir = tempfile.mkdtemp()
    try:
        config = BackupConfig(
            backup_dir=temp_dir,
            max_backups=10,
            compress_backups=False
        )
        
        manager = AdvancedBackupManager(config)
        memory_system = get_memory_system()
        
        # 创建初始备份
        memory_system.add("初始数据1", "session1")
        result1 = manager.create_backup(memory_system, BackupType.FULL, "初始完整备份")
        assert result1["success"]
        print(f"✓ 初始完整备份: {result1['backup_id']}")
        
        # 添加新数据
        memory_system.add("新增数据1", "session1")
        memory_system.add("新增数据2", "session1")
        
        # 创建增量备份
        result2 = manager.create_backup(memory_system, BackupType.INCREMENTAL, "增量备份1")
        assert result2["success"]
        print(f"✓ 增量备份: {result2['backup_id']}")
        
        # 验证两个备份都存在
        backups = manager.list_backups()
        assert len(backups) >= 2
        print(f"✓ 两个备份都存在")
        
        print("✓ 增量备份测试通过")
        
    finally:
        shutil.rmtree(temp_dir)


def test_backup_cleanup():
    """测试备份清理"""
    print("\n=== 测试备份清理 ===")
    
    temp_dir = tempfile.mkdtemp()
    try:
        config = BackupConfig(
            backup_dir=temp_dir,
            max_backups=3  # 只保留3个备份
        )
        
        manager = AdvancedBackupManager(config)
        memory_system = get_memory_system()
        
        # 创建5个备份
        backup_ids = []
        for i in range(5):
            memory_system.add(f"测试数据{i}", f"session{i}")
            result = manager.create_backup(memory_system, BackupType.FULL, f"备份{i}")
            backup_ids.append(result["backup_id"])
            time.sleep(0.1)  # 确保时间戳不同
        
        # 检查只有3个备份保留
        backups = manager.list_backups()
        assert len(backups) == 3, f"应该只保留3个备份，实际有{len(backups)}个"
        print(f"✓ 备份清理正常，保留了3个最新备份")
        
        print("✓ 备份清理测试通过")
        
    finally:
        shutil.rmtree(temp_dir)


def test_backup_scheduler():
    """测试备份调度器"""
    print("\n=== 测试备份调度器 ===")
    
    temp_dir = tempfile.mkdtemp()
    try:
        config = BackupConfig(
            backup_dir=temp_dir,
            auto_backup_enabled=True,
            auto_backup_interval_hours=1,  # 1小时间隔（测试时用）
            max_backups=10
        )
        
        manager = AdvancedBackupManager(config)
        memory_system = get_memory_system()
        
        # 创建备份系统
        backup_system = create_backup_system(memory_system, config)
        scheduler = backup_system["scheduler"]
        
        # 获取调度器状态
        status = scheduler.get_scheduler_status()
        assert not status["running"], "调度器初始应该停止"
        print(f"✓ 调度器初始状态: {status}")
        
        # 启动调度器
        scheduler.start()
        time.sleep(0.5)
        
        status = scheduler.get_scheduler_status()
        assert status["running"], "调度器应该已启动"
        print(f"✓ 调度器启动成功")
        
        # 停止调度器
        scheduler.stop()
        time.sleep(0.5)
        
        status = scheduler.get_scheduler_status()
        assert not status["running"], "调度器应该已停止"
        print(f"✓ 调度器停止成功")
        
        print("✓ 备份调度器测试通过")
        
    finally:
        shutil.rmtree(temp_dir)


def test_backup_system_integration():
    """测试备份系统完整集成"""
    print("\n=== 测试备份系统完整集成 ===")
    
    temp_dir = tempfile.mkdtemp()
    try:
        config = BackupConfig(
            backup_dir=temp_dir,
            auto_backup_enabled=False,
            max_backups=5,
            compress_backups=True
        )
        
        # 创建完整备份系统
        memory_system = get_memory_system()
        backup_system = create_backup_system(memory_system, config)
        
        manager = backup_system["manager"]
        scheduler = backup_system["scheduler"]
        
        # 添加测试数据
        for i in range(10):
            memory_system.add(f"测试记忆内容 {i}", f"session_{i % 3}")
            if i % 2 == 0:
                memory_system.add_fact(f"实体{i}", f"属性{i}", f"值{i}", "测试")
        
        print(f"✓ 添加了10条记忆和5个事实")
        
        # 创建完整备份
        backup_result = manager.create_backup(
            memory_system,
            BackupType.FULL,
            "完整集成测试备份"
        )
        assert backup_result["success"]
        print(f"✓ 完整备份创建成功: {backup_result['backup_id']}")
        print(f"  统计: {backup_result['stats']}")
        
        # 验证备份
        verify_result = manager.verify_backup(backup_result["backup_id"])
        assert verify_result["status"] == VerificationStatus.PASS.value
        print(f"✓ 备份验证通过: {verify_result['message']}")
        
        # 清空记忆系统
        memory_system.l1.clear()
        memory_system.l2.clear()
        memory_system.l3.clear()
        
        stats = memory_system.get_statistics()
        assert stats["l1"]["size"] == 0
        assert stats["l2"]["size"] == 0
        assert stats["l3"]["size"] == 0
        print(f"✓ 记忆系统已清空")
        
        # 恢复备份
        restore_result = manager.restore_backup(
            memory_system,
            backup_result["backup_id"]
        )
        assert restore_result["success"]
        print(f"✓ 备份恢复成功")
        print(f"  恢复统计: {restore_result['stats']}")
        
        # 验证数据恢复
        stats = memory_system.get_statistics()
        assert stats["l1"]["size"] > 0 or stats["l2"]["size"] > 0 or stats["l3"]["size"] > 0
        print(f"✓ 数据恢复验证通过: {stats}")
        
        print("✓ 备份系统集成测试通过")
        
    finally:
        shutil.rmtree(temp_dir)


def main():
    """运行所有测试"""
    print("=" * 60)
    print("第33阶段测试：数据持久化与备份系统")
    print("遵循原则：图难于其易，为大于其细")
    print("=" * 60)
    
    try:
        test_data_verifier()
        test_backup_manager()
        test_incremental_backup()
        test_backup_cleanup()
        test_backup_scheduler()
        test_backup_system_integration()
        
        print("\n" + "=" * 60)
        print("✓ 所有第33阶段测试通过！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
