"""
第13阶段测试：记忆导出/导入与备份系统
"""

import sys
import os
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.memory import get_memory_system
from src.backup import MemoryExporter, MemoryImporter, BackupManager


def test_export_import():
    """测试记忆导出和导入"""
    print("\n" + "=" * 60)
    print("测试1: 记忆导出与导入")
    print("=" * 60)
    
    # 创建记忆系统并添加测试数据
    memory = get_memory_system()
    
    # 清空先
    memory.l1.clear()
    memory.l2.clear()
    memory.l3.clear()
    
    # 添加测试记忆
    print("添加测试数据...")
    
    # L1
    memory.l1.add("用户输入1：你好", "session_test1")
    memory.l1.add("用户输入2：今天天气", "session_test1")
    memory.l1.add("临时上下文：正在处理", "session_test2")
    
    # L2
    for i in range(5):
        memory.add(f"情景记忆{i}: 关于项目的重要讨论", "session_test1", "l2")
    
    # L3
    memory.add_fact("用户", "姓名", "张三")
    memory.add_fact("系统", "版本", "1.0.0")
    memory.add_fact("配置", "语言", "中文")
    
    print(f"当前统计: L1={memory.l1.size()}, L2={memory.l2.size()}, L3={memory.l3.size()}")
    
    # 导出
    print("\n导出记忆...")
    exporter = MemoryExporter()
    export_path = "./test_export.json"
    result = exporter.export_memory(
        memory,
        export_path,
        include_l1=True,
        include_l2=True,
        include_l3=True
    )
    
    print(f"导出结果: {result}")
    assert result["success"], "导出失败"
    assert result["total_count"] > 0, "应该导出了一些数据"
    print("✓ 导出成功")
    
    # 清空记忆系统
    print("\n清空记忆系统...")
    memory.l1.clear()
    memory.l2.clear()
    memory.l3.clear()
    print(f"清空后统计: L1={memory.l1.size()}, L2={memory.l2.size()}, L3={memory.l3.size()}")
    
    # 导入
    print("\n导入记忆...")
    importer = MemoryImporter()
    import_result = importer.import_memory(
        memory,
        export_path,
        clear_before_import=False
    )
    print(f"导入结果: {import_result}")
    
    assert import_result["success"], "导入失败"
    assert import_result["total_imported"] > 0, "应该导入了一些数据"
    
    # 验证
    print(f"\n导入后统计: L1={memory.l1.size()}, L2={memory.l2.size()}, L3={memory.l3.size()}")
    print("✓ 导入成功")
    
    return True


def test_backup_manager():
    """测试备份管理器"""
    print("\n" + "=" * 60)
    print("测试2: 备份管理器")
    print("=" * 60)
    
    # 创建记忆系统
    memory = get_memory_system()
    
    # 清空并添加一些测试数据
    memory.l1.clear()
    memory.l2.clear()
    memory.l3.clear()
    
    memory.add("备份测试：这是一个重要记忆", "backup_test", "l2")
    memory.add("另一个记忆：记得更新文档", "backup_test", "l2")
    memory.add_fact("backup", "test", "true")
    
    # 备份管理器
    backup_dir = "./data/test_backups"
    if os.path.exists(backup_dir):
        shutil.rmtree(backup_dir)
    
    manager = BackupManager(backup_dir)
    
    # 创建备份
    print("\n创建备份...")
    backup_result = manager.create_backup(memory, "test_backup_001")
    print(f"备份结果: {backup_result}")
    assert backup_result["success"], "创建备份失败"
    print("✓ 备份创建成功")
    
    # 列出备份
    print("\n列出备份...")
    backups = manager.list_backups()
    print(f"找到 {len(backups)} 个备份")
    assert len(backups) >= 1, "应该至少有一个备份"
    for b in backups:
        print(f"  - {b['name']} ({b['size']} bytes)")
    print("✓ 备份列表正常")
    
    # 清空记忆
    memory.l1.clear()
    memory.l2.clear()
    memory.l3.clear()
    print(f"\n清空后统计: L1={memory.l1.size()}, L2={memory.l2.size()}, L3={memory.l3.size()}")
    
    # 恢复备份
    print("\n恢复备份...")
    restore_result = manager.restore_backup(memory, "test_backup_001")
    print(f"恢复结果: {restore_result}")
    assert restore_result["success"], "恢复备份失败"
    
    # 验证
    print(f"\n恢复后统计: L1={memory.l1.size()}, L2={memory.l2.size()}, L3={memory.l3.size()}")
    assert memory.l2.size() > 0, "L2 应该有记忆"
    assert memory.l3.size() > 0, "L3 应该有事实"
    print("✓ 备份恢复成功")
    
    return True


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("第13阶段测试：记忆导出/导入与备份系统")
    print("=" * 60)
    
    all_passed = True
    
    try:
        passed = test_export_import()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"✗ 测试1失败: {e}")
        all_passed = False
    
    try:
        passed = test_backup_manager()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"✗ 测试2失败: {e}")
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
