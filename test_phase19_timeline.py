"""
第19阶段测试：记忆时间线/历史记录功能
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.memory import get_memory_system
from src.timeline import (
    MemoryTimeline,
    MemoryEvent,
    MemoryEventType,
    EnhancedMemoryWithTimeline
)


def test_basic_timeline():
    """测试基本时间线功能"""
    print("\n" + "=" * 60)
    print("测试 1: 基本时间线功能")
    print("=" * 60)

    # 清理测试数据
    test_path = "./data/test_timeline_temp.json"
    if os.path.exists(test_path):
        os.remove(test_path)

    timeline = MemoryTimeline(test_path)

    # 记录事件
    mem_id = "mem_001"

    event1 = timeline.record_event(
        mem_id,
        MemoryEventType.CREATED,
        {"text": "测试记忆内容"}
    )
    time.sleep(0.1)

    event2 = timeline.record_event(
        mem_id,
        MemoryEventType.ACCESSED,
        {"query": "测试查询"}
    )
    time.sleep(0.1)

    event3 = timeline.record_event(
        mem_id,
        MemoryEventType.MODIFIED,
        {"old_text": "旧内容", "new_text": "新内容"}
    )

    print(f"记录了 {len(timeline.events)} 个事件")

    # 获取记忆时间线
    memory_timeline = timeline.get_memory_timeline(mem_id)
    print(f"\n记忆 {mem_id} 的时间线有 {len(memory_timeline)} 个事件")

    for event in memory_timeline:
        event_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(event.timestamp))
        print(f"  [{event_time}] {event.event_type}: {event.details}")

    assert len(memory_timeline) == 3

    # 测试过滤
    accessed_events = timeline.get_memory_timeline(
        mem_id,
        event_types=[MemoryEventType.ACCESSED]
    )
    print(f"\n访问事件数量: {len(accessed_events)}")
    assert len(accessed_events) == 1

    # 测试限制数量
    limited = timeline.get_memory_timeline(mem_id, limit=2)
    assert len(limited) == 2

    # 清理
    os.remove(test_path)
    print("\n✓ 基本时间线功能测试通过！")
    return True


def test_global_timeline():
    """测试全局时间线"""
    print("\n" + "=" * 60)
    print("测试 2: 全局时间线功能")
    print("=" * 60)

    test_path = "./data/test_global_temp.json"
    if os.path.exists(test_path):
        os.remove(test_path)

    timeline = MemoryTimeline(test_path)

    # 记录多个记忆的事件
    timeline.record_event("mem_001", MemoryEventType.CREATED)
    timeline.record_event("mem_002", MemoryEventType.CREATED)
    timeline.record_event("mem_001", MemoryEventType.ACCESSED)
    timeline.record_event("mem_003", MemoryEventType.CREATED)
    timeline.record_event("mem_002", MemoryEventType.MODIFIED)

    print(f"记录了 {len(timeline.events)} 个事件")

    # 获取全局时间线
    global_events = timeline.get_global_timeline()
    print(f"\n全局时间线有 {len(global_events)} 个事件")

    for event in global_events:
        event_time = time.strftime("%H:%M:%S", time.localtime(event.timestamp))
        print(f"  [{event_time}] {event.memory_id} - {event.event_type}")

    assert len(global_events) == 5

    # 测试按类型过滤
    created_events = timeline.get_global_timeline(
        event_types=[MemoryEventType.CREATED]
    )
    print(f"\n创建事件数量: {len(created_events)}")
    assert len(created_events) == 3

    # 测试限制数量
    limited = timeline.get_global_timeline(limit=3)
    assert len(limited) == 3

    # 清理
    os.remove(test_path)
    print("\n✓ 全局时间线功能测试通过！")
    return True


def test_statistics():
    """测试统计功能"""
    print("\n" + "=" * 60)
    print("测试 3: 统计功能")
    print("=" * 60)

    test_path = "./data/test_stats_temp.json"
    if os.path.exists(test_path):
        os.remove(test_path)

    timeline = MemoryTimeline(test_path)

    # 记录一些事件
    for i in range(5):
        timeline.record_event(f"mem_{i:03d}", MemoryEventType.CREATED)

    timeline.record_event("mem_000", MemoryEventType.ACCESSED)
    timeline.record_event("mem_000", MemoryEventType.ACCESSED)
    timeline.record_event("mem_000", MemoryEventType.MODIFIED)
    timeline.record_event("mem_001", MemoryEventType.ACCESSED)

    # 获取统计
    stats = timeline.get_event_statistics()
    print(f"\n统计信息:")
    print(f"  总事件数: {stats['total_events']}")
    print(f"  事件类型分布:")
    for et, count in stats['event_type_counts'].items():
        if count > 0:
            print(f"    {et}: {count}")
    print(f"  最活跃的记忆: {stats['most_active_memories'][:3]}")

    assert stats['total_events'] == 9
    assert stats['event_type_counts']['created'] == 5
    assert stats['event_type_counts']['accessed'] == 3

    # 测试活动摘要
    summary = timeline.get_activity_summary()
    print(f"\n活动摘要:")
    print(f"  时间段事件数: {summary['period_events']}")
    print(f"  每小时活动: {list(summary['hourly_activity'].keys())}")

    # 清理
    os.remove(test_path)
    print("\n✓ 统计功能测试通过！")
    return True


def test_enhanced_memory():
    """测试增强记忆系统"""
    print("\n" + "=" * 60)
    print("测试 4: 增强记忆系统")
    print("=" * 60)

    # 清理测试数据
    test_path = "./data/timeline.json"
    if os.path.exists(test_path):
        os.remove(test_path)

    # 创建系统
    memory = get_memory_system()
    enhanced = EnhancedMemoryWithTimeline(memory)

    # 清空现有数据
    memory.l1.clear()
    memory.l2.clear()
    memory.l3.clear()

    # 添加带跟踪的记忆
    mem1 = enhanced.add_with_tracking("项目计划文档", "proj_001", "l2")
    mem2 = enhanced.add_with_tracking("技术架构设计", "proj_001", "l2")
    print(f"添加了 2 个记忆并记录创建事件")

    # 跟踪访问
    enhanced.track_access(mem1, "查看项目计划")
    enhanced.track_access(mem1, "再次查看计划")
    print(f"记录了访问事件")

    # 获取记忆时间线
    mem1_timeline = enhanced.get_timeline(mem1)
    print(f"\n记忆 {mem1} 的时间线:")
    for event in mem1_timeline:
        event_time = time.strftime("%H:%M:%S", time.localtime(event.timestamp))
        print(f"  [{event_time}] {event.event_type}")

    assert len(mem1_timeline) == 3

    # 获取全局时间线
    global_timeline = enhanced.get_timeline()
    print(f"\n全局时间线有 {len(global_timeline)} 个事件")

    # 获取统计
    stats = enhanced.get_statistics()
    print(f"\n统计:")
    print(f"  总事件数: {stats['total_events']}")
    print(f"  最活跃记忆: {stats['most_active_memories']}")

    # 清理
    if os.path.exists(test_path):
        os.remove(test_path)

    print("\n✓ 增强记忆系统测试通过！")
    return True


def test_event_types():
    """测试不同类型的事件"""
    print("\n" + "=" * 60)
    print("测试 5: 不同类型的事件")
    print("=" * 60)

    test_path = "./data/test_types_temp.json"
    if os.path.exists(test_path):
        os.remove(test_path)

    timeline = MemoryTimeline(test_path)

    # 记录各种类型的事件
    mem_id = "mem_001"
    timeline.record_event(mem_id, MemoryEventType.CREATED)
    timeline.record_event(mem_id, MemoryEventType.MODIFIED)
    timeline.record_event(mem_id, MemoryEventType.ACCESSED)
    timeline.record_event(mem_id, MemoryEventType.TAG_ADDED, {"tag": "important"})
    timeline.record_event(mem_id, MemoryEventType.TAG_REMOVED, {"tag": "old"})
    timeline.record_event(mem_id, MemoryEventType.RELATION_ADDED, {"other_mem": "mem_002"})
    timeline.record_event(mem_id, MemoryEventType.IMPORTANCE_CHANGED, {"old": 1, "new": 5})

    # 检查所有类型
    events = timeline.get_memory_timeline(mem_id)
    event_types = {e.event_type for e in events}

    print(f"\n记录的事件类型: {sorted(event_types)}")

    assert len(events) == 7

    # 清理
    os.remove(test_path)
    print("\n✓ 不同类型事件测试通过！")
    return True


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("第19阶段测试：记忆时间线/历史记录功能")
    print("=" * 60)

    all_passed = True

    try:
        passed = test_basic_timeline()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试1失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_global_timeline()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试2失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_statistics()
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
        passed = test_event_types()
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
