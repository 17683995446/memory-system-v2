"""
第23阶段测试：记忆提醒/定时任务功能
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.memory import get_memory_system
from src.reminders import (
    ReminderScheduler,
    Reminder,
    ReminderStatus,
    TriggerType,
    EnhancedMemoryWithReminders
)


def test_basic_reminder():
    """测试基本提醒功能"""
    print("\n" + "=" * 60)
    print("测试 1: 基本提醒功能")
    print("=" * 60)

    scheduler = ReminderScheduler()

    # 创建时间提醒
    reminder = Reminder(
        memory_id="mem_001",
        trigger_type=TriggerType.TIME_BASED,
        title="项目截止日期提醒",
        message="别忘了明天是项目截止日期！",
        trigger_time=time.time() + 3600
    )

    reminder_id = scheduler.add_reminder(reminder)
    print(f"\n创建提醒: {reminder_id}")

    # 验证添加
    assert scheduler.get_reminder(reminder_id) is not None
    assert len(scheduler.get_pending_reminders()) == 1

    # 取消提醒
    cancelled = scheduler.remove_reminder(reminder_id)
    assert cancelled
    assert scheduler.get_reminder(reminder_id).status == ReminderStatus.CANCELLED.value

    print("✓ 基本提醒功能测试通过！")
    return True


def test_time_based_reminder():
    """测试基于时间的提醒"""
    print("\n" + "=" * 60)
    print("测试 2: 基于时间的提醒")
    print("=" * 60)

    scheduler = ReminderScheduler()

    # 创建多个提醒
    now = time.time()

    # 1分钟后触发
    reminder1 = Reminder(
        memory_id="mem_001",
        trigger_type=TriggerType.TIME_BASED,
        title="提醒1",
        trigger_time=now + 60
    )

    # 2分钟后触发
    reminder2 = Reminder(
        memory_id="mem_002",
        trigger_type=TriggerType.TIME_BASED,
        title="提醒2",
        trigger_time=now + 120
    )

    # 已经过期（立即触发）
    reminder3 = Reminder(
        memory_id="mem_003",
        trigger_type=TriggerType.TIME_BASED,
        title="提醒3",
        trigger_time=now - 1
    )

    scheduler.add_reminder(reminder1)
    scheduler.add_reminder(reminder2)
    scheduler.add_reminder(reminder3)

    print(f"\n创建了 {len(scheduler.reminders)} 个提醒")

    # 触发已过期的提醒
    triggered = scheduler.check_time_based_reminders()
    print(f"触发了 {len(triggered)} 个提醒")

    assert len(triggered) == 1
    assert scheduler.get_reminder(triggered[0]).status == ReminderStatus.TRIGGERED.value

    print("✓ 基于时间的提醒测试通过！")
    return True


def test_recurring_reminder():
    """测试重复提醒"""
    print("\n" + "=" * 60)
    print("测试 3: 重复提醒")
    print("=" * 60)

    scheduler = ReminderScheduler()

    # 创建重复提醒（每小时执行一次）
    reminder = Reminder(
        memory_id="mem_001",
        trigger_type=TriggerType.RECURRING,
        title="每小时健康提醒",
        message="站起来活动一下！",
        recurring_config={"interval_seconds": 3600}
    )

    scheduler.add_reminder(reminder)

    # 触发第一次
    triggered = scheduler.trigger_reminder(reminder.reminder_id)
    assert triggered

    reminder = scheduler.get_reminder(reminder.reminder_id)
    print(f"\n触发后状态: {reminder.status}")
    print(f"触发次数: {reminder.execution_count}")
    print(f"下次触发时间: {reminder.trigger_time}")

    assert reminder.status == ReminderStatus.PENDING.value
    assert reminder.execution_count == 1

    print("✓ 重复提醒测试通过！")
    return True


def test_condition_reminder():
    """测试条件提醒"""
    print("\n" + "=" * 60)
    print("测试 4: 条件提醒")
    print("=" * 60)

    scheduler = ReminderScheduler()

    # 条件提醒 - 初始条件不满足
    reminder = Reminder(
        memory_id="mem_001",
        trigger_type=TriggerType.CONDITION_BASED,
        title="当项目状态变更时提醒",
        condition={
            "check": "project_status",
            "value": "pending"  # 初始状态是pending
        }
    )

    scheduler.add_reminder(reminder)

    # 条件评估函数 - 检查project_status是否为completed
    def evaluator(condition):
        return condition.get("value") == "completed"

    # 检查（条件不满足，因为value还是pending）
    triggered1 = scheduler.check_condition_based_reminders(evaluator)
    print(f"\n条件检查1（不满足）: {len(triggered1)} 个触发")
    assert len(triggered1) == 0

    # 模拟状态变更（修改条件）
    reminder.condition["value"] = "completed"

    # 检查（条件满足）
    triggered2 = scheduler.check_condition_based_reminders(evaluator)
    print(f"条件检查2（满足）: {len(triggered2)} 个触发")
    assert len(triggered2) == 1

    print("✓ 条件提醒测试通过！")
    return True


def test_callback():
    """测试回调功能"""
    print("\n" + "=" * 60)
    print("测试 5: 回调功能")
    print("=" * 60)

    scheduler = ReminderScheduler()

    triggered_reminders = []

    def callback(reminder):
        triggered_reminders.append(reminder.reminder_id)
        print(f"  回调触发: {reminder.title}")

    scheduler.register_callback(callback)

    # 创建提醒
    reminder = Reminder(
        memory_id="mem_001",
        trigger_type=TriggerType.TIME_BASED,
        title="回调测试提醒",
        trigger_time=time.time() - 1
    )

    scheduler.add_reminder(reminder)

    # 触发
    scheduler.check_time_based_reminders()

    assert len(triggered_reminders) == 1
    assert triggered_reminders[0] == reminder.reminder_id

    print("✓ 回调功能测试通过！")
    return True


def test_enhanced_memory():
    """测试增强记忆系统"""
    print("\n" + "=" * 60)
    print("测试 6: 增强记忆系统")
    print("=" * 60)

    memory = get_memory_system()
    enhanced = EnhancedMemoryWithReminders(memory)

    # 清空现有数据
    memory.l1.clear()
    memory.l2.clear()
    memory.l3.clear()

    # 添加记忆
    mem_id = memory.add("重要会议记录", "proj_001", "l2")
    print(f"\n添加记忆: {mem_id}")

    # 创建时间提醒
    reminder_id = enhanced.create_time_reminder(
        memory_id=mem_id,
        title="回顾会议记录",
        trigger_time=time.time() + 3600,
        message="别忘了回顾今天的会议记录"
    )
    print(f"创建时间提醒: {reminder_id}")

    # 创建重复提醒
    recurring_id = enhanced.create_recurring_reminder(
        memory_id=mem_id,
        title="每日回顾",
        interval_seconds=86400,
        message="每天提醒回顾重要记忆"
    )
    print(f"创建重复提醒: {recurring_id}")

    # 获取记忆的提醒
    reminders = enhanced.get_memory_reminders(mem_id)
    print(f"\n记忆 {mem_id} 有 {len(reminders)} 个提醒")

    # 获取统计
    stats = enhanced.get_reminder_statistics()
    print(f"\n提醒统计:")
    print(f"  总提醒数: {stats['total_reminders']}")
    print(f"  待触发: {stats['pending']}")
    print(f"  类型分布: {stats['type_distribution']}")

    assert stats['total_reminders'] == 2

    # 取消提醒
    cancelled = enhanced.cancel_reminder(recurring_id)
    assert cancelled

    stats_after = enhanced.get_reminder_statistics()
    print(f"\n取消后统计:")
    print(f"  待触发: {stats_after['pending']}")

    print("✓ 增强记忆系统测试通过！")
    return True


def test_statistics():
    """测试统计功能"""
    print("\n" + "=" * 60)
    print("测试 7: 统计功能")
    print("=" * 60)

    scheduler = ReminderScheduler()

    # 创建多种类型的提醒
    for i in range(5):
        scheduler.add_reminder(Reminder(
            memory_id=f"mem_{i}",
            trigger_type=TriggerType.TIME_BASED,
            title=f"提醒{i}",
            trigger_time=time.time() + 1000 * i
        ))

    for i in range(3):
        scheduler.add_reminder(Reminder(
            memory_id=f"mem_recurring_{i}",
            trigger_type=TriggerType.RECURRING,
            title=f"重复提醒{i}",
            recurring_config={"interval_seconds": 3600}
        ))

    # 触发一些
    scheduler.trigger_reminder(list(scheduler.reminders.values())[0].reminder_id)
    scheduler.trigger_reminder(list(scheduler.reminders.values())[1].reminder_id)

    # 取消一个
    scheduler.remove_reminder(list(scheduler.reminders.values())[2].reminder_id)

    # 获取统计
    stats = scheduler.get_statistics()
    print(f"\n统计信息:")
    print(f"  总提醒数: {stats['total_reminders']}")
    print(f"  待触发: {stats['pending']}")
    print(f"  已触发: {stats['triggered']}")
    print(f"  已取消: {stats['cancelled']}")
    print(f"  类型分布: {stats['type_distribution']}")

    assert stats['total_reminders'] == 8
    assert stats['triggered'] == 2
    assert stats['cancelled'] == 1

    print("✓ 统计功能测试通过！")
    return True


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("第23阶段测试：记忆提醒/定时任务功能")
    print("=" * 60)

    all_passed = True

    try:
        passed = test_basic_reminder()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试1失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_time_based_reminder()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试2失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_recurring_reminder()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试3失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_condition_reminder()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试4失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_callback()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试5失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_enhanced_memory()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试6失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_statistics()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试7失败: {e}")
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
