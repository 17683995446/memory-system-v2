"""
分布式节点管理模块
基于第一性原理：一致性优先、分区容错、最终一致
简化Raft共识：Leader选举、日志复制、心跳机制
"""

import time
import threading
import json
import uuid
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import deque

from ..utils.logger import get_logger

logger = get_logger()


class NodeState(Enum):
    """节点状态"""
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    LEADER = "leader"


class LogEntryType(Enum):
    """日志条目类型"""
    ADD = "add"
    DELETE = "delete"
    UPDATE = "update"
    CONFIG_CHANGE = "config_change"


@dataclass
class LogEntry:
    """Raft日志条目"""
    term: int
    index: int
    entry_type: LogEntryType
    data: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)


@dataclass
class NodeInfo:
    """节点信息"""
    node_id: str
    address: str
    port: int
    state: NodeState = NodeState.FOLLOWER
    last_heartbeat: float = field(default_factory=time.time)
    is_alive: bool = True


class RaftConsensus:
    """简化Raft共识算法实现"""

    def __init__(self, node_id: str, peers: List[Dict[str, Any]],
                 heartbeat_interval: float = 0.5, election_timeout: float = 2.0):
        self.node_id = node_id
        self.peers: Dict[str, NodeInfo] = {}
        for peer in peers:
            if peer["node_id"] != node_id:
                self.peers[peer["node_id"]] = NodeInfo(
                    node_id=peer["node_id"],
                    address=peer.get("address", "localhost"),
                    port=peer.get("port", 8000)
                )

        self.state = NodeState.FOLLOWER
        self.current_term = 0
        self.voted_for: Optional[str] = None
        self.leader_id: Optional[str] = None

        # 日志
        self.log: List[LogEntry] = []
        self.commit_index = 0
        self.last_applied = 0

        # Leader状态
        self.next_index: Dict[str, int] = {}
        self.match_index: Dict[str, int] = {}

        # 定时器
        self.heartbeat_interval = heartbeat_interval
        self.election_timeout = election_timeout
        self.last_heartbeat_time = time.time()
        self.election_deadline = time.time() + self._random_timeout()

        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None

        # 已提交日志回调
        self._commit_callbacks: List[Callable[[LogEntry], None]] = []

    def _random_timeout(self) -> float:
        """随机选举超时（避免活锁）"""
        import random
        return self.election_timeout + random.uniform(0, self.election_timeout)

    def start(self):
        """启动Raft节点"""
        self._running = True
        self._thread = threading.Thread(target=self._main_loop, daemon=True)
        self._thread.start()
        logger.info(f"[Raft] Node {self.node_id} started as {self.state.value}")

    def stop(self):
        """停止Raft节点"""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        logger.info(f"[Raft] Node {self.node_id} stopped")

    def _main_loop(self):
        """主循环"""
        while self._running:
            with self._lock:
                now = time.time()

                if self.state == NodeState.LEADER:
                    # Leader: 发送心跳
                    if now - self.last_heartbeat_time >= self.heartbeat_interval:
                        self._send_heartbeats()
                        self.last_heartbeat_time = now
                else:
                    # Follower/Candidate: 检查选举超时
                    if now >= self.election_deadline:
                        self._start_election()

            time.sleep(0.05)

    def _start_election(self):
        """开始选举"""
        self.state = NodeState.CANDIDATE
        self.current_term += 1
        self.voted_for = self.node_id
        self.election_deadline = time.time() + self._random_timeout()

        logger.info(f"[Raft] Node {self.node_id} starting election for term {self.current_term}")

        # 给自己投票
        votes = 1

        # 请求其他节点投票（简化：直接计算）
        for peer_id in self.peers:
            if self._request_vote(peer_id):
                votes += 1

        # 检查是否获得多数票
        if votes > (len(self.peers) + 1) / 2:
            self._become_leader()

    def _request_vote(self, peer_id: str) -> bool:
        """请求投票（模拟RPC）"""
        # 简化实现：随机返回，实际应通过网络RPC
        import random
        return random.random() > 0.3

    def _become_leader(self):
        """成为Leader"""
        self.state = NodeState.LEADER
        self.leader_id = self.node_id
        logger.info(f"[Raft] Node {self.node_id} became leader for term {self.current_term}")

        # 初始化Leader状态
        next_idx = len(self.log) + 1
        for peer_id in self.peers:
            self.next_index[peer_id] = next_idx
            self.match_index[peer_id] = 0

    def _send_heartbeats(self):
        """发送心跳（简化）"""
        for peer_id in self.peers:
            self.peers[peer_id].last_heartbeat = time.time()

    def append_entries(self, entries: List[LogEntry]) -> bool:
        """追加日志条目（Leader调用）"""
        with self._lock:
            if self.state != NodeState.LEADER:
                return False

            for entry in entries:
                entry.term = self.current_term
                entry.index = len(self.log) + 1
                self.log.append(entry)

            # 简化：直接提交（实际需等待多数复制）
            self._commit_entries()
            return True

    def _commit_entries(self):
        """提交日志条目"""
        # 简化：Leader直接提交
        while self.commit_index < len(self.log):
            self.commit_index += 1
            entry = self.log[self.commit_index - 1]
            logger.info(f"[Raft] Committed entry {entry.index} (term {entry.term})")

            # 通知回调
            for callback in self._commit_callbacks:
                try:
                    callback(entry)
                except Exception as e:
                    logger.error(f"[Raft] Commit callback error: {e}")

    def receive_append_entries(self, term: int, leader_id: str, entries: List[Dict],
                               leader_commit: int) -> bool:
        """接收AppendEntries RPC（Follower调用）"""
        with self._lock:
            if term < self.current_term:
                return False

            self.current_term = term
            self.leader_id = leader_id
            self.state = NodeState.FOLLOWER
            self.last_heartbeat_time = time.time()
            self.election_deadline = time.time() + self._random_timeout()

            # 追加日志（简化）
            for entry_data in entries:
                entry = LogEntry(
                    term=term,
                    index=entry_data["index"],
                    entry_type=LogEntryType(entry_data["entry_type"]),
                    data=entry_data["data"]
                )
                if entry.index > len(self.log):
                    self.log.append(entry)

            # 更新commit_index
            if leader_commit > self.commit_index:
                self.commit_index = min(leader_commit, len(self.log))
                self._commit_entries()

            return True

    def add_commit_callback(self, callback: Callable[[LogEntry], None]):
        """添加提交回调"""
        self._commit_callbacks.append(callback)

    def get_status(self) -> Dict[str, Any]:
        """获取节点状态"""
        with self._lock:
            return {
                "node_id": self.node_id,
                "state": self.state.value,
                "term": self.current_term,
                "leader_id": self.leader_id,
                "log_size": len(self.log),
                "commit_index": self.commit_index,
                "peers": len(self.peers)
            }


class DistributedMemorySystem:
    """分布式记忆系统"""

    def __init__(self, node_id: Optional[str] = None, peers: Optional[List[Dict]] = None):
        self.node_id = node_id or str(uuid.uuid4())[:8]
        self.raft = RaftConsensus(
            node_id=self.node_id,
            peers=peers or []
        )
        self.local_data: Dict[str, Any] = {}
        self._lock = threading.Lock()

        # 注册日志提交回调
        self.raft.add_commit_callback(self._on_log_committed)

    def _on_log_committed(self, entry: LogEntry):
        """日志提交回调 - 应用到本地状态机"""
        with self._lock:
            if entry.entry_type == LogEntryType.ADD:
                key = entry.data.get("key")
                value = entry.data.get("value")
                if key:
                    self.local_data[key] = value
                    logger.info(f"[Distributed] Applied ADD: {key}")
            elif entry.entry_type == LogEntryType.DELETE:
                key = entry.data.get("key")
                if key and key in self.local_data:
                    del self.local_data[key]
                    logger.info(f"[Distributed] Applied DELETE: {key}")

    def add(self, key: str, value: Any) -> bool:
        """添加数据（通过Raft共识）"""
        entry = LogEntry(
            term=0,  # 由Raft设置
            index=0,  # 由Raft设置
            entry_type=LogEntryType.ADD,
            data={"key": key, "value": value}
        )
        return self.raft.append_entries([entry])

    def delete(self, key: str) -> bool:
        """删除数据（通过Raft共识）"""
        entry = LogEntry(
            term=0,
            index=0,
            entry_type=LogEntryType.DELETE,
            data={"key": key}
        )
        return self.raft.append_entries([entry])

    def get(self, key: str) -> Optional[Any]:
        """获取数据（本地读取）"""
        with self._lock:
            return self.local_data.get(key)

    def get_all(self) -> Dict[str, Any]:
        """获取所有数据"""
        with self._lock:
            return dict(self.local_data)

    def start(self):
        """启动分布式系统"""
        self.raft.start()

    def stop(self):
        """停止分布式系统"""
        self.raft.stop()

    def get_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            "node_id": self.node_id,
            "raft": self.raft.get_status(),
            "local_data_size": len(self.local_data)
        }


class ClusterManager:
    """集群管理器"""

    def __init__(self):
        self.nodes: Dict[str, DistributedMemorySystem] = {}
        self._lock = threading.Lock()

    def add_node(self, node: DistributedMemorySystem):
        """添加节点"""
        with self._lock:
            self.nodes[node.node_id] = node

    def remove_node(self, node_id: str):
        """移除节点"""
        with self._lock:
            if node_id in self.nodes:
                self.nodes[node_id].stop()
                del self.nodes[node_id]

    def get_leader(self) -> Optional[str]:
        """获取Leader节点ID"""
        with self._lock:
            for node_id, node in self.nodes.items():
                if node.raft.state == NodeState.LEADER:
                    return node_id
            return None

    def get_cluster_status(self) -> Dict[str, Any]:
        """获取集群状态"""
        with self._lock:
            nodes = dict(self.nodes)
            node_count = len(self.nodes)

        # 在锁外调用get_status和get_leader避免死锁
        leader = self.get_leader()
        return {
            "nodes": {
                node_id: node.get_status()
                for node_id, node in nodes.items()
            },
            "node_count": node_count,
            "leader": leader
        }
