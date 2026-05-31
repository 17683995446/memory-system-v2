"""
基于第一性原理的Agent可靠记忆系统 - 第4阶段测试
测试记忆自治治理与迭代优化功能
"""
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.governance import (
    get_forget_thresholds, get_adaptive_forget_policy,
    get_version_manager, get_memory_correction,
    get_memory_isolation, get_memory_switch,
    get_statistics_collector, get_anomaly_marker,
    get_auto_task_scheduler, get_experience_converter,
    MemoryType, AccessLevel, TaskType
)


def test_forget_policy():
    """测试遗忘策略"""
    print("\n" + "="*50)
    print("测试1: 遗忘量化阈值")
    print("="*50)
    
    # 测试1.1: 遗忘阈值
    print("\n[1.1] 遗忘阈值测试")
    thresholds = get_forget_thresholds()
    
    print(f"  L1 TTL: {thresholds.l1_ttl_seconds}秒")
    print(f"  L2 最大天数: {thresholds.l2_max_days}天")
    print(f"  L2 最低访问次数: {thresholds.l2_min_access_count}")
    
    # 测试1.2: 自适应遗忘策略
    print("\n[1.2] 自适应遗忘策略测试")
    policy = get_adaptive_forget_policy()
    
    item1 = {'last_access': time.time() - 86400 * 60, 'access_count': 1}
    item2 = {'last_access': time.time() - 86400 * 10, 'access_count': 5}
    
    should_forget1, reason1 = policy.should_forget('l2', item1)
    should_forget2, reason2 = policy.should_forget('l2', item2)
    
    print(f"  项目1 (60天未访问,1次): 遗忘={should_forget1}, 原因={reason1}")
    print(f"  项目2 (10天未访问,5次): 遗忘={should_forget2}, 原因={reason2}")


def test_version_management():
    """测试版本管理"""
    print("\n" + "="*50)
    print("测试2: 记忆版本管理")
    print("="*50)
    
    version_manager = get_version_manager()
    
    # 测试2.1: 记录版本
    print("\n[2.1] 记录版本测试")
    content1 = {'name': 'test', 'value': 'original'}
    version_id1 = version_manager.record_version('item_001', 'l2', content1, 'create')
    print(f"  创建版本: {version_id1}")
    
    # 更新
    content2 = {'name': 'test', 'value': 'updated'}
    version_id2 = version_manager.record_version('item_001', 'l2', content2, 'update')
    print(f"  更新版本: {version_id2}")
    
    # 测试2.2: 获取版本历史
    print("\n[2.2] 获取版本历史")
    versions = version_manager.get_versions('item_001')
    print(f"  版本数量: {len(versions)}")
    for v in versions:
        print(f"    {v['version_id']}: {v['content']['value']} ({v['action']})")
    
    # 测试2.3: 回滚
    print("\n[2.3] 回滚测试")
    rolled_back = version_manager.rollback_to_version('item_001', version_id1)
    if rolled_back:
        print(f"  ✓ 回滚成功: {rolled_back['value']}")


def test_memory_correction():
    """测试记忆纠错"""
    print("\n" + "="*50)
    print("测试3: 错误记忆人工修正")
    print("="*50)
    
    correction = get_memory_correction()
    version_manager = get_version_manager()
    
    # 提交修正
    print("\n[3.1] 提交修正")
    new_content = {'name': 'test', 'value': 'corrected', 'memory_level': 'l2'}
    version_id = correction.submit_correction(
        'item_001',
        new_content,
        '修正错误数据',
        'admin'
    )
    print(f"  ✓ 提交修正: {version_id}")
    
    # 获取待处理修正
    pending = correction.get_pending_corrections()
    print(f"  待处理修正数: {len(pending)}")


def test_memory_isolation():
    """测试记忆隔离"""
    print("\n" + "="*50)
    print("测试4: 公私记忆隔离")
    print("="*50)
    
    isolation = get_memory_isolation()
    
    # 测试4.1: 创建公共记忆
    print("\n[4.1] 创建公共记忆")
    acl_public = isolation.create_memory(
        'public_rule_001',
        MemoryType.PUBLIC,
        'admin'
    )
    print(f"  ✓ 创建公共记忆: {acl_public.item_id}")
    
    # 测试4.2: 创建私有记忆
    print("\n[4.2] 创建私有记忆")
    acl_private = isolation.create_memory(
        'private_data_001',
        MemoryType.PRIVATE,
        'user_001'
    )
    print(f"  ✓ 创建私有记忆: {acl_private.item_id}")
    
    # 测试4.3: 访问控制
    print("\n[4.3] 访问控制测试")
    can_access_user1 = isolation.check_access('public_rule_001', 'user_001')
    can_access_user2 = isolation.check_access('private_data_001', 'user_001')
    can_access_user3 = isolation.check_access('private_data_001', 'user_002')
    
    print(f"  user_001访问公共记忆: {can_access_user1} ✓")
    print(f"  user_001访问自己的私有记忆: {can_access_user2} ✓")
    print(f"  user_002访问user_001的私有记忆: {can_access_user3} (应False)")


def test_memory_switch():
    """测试记忆开关"""
    print("\n" + "="*50)
    print("测试5: 记忆开关控制")
    print("="*50)
    
    switch = get_memory_switch()
    
    # 测试5.1: 全局开关
    print("\n[5.1] 全局开关测试")
    switch.disable_global()
    is_enabled = switch.is_enabled()
    print(f"  全局禁用后是否启用: {is_enabled} (应False)")
    
    switch.enable_global()
    is_enabled = switch.is_enabled()
    print(f"  全局启用后是否启用: {is_enabled} (应True)")
    
    # 测试5.2: 用户开关
    print("\n[5.2] 用户开关测试")
    switch.disable_user('user_test')
    is_enabled = switch.is_enabled(user='user_test')
    print(f"  禁用user_test后是否启用: {is_enabled} (应False)")


def test_statistics():
    """测试统计面板"""
    print("\n" + "="*50)
    print("测试6: 记忆数据统计")
    print("="*50)
    
    stats = get_statistics_collector()
    
    # 记录一些操作
    print("\n[6.1] 记录操作")
    stats.record_operation('read', 'l1', 'item_001', duration_ms=10)
    stats.record_operation('write', 'l2', 'item_002', duration_ms=20)
    stats.record_operation('recall', 'l3', 'item_003', duration_ms=15)
    print(f"  ✓ 记录了3条操作")
    
    # 获取统计
    print("\n[6.2] 获取统计摘要")
    summary = stats.get_summary()
    print(f"  总操作数: {summary['total_operations']}")
    print(f"  操作类型: {summary['operations_by_type']}")
    print(f"  成功率: {summary['success_rate']:.2%}")


def test_anomaly_detection():
    """测试异常检测"""
    print("\n" + "="*50)
    print("测试7: 异常记忆标记")
    print("="*50)
    
    anomaly_marker = get_anomaly_marker()
    
    # 标记异常
    print("\n[7.1] 标记异常")
    anomaly_id = anomaly_marker.mark_anomaly(
        'high_error_rate',
        '错误率超过10%',
        'high'
    )
    print(f"  ✓ 标记异常: {anomaly_id}")
    
    # 获取未解决异常
    unresolved = anomaly_marker.get_unresolved_anomalies()
    print(f"  未解决异常数: {len(unresolved)}")


def test_experience_converter():
    """测试经验转规则"""
    print("\n" + "="*50)
    print("测试8: 经验转规则自动化")
    print("="*50)
    
    converter = get_experience_converter()
    
    # 提取规则
    print("\n[8.1] 提取规则")
    experience = {
        'id': 'exp_001',
        'entity': '天气',
        'attribute': '查询',
        'value': '晴',
        'confidence': 0.8
    }
    
    rule = converter.extract_rule_from_experience(experience, confidence_threshold=0.7)
    if rule:
        print(f"  ✓ 提取规则成功")
        print(f"    实体: {rule['entity']}")
        print(f"    属性: {rule['attribute']}")
        print(f"    值: {rule['value']}")
        print(f"    置信度: {rule['confidence']}")
    
    # 批量转换
    print("\n[8.2] 批量转换")
    experiences = [
        {'id': 'exp_002', 'entity': 'A', 'attribute': 'B', 'value': 'C', 'confidence': 0.8},
        {'id': 'exp_003', 'entity': 'D', 'attribute': 'E', 'value': 'F', 'confidence': 0.5},
        {'id': 'exp_004', 'entity': 'G', 'attribute': 'H', 'value': 'I', 'confidence': 0.9},
    ]
    
    rules = converter.batch_convert(experiences, confidence_threshold=0.7)
    print(f"  转换结果: {len(rules)}条规则 (预期2条)")


def main():
    """主测试函数"""
    print("="*60)
    print("基于第一性原理的Agent可靠记忆系统 - 第4阶段测试")
    print("记忆自治治理与迭代优化体系")
    print("="*60)
    
    try:
        test_forget_policy()
        test_version_management()
        test_memory_correction()
        test_memory_isolation()
        test_memory_switch()
        test_statistics()
        test_anomaly_detection()
        test_experience_converter()
        
        print("\n" + "="*60)
        print("✓ 所有测试完成！")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
