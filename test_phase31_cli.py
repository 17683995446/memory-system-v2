"""
第31阶段测试: CLI命令行工具
测试CLI的基本功能
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.cli import MemoryCLI
import argparse


def test_cli_basic():
    """测试CLI基本功能"""
    print("\n" + "=" * 70)
    print("第31阶段测试: 记忆系统CLI命令行工具")
    print("=" * 70)

    # 创建CLI实例
    cli = MemoryCLI()
    all_passed = True

    # 测试1: 配置管理
    print("\n[测试1] 配置管理")
    try:
        print(f"✓ CLI初始化成功")
        print(f"  默认层级: {cli.config.get('default_level')}")
        print(f"  输出格式: {cli.config.get('output_format')}")
        print(f"  最大结果数: {cli.config.get('max_results')}")
    except Exception as e:
        print(f"✗ CLI初始化失败: {e}")
        all_passed = False

    # 测试2: 添加记忆
    print("\n[测试2] 添加记忆")
    try:
        args = argparse.Namespace(
            content="这是CLI测试记忆",
            level="l2",
            source="cli_test"
        )
        result = cli.cmd_add(args)
        assert result == 0
        assert len(cli.current_memories) > 0
        print(f"✓ 成功添加记忆，共 {len(cli.current_memories)} 条")
    except Exception as e:
        print(f"✗ 添加记忆失败: {e}")
        all_passed = False

    # 测试3: 列出记忆
    print("\n[测试3] 列出记忆")
    try:
        args = argparse.Namespace(level=None, limit=None)
        result = cli.cmd_list(args)
        assert result == 0
        print("✓ 列出记忆成功")
    except Exception as e:
        print(f"✗ 列出记忆失败: {e}")
        all_passed = False

    # 测试4: 搜索记忆
    print("\n[测试4] 搜索记忆")
    try:
        args = argparse.Namespace(query="CLI测试")
        result = cli.cmd_search(args)
        assert result == 0
        print("✓ 搜索记忆成功")
    except Exception as e:
        print(f"✗ 搜索记忆失败: {e}")
        all_passed = False

    # 测试5: 提问问题
    print("\n[测试5] 提问问题")
    try:
        args = argparse.Namespace(question="CLI测试记忆是什么？", show_sources=False)
        result = cli.cmd_ask(args)
        assert result == 0
        print(f"✓ 提问成功，对话ID: {cli.conversation_id}")
    except Exception as e:
        print(f"✗ 提问失败: {e}")
        all_passed = False

    # 测试6: 统计信息
    print("\n[测试6] 统计信息")
    try:
        args = argparse.Namespace()
        result = cli.cmd_stats(args)
        assert result == 0
        print("✓ 统计信息显示成功")
    except Exception as e:
        print(f"✗ 统计信息失败: {e}")
        all_passed = False

    # 测试7: 导出记忆
    print("\n[测试7] 导出记忆")
    try:
        args = argparse.Namespace(format="json", output=None, no_metadata=False)
        result = cli.cmd_export(args)
        assert result == 0
        print("✓ JSON导出成功")
    except Exception as e:
        print(f"✗ 导出失败: {e}")
        all_passed = False

    # 测试8: Markdown导出
    print("\n[测试8] Markdown导出")
    try:
        args = argparse.Namespace(format="markdown", output=None, no_metadata=False)
        result = cli.cmd_export(args)
        assert result == 0
        print("✓ Markdown导出成功")
    except Exception as e:
        print(f"✗ Markdown导出失败: {e}")
        all_passed = False

    # 测试9: 分享创建
    print("\n[测试9] 创建分享")
    try:
        args = argparse.Namespace(
            memory_ids="",
            type="read",
            expires=24
        )
        result = cli.cmd_share(args)
        assert result == 0
        print("✓ 创建分享成功")
    except Exception as e:
        print(f"✗ 创建分享失败: {e}")
        all_passed = False

    # 测试10: 删除记忆
    print("\n[测试10] 删除记忆")
    try:
        if cli.current_memories:
            mem_id = cli.current_memories[0]['id']
            args = argparse.Namespace(id=mem_id)
            result = cli.cmd_delete(args)
            assert result == 0
            print(f"✓ 删除记忆成功: {mem_id}")
    except Exception as e:
        print(f"✗ 删除记忆失败: {e}")
        all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print("✓ 所有CLI功能测试通过!")
    else:
        print("✗ 部分测试失败")
    print("=" * 70)

    return all_passed


if __name__ == "__main__":
    success = test_cli_basic()
    sys.exit(0 if success else 1)
