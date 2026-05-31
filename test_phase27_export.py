"""
第27阶段测试：记忆导出与分享功能
"""

import sys
import os
import time
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.memory import get_memory_system
from src.export import (
    MemoryExporter,
    MemorySharer,
    EnhancedMemoryWithExport
)


def test_memory_exporter():
    """测试记忆导出功能"""
    print("\n" + "=" * 60)
    print("测试 1: 记忆导出")
    print("=" * 60)

    # 创建测试记忆
    test_memories = [
        {
            "memory_id": "mem_001",
            "content": "重要的项目文档内容。这是第一条测试记忆。",
            "memory_level": "L2",
            "created_at": time.time() - 3600
        },
        {
            "memory_id": "mem_002",
            "content": "学习笔记：关于人工智能的基础知识。",
            "memory_level": "L2",
            "created_at": time.time() - 7200
        },
        {
            "memory_id": "mem_003",
            "content": "会议记录：项目组讨论了下一阶段的工作计划。",
            "memory_level": "L3",
            "created_at": time.time()
        }
    ]

    # 测试 JSON 导出
    print("\nJSON 导出:")
    json_export = MemoryExporter.export_to_json(test_memories)
    print(f"  长度: {len(json_export)}")
    assert json_export
    assert "mem_001" in json_export
    print("  ✓ JSON 导出成功")

    # 测试文本导出
    print("\n文本导出:")
    text_export = MemoryExporter.export_to_text(test_memories)
    print(f"  长度: {len(text_export)}")
    assert text_export
    assert "重要的项目文档内容" in text_export
    print("  ✓ 文本导出成功")

    # 测试 Markdown 导出
    print("\nMarkdown 导出:")
    md_export = MemoryExporter.export_to_markdown(test_memories)
    print(f"  长度: {len(md_export)}")
    assert md_export
    assert "# 记忆导出" in md_export
    assert "记忆 1" in md_export
    print("  ✓ Markdown 导出成功")

    # 测试 CSV 导出
    print("\nCSV 导出:")
    csv_export = MemoryExporter.export_to_csv(test_memories)
    print(f"  长度: {len(csv_export)}")
    assert csv_export
    print("  ✓ CSV 导出成功")

    # 测试文件导出
    test_dir = "./data/test_exports"
    os.makedirs(test_dir, exist_ok=True)

    json_file = os.path.join(test_dir, "test_export.json")
    MemoryExporter.export_to_json(test_memories, json_file)
    assert os.path.exists(json_file)
    print(f"  ✓ JSON 文件导出成功: {json_file}")

    text_file = os.path.join(test_dir, "test_export.txt")
    MemoryExporter.export_to_text(test_memories, text_file)
    assert os.path.exists(text_file)
    print(f"  ✓ 文本文件导出成功: {text_file}")

    print("\n✓ 记忆导出测试通过！")
    return True


def test_memory_sharer():
    """测试记忆分享功能"""
    print("\n" + "=" * 60)
    print("测试 2: 记忆分享")
    print("=" * 60)

    # 创建分享器
    test_share_dir = "./data/test_shares"
    sharer = MemorySharer(test_share_dir)

    # 创建测试记忆
    share_memories = [
        {
            "memory_id": "share_001",
            "content": "分享的记忆内容 1",
            "memory_level": "L2",
            "created_at": time.time()
        },
        {
            "memory_id": "share_002",
            "content": "分享的记忆内容 2",
            "memory_level": "L2",
            "created_at": time.time()
        }
    ]

    # 创建分享
    share_id = sharer.create_share(
        memory_ids=["share_001", "share_002"],
        memories=share_memories,
        share_type="read",
        expires_at=time.time() + 3600  # 1小时后过期
    )
    print(f"\n创建分享 ID: {share_id}")
    assert share_id
    print("  ✓ 分享创建成功")

    # 获取分享
    share_data = sharer.get_share(share_id)
    assert share_data
    assert share_data["share_id"] == share_id
    assert len(share_data["memories"]) == 2
    print("  ✓ 获取分享成功")

    # 再次获取（访问计数增加）
    share_data2 = sharer.get_share(share_id)
    assert share_data2["access_count"] == 2
    print("  ✓ 访问计数更新成功")

    # 列出分享
    shares = sharer.list_shares()
    assert len(shares) >= 1
    print(f"  ✓ 列出分享成功: {len(shares)} 个分享")

    # 删除分享
    success = sharer.delete_share(share_id)
    assert success
    print("  ✓ 删除分享成功")

    # 验证删除
    share_data_deleted = sharer.get_share(share_id)
    assert share_data_deleted is None
    print("  ✓ 分享删除后无法获取")

    print("\n✓ 记忆分享测试通过！")
    return True


def test_enhanced_memory():
    """测试增强记忆系统"""
    print("\n" + "=" * 60)
    print("测试 3: 增强记忆系统")
    print("=" * 60)

    memory = get_memory_system()
    enhanced = EnhancedMemoryWithExport(memory)

    # 清空现有数据
    memory.l1.clear()
    memory.l2.clear()
    memory.l3.clear()

    # 添加一些记忆
    sample_contents = [
        "项目总结：今天完成了重要项目的核心功能。",
        "学习笔记：今天学习了Python的高级特性。",
        "会议记录：项目组会议讨论了下一阶段的工作计划。",
        "技术文档：API接口设计规范。"
    ]
    mem_ids = []
    for i, content in enumerate(sample_contents):
        mem_id = memory.add(content, "test", "l2")
        mem_ids.append(mem_id)

    print(f"\n添加了 {len(mem_ids)} 条记忆")

    # 测试导出
    print("\n导出测试:")

    # JSON 导出
    json_result = enhanced.export_memories("json")
    assert json_result
    print(f"  ✓ JSON 导出: {len(json_result)} 字符")

    # 文本导出
    text_result = enhanced.export_memories("text")
    assert text_result
    print(f"  ✓ 文本导出: {len(text_result)} 字符")

    # Markdown 导出
    md_result = enhanced.export_memories("markdown")
    assert md_result
    print(f"  ✓ Markdown 导出: {len(md_result)} 字符")

    # 测试文件导出
    export_file = "./data/test_export_file.json"
    file_result = enhanced.export_memories("json", export_file)
    assert os.path.exists(export_file)
    print(f"  ✓ 文件导出: {file_result}")

    # 测试分享
    print("\n分享测试:")

    # 创建分享
    share_id = enhanced.create_share(
        memory_ids=[],  # 分享所有记忆
        share_type="read",
        expires_hours=24  # 24小时过期
    )
    assert share_id
    print(f"  ✓ 创建分享: {share_id}")

    # 获取分享
    share_data = enhanced.get_share(share_id)
    assert share_data
    assert len(share_data["memories"]) >= len(sample_contents) - 1
    print(f"  ✓ 获取分享成功: {len(share_data['memories'])} 条记忆")

    # 列出分享
    shares_list = enhanced.list_shares()
    assert len(shares_list) >= 1
    print(f"  ✓ 列出分享: {len(shares_list)} 个分享")

    print("\n✓ 增强记忆系统测试通过！")
    return True


def test_integration():
    """测试集成功能"""
    print("\n" + "=" * 60)
    print("测试 4: 集成测试")
    print("=" * 60)

    memory = get_memory_system()
    enhanced = EnhancedMemoryWithExport(memory)

    # 清空现有数据
    memory.l1.clear()
    memory.l2.clear()
    memory.l3.clear()

    # 添加更多测试数据
    more_contents = [
        "测试记忆 A",
        "测试记忆 B",
        "测试记忆 C",
        "测试记忆 D"
    ]
    for content in more_contents:
        memory.add(content, "integration", "l2")

    print(f"\n添加了 {len(more_contents)} 条测试记忆")

    # 测试完整流程
    print("\n完整流程测试:")

    # 1. 导出为多种格式
    for fmt in ["json", "text", "markdown", "csv"]:
        result = enhanced.export_memories(fmt)
        assert result
        print(f"  ✓ {fmt.upper()} 格式导出成功")

    # 2. 创建多个分享
    share_ids = []
    for i in range(2):
        sid = enhanced.create_share(
            memory_ids=[],
            share_type="read",
            expires_hours=1
        )
        share_ids.append(sid)
        print(f"  ✓ 创建分享 {i+1}: {sid}")

    # 3. 列出所有分享
    shares = enhanced.list_shares()
    print(f"  ✓ 当前分享数: {len(shares)}")

    # 4. 访问分享
    for sid in share_ids:
        data = enhanced.get_share(sid)
        assert data
        print(f"  ✓ 访问分享: {sid}")

    # 5. 清理
    for sid in share_ids:
        enhanced.delete_share(sid)
        print(f"  ✓ 删除分享: {sid}")

    print("\n✓ 集成测试通过！")
    return True


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("第27阶段测试：记忆导出与分享功能")
    print("=" * 60)

    all_passed = True

    try:
        passed = test_memory_exporter()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试1失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_memory_sharer()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试2失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_enhanced_memory()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试3失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_integration()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试4失败: {e}")
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
