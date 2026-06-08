#!/usr/bin/env python3
"""
分布式系统测试 - 验证Raft共识、Leader选举、数据复制
"""

import sys
import time
sys.path.insert(0, '/workspace')

from src.distributed import (
    RaftConsensus, DistributedMemorySystem, ClusterManager,
    NodeState, LogEntry, LogEntryType
)


def test_raft_manual_leader():
    """测试手动设置Leader和日志复制"""
    print("[Distributed] 测试Raft日志复制...")

    raft = RaftConsensus("node1", [])

    # 手动成为Leader（跳过选举）
    raft.state = NodeState.LEADER
    raft.leader_id = "node1"
    raft.current_term = 1

    # 追加日志
    entry1 = LogEntry(term=1, index=1, entry_type=LogEntryType.ADD, data={"key": "a", "value": 1})
    entry2 = LogEntry(term=1, index=2, entry_type=LogEntryType.ADD, data={"key": "b", "value": 2})

    success = raft.append_entries([entry1, entry2])
    assert success, "追加日志应该成功"
    assert len(raft.log) == 2, f"日志应该有2条，实际有{len(raft.log)}"
    assert raft.commit_index == 2, f"commit_index应该是2，实际是{raft.commit_index}"

    print("[Distributed] 日志复制通过")
    return True


def test_distributed_state_machine():
    """测试分布式状态机应用"""
    print("[Distributed] 测试状态机应用...")

    system = DistributedMemorySystem("node1", [])

    # 手动设置Raft为Leader
    system.raft.state = NodeState.LEADER
    system.raft.leader_id = "node1"
    system.raft.current_term = 1

    # 添加数据
    success = system.add("key1", "value1")
    assert success, "添加应该成功"

    # 验证数据已应用到状态机
    value = system.get("key1")
    assert value == "value1", f"获取的值应该是value1，实际是{value}"

    # 添加更多数据
    system.add("key2", "value2")
    system.add("key3", "value3")

    # 验证所有数据
    all_data = system.get_all()
    assert len(all_data) == 3, f"应该有3条数据，实际有{len(all_data)}"

    # 删除数据
    system.delete("key2")
    assert system.get("key2") is None
    assert len(system.get_all()) == 2

    print("[Distributed] 状态机应用通过")
    return True


def test_raft_election_timeout():
    """测试Raft选举超时机制"""
    print("[Distributed] 测试选举超时...")

    raft = RaftConsensus("timeout_node", [], election_timeout=0.3)
    raft.start()

    # 初始状态是Follower
    assert raft.state == NodeState.FOLLOWER

    # 等待超过选举超时
    time.sleep(1.5)

    # 应该已经变成Candidate或Leader
    assert raft.state in (NodeState.CANDIDATE, NodeState.LEADER), \
        f"状态应该是CANDIDATE或LEADER，实际是{raft.state.value}"

    print(f"[Distributed] 选举超时通过: 状态={raft.state.value}")

    raft.stop()
    # 确保线程完全停止
    time.sleep(0.2)
    return True


def test_cluster_manager():
    """测试集群管理器"""
    print("[Distributed] 测试集群管理器...")

    cluster = ClusterManager()

    node1 = DistributedMemorySystem("cm_node1", [])
    node2 = DistributedMemorySystem("cm_node2", [])

    cluster.add_node(node1)
    cluster.add_node(node2)

    # 获取集群状态
    status = cluster.get_cluster_status()
    assert status["node_count"] == 2

    # 移除节点
    cluster.remove_node("cm_node1")
    status = cluster.get_cluster_status()
    assert status["node_count"] == 1

    print(f"[Distributed] 集群管理器通过")
    return True


def test_raft_log_consistency():
    """测试Raft日志一致性"""
    print("[Distributed] 测试日志一致性...")

    raft = RaftConsensus("consistency_node", [], election_timeout=60.0)
    raft.state = NodeState.LEADER
    raft.current_term = 1

    # 添加一系列日志
    for i in range(10):
        entry = LogEntry(
            term=1,
            index=i+1,
            entry_type=LogEntryType.ADD,
            data={"key": f"key{i}", "value": i}
        )
        raft.append_entries([entry])

    # 验证日志连续性
    assert len(raft.log) == 10
    for i, entry in enumerate(raft.log):
        assert entry.index == i + 1, f"日志索引不连续: {entry.index} != {i+1}"
        assert entry.term == 1

    # 验证commit_index
    assert raft.commit_index == 10

    print("[Distributed] 日志一致性通过")
    return True


def run_all_distributed_tests():
    """运行所有分布式测试"""
    print("=" * 80)
    print("分布式系统测试开始")
    print("=" * 80)

    tests = [
        test_raft_manual_leader,
        test_distributed_state_machine,
        test_raft_election_timeout,
        test_cluster_manager,
        test_raft_log_consistency,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            failed += 1
            print(f"[Distributed] 测试失败: {test.__name__}: {e}")

    print("\n" + "=" * 80)
    print(f"分布式系统测试完成: 通过={passed}, 失败={failed}")
    print("=" * 80)

    return failed == 0


if __name__ == "__main__":
    success = run_all_distributed_tests()
    sys.exit(0 if success else 1)
