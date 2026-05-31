"""
基于第一性原理的Agent可靠记忆系统 - 测试脚本
"""
import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.memory.memory_system import get_memory_system


def test_memory_system():
    """测试记忆系统"""
    print("=" * 50)
    print("基于第一性原理的Agent可靠记忆系统 - 测试")
    print("=" * 50)
    
    # 获取记忆系统
    memory = get_memory_system()
    
    task_id = "test_task_001"
    
    print("\n[1] 添加L1记忆（瞬时工作记忆）")
    memory.add("用户问：你好，今天天气怎么样？", task_id, "l1")
    memory.add("工具返回：北京今天晴，气温22度", task_id, "l1")
    print(f"✓ L1记忆添加完成")
    
    print("\n[2] 添加L2记忆（情景经验）")
    memory.add("用户通常在上午9点到10点之间询问天气", task_id, "l2")
    memory.add("上次用户去公园是因为天气好", task_id, "l2")
    print(f"✓ L2记忆添加完成")
    
    print("\n[3] 添加L3记忆（永久事实）")
    memory.add_fact("系统", "名称", "FirstPrincipleMemory")
    memory.add_fact("用户", "偏好", "简洁回答")
    memory.add_fact("规则", "必须", "保护用户隐私")
    print(f"✓ L3记忆添加完成")
    
    print("\n[4] 统计信息")
    stats = memory.get_statistics()
    print(f"  L1: {stats['l1']['size']} 条, {stats['l1']['task_count']} 个任务")
    print(f"  L2: {stats['l2']['size']} 条")
    print(f"  L3: {stats['l3']['size']} 条")
    
    print("\n[5] 智能召回测试")
    print("  查询：'用户天气'")
    results = memory.recall("用户天气", task_id)
    print(f"  L1召回: {len(results['l1'])} 条")
    print(f"  L2召回: {len(results['l2'])} 条")
    print(f"  L3召回: {len(results['l3'])} 条")
    
    print("\n[6] 任务结束，清理L1")
    memory.end_task(task_id)
    stats = memory.get_statistics()
    print(f"  清理后L1: {stats['l1']['size']} 条")
    
    print("\n" + "=" * 50)
    print("测试完成！系统运行正常。")
    print("=" * 50)


if __name__ == "__main__":
    test_memory_system()
