"""
记忆系统高级可视化和用户界面
基于第一性原理：从基础图形元素开始，构建完整的可视化系统
"""

import json
import math
import time
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import uuid


class VisualizationType(Enum):
    """可视化类型"""
    NETWORK_GRAPH = "network_graph"
    TIMELINE = "timeline"
    DASHBOARD = "dashboard"
    INTERACTIVE_MAP = "interactive_map"


class NodeType(Enum):
    """节点类型"""
    MEMORY = "memory"
    CATEGORY = "category"
    TAG = "tag"
    CLUSTER = "cluster"


class EdgeType(Enum):
    """边类型"""
    RELATION = "relation"
    SIMILAR = "similar"
    CO_OCCURRENCE = "co_occurrence"
    TEMPORAL = "temporal"


@dataclass
class Node:
    """图节点"""
    id: str
    label: str
    type: NodeType
    x: float = 0.0
    y: float = 0.0
    size: float = 10.0
    color: str = "#3498db"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Edge:
    """图边"""
    id: str
    source: str
    target: str
    type: EdgeType
    weight: float = 1.0
    label: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NetworkGraph:
    """网络图数据结构"""
    nodes: List[Node] = field(default_factory=list)
    edges: List[Edge] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TimelineEvent:
    """时间线事件"""
    id: str
    timestamp: float
    title: str
    description: str
    memory_id: Optional[str] = None
    type: str = "memory"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Timeline:
    """时间线数据结构"""
    events: List[TimelineEvent] = field(default_factory=list)
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DashboardWidget:
    """仪表盘组件"""
    id: str
    type: str
    title: str
    data: Dict[str, Any] = field(default_factory=dict)
    position: Tuple[int, int] = (0, 0)
    size: Tuple[int, int] = (4, 3)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Dashboard:
    """仪表盘数据结构"""
    widgets: List[DashboardWidget] = field(default_factory=list)
    layout: str = "grid"
    theme: str = "light"
    metadata: Dict[str, Any] = field(default_factory=dict)


class NetworkGraphVisualizer:
    """记忆关系网络图可视化器"""

    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.edges: Dict[str, Edge] = {}
        self.adjacency_list: Dict[str, List[str]] = defaultdict(list)

    def add_node(
        self,
        node_id: str,
        label: str,
        node_type: NodeType = NodeType.MEMORY,
        metadata: Dict[str, Any] = None
    ) -> Node:
        """添加节点"""
        node = Node(
            id=node_id,
            label=label,
            type=node_type,
            metadata=metadata or {}
        )
        self.nodes[node_id] = node
        return node

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: EdgeType = EdgeType.RELATION,
        weight: float = 1.0,
        label: str = ""
    ) -> Optional[Edge]:
        """添加边"""
        if source_id not in self.nodes or target_id not in self.nodes:
            return None

        edge_id = f"{source_id}-{target_id}"
        edge = Edge(
            id=edge_id,
            source=source_id,
            target=target_id,
            type=edge_type,
            weight=weight,
            label=label
        )
        self.edges[edge_id] = edge
        self.adjacency_list[source_id].append(target_id)
        self.adjacency_list[target_id].append(source_id)
        return edge

    def calculate_layout(self, width: float = 800, height: float = 600):
        """计算图布局（简单力导向算法）"""
        import random

        # 初始化随机位置
        for node in self.nodes.values():
            node.x = random.random() * width
            node.y = random.random() * height

        # 简单迭代布局优化
        iterations = 50
        for i in range(iterations):
            for node in self.nodes.values():
                # 排斥力
                fx, fy = 0.0, 0.0
                for other in self.nodes.values():
                    if node.id != other.id:
                        dx = node.x - other.x
                        dy = node.y - other.y
                        dist = math.sqrt(dx * dx + dy * dy)
                        if dist > 0:
                            repulsion = 100.0 / (dist * dist)
                            fx += (dx / dist) * repulsion
                            fy += (dy / dist) * repulsion

                # 吸引力
                for neighbor_id in self.adjacency_list[node.id]:
                    neighbor = self.nodes[neighbor_id]
                    dx = node.x - neighbor.x
                    dy = node.y - neighbor.y
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist > 0:
                        attraction = 0.1 * dist
                        fx -= (dx / dist) * attraction
                        fy -= (dy / dist) * attraction

                # 更新位置
                node.x = max(10, min(width - 10, node.x + fx * 0.1))
                node.y = max(10, min(height - 10, node.y + fy * 0.1))

    def get_network_graph(self) -> NetworkGraph:
        """获取网络图数据"""
        return NetworkGraph(
            nodes=list(self.nodes.values()),
            edges=list(self.edges.values())
        )

    def to_json(self) -> str:
        """导出为JSON（用于前端渲染）"""
        graph = self.get_network_graph()
        return json.dumps({
            "nodes": [
                {
                    "id": n.id,
                    "label": n.label,
                    "type": n.type.value,
                    "x": n.x,
                    "y": n.y,
                    "size": n.size,
                    "color": n.color,
                    "metadata": n.metadata
                }
                for n in graph.nodes
            ],
            "edges": [
                {
                    "id": e.id,
                    "source": e.source,
                    "target": e.target,
                    "type": e.type.value,
                    "weight": e.weight,
                    "label": e.label
                }
                for e in graph.edges
            ]
        }, ensure_ascii=False)


class TimelineVisualizer:
    """记忆时间线可视化器"""

    def __init__(self):
        self.events: List[TimelineEvent] = []
        self._sorted: bool = False

    def add_event(
        self,
        title: str,
        description: str,
        timestamp: float = None,
        memory_id: str = None,
        event_type: str = "memory",
        metadata: Dict[str, Any] = None
    ) -> TimelineEvent:
        """添加时间线事件"""
        event = TimelineEvent(
            id=str(uuid.uuid4()),
            timestamp=timestamp or time.time(),
            title=title,
            description=description,
            memory_id=memory_id,
            type=event_type,
            metadata=metadata or {}
        )
        self.events.append(event)
        self._sorted = False
        return event

    def sort_events(self):
        """按时间排序事件"""
        self.events.sort(key=lambda e: e.timestamp)
        self._sorted = True

    def get_time_range(self) -> Tuple[Optional[float], Optional[float]]:
        """获取时间范围"""
        if not self.events:
            return None, None

        if not self._sorted:
            self.sort_events()

        return self.events[0].timestamp, self.events[-1].timestamp

    def get_timeline(self, limit: int = None) -> Timeline:
        """获取时间线数据"""
        if not self._sorted:
            self.sort_events()

        events = self.events[:limit] if limit else self.events
        start_time, end_time = self.get_time_range()

        return Timeline(
            events=events,
            start_time=start_time,
            end_time=end_time
        )

    def get_events_by_type(self, event_type: str) -> List[TimelineEvent]:
        """按类型获取事件"""
        return [e for e in self.events if e.type == event_type]

    def to_json(self) -> str:
        """导出为JSON"""
        timeline = self.get_timeline()
        return json.dumps({
            "events": [
                {
                    "id": e.id,
                    "timestamp": e.timestamp,
                    "title": e.title,
                    "description": e.description,
                    "memory_id": e.memory_id,
                    "type": e.type,
                    "metadata": e.metadata
                }
                for e in timeline.events
            ],
            "start_time": timeline.start_time,
            "end_time": timeline.end_time
        }, ensure_ascii=False)


class DashboardVisualizer:
    """个性化仪表盘可视化器"""

    def __init__(self):
        self.widgets: Dict[str, DashboardWidget] = {}
        self.layout = "grid"
        self.theme = "light"

    def add_widget(
        self,
        widget_id: str,
        widget_type: str,
        title: str,
        data: Dict[str, Any] = None,
        position: Tuple[int, int] = (0, 0),
        size: Tuple[int, int] = (4, 3)
    ) -> DashboardWidget:
        """添加仪表盘组件"""
        widget = DashboardWidget(
            id=widget_id,
            type=widget_type,
            title=title,
            data=data or {},
            position=position,
            size=size
        )
        self.widgets[widget_id] = widget
        return widget

    def add_stat_widget(self, title: str, value: Any, position: Tuple[int, int] = (0, 0)):
        """添加统计组件"""
        return self.add_widget(
            widget_id=f"stat_{int(time.time())}",
            widget_type="statistic",
            title=title,
            data={"value": value},
            position=position,
            size=(2, 1)
        )

    def add_chart_widget(self, title: str, chart_type: str, data: List[Dict], position: Tuple[int, int] = (0, 0)):
        """添加图表组件"""
        return self.add_widget(
            widget_id=f"chart_{int(time.time())}",
            widget_type=chart_type,
            title=title,
            data={"values": data},
            position=position,
            size=(4, 3)
        )

    def get_dashboard(self) -> Dashboard:
        """获取仪表盘数据"""
        return Dashboard(
            widgets=list(self.widgets.values()),
            layout=self.layout,
            theme=self.theme
        )

    def to_json(self) -> str:
        """导出为JSON"""
        dashboard = self.get_dashboard()
        return json.dumps({
            "widgets": [
                {
                    "id": w.id,
                    "type": w.type,
                    "title": w.title,
                    "data": w.data,
                    "position": w.position,
                    "size": w.size
                }
                for w in dashboard.widgets
            ],
            "layout": dashboard.layout,
            "theme": dashboard.theme
        }, ensure_ascii=False)


class InteractiveExplorer:
    """交互式探索界面"""

    def __init__(self):
        self.history: List[Dict[str, Any]] = []
        self.current_view: Optional[Dict[str, Any]] = None

    def navigate_to(self, node_id: str, view_type: str = "details"):
        """导航到特定节点"""
        self.history.append({
            "action": "navigate",
            "node_id": node_id,
            "timestamp": time.time()
        })
        self.current_view = {"type": view_type, "node_id": node_id}

    def search_connections(self, query: str) -> List[Dict[str, Any]]:
        """搜索连接"""
        results = []
        # 简单搜索实现
        self.history.append({
            "action": "search",
            "query": query,
            "timestamp": time.time()
        })
        return results

    def filter_by_type(self, node_type: NodeType) -> List[str]:
        """按类型过滤"""
        self.history.append({
            "action": "filter",
            "type": node_type.value,
            "timestamp": time.time()
        })
        return []

    def go_back(self) -> bool:
        """返回上一步"""
        if len(self.history) > 1:
            self.history.pop()
            return True
        return False

    def get_history(self) -> List[Dict[str, Any]]:
        """获取操作历史"""
        return self.history


class MemoryVisualizationSystem:
    """记忆可视化综合系统"""

    def __init__(self):
        self.network = NetworkGraphVisualizer()
        self.timeline = TimelineVisualizer()
        self.dashboard = DashboardVisualizer()
        self.explorer = InteractiveExplorer()

    def add_memory_with_relations(
        self,
        memory_id: str,
        content: str,
        relations: List[Dict[str, Any]] = None,
        tags: List[str] = None
    ):
        """添加记忆及其关联"""
        # 添加记忆节点
        label = content[:50] + "..." if len(content) > 50 else content
        self.network.add_node(memory_id, label, NodeType.MEMORY, {"content": content})

        # 添加标签节点
        if tags:
            for tag in tags:
                tag_id = f"tag_{tag}"
                if tag_id not in self.network.nodes:
                    self.network.add_node(tag_id, tag, NodeType.TAG, {"is_tag": True})
                self.network.add_edge(memory_id, tag_id, EdgeType.RELATION, 0.5)

        # 添加关系
        if relations:
            for rel in relations:
                target_id = rel.get("target_id")
                rel_type = rel.get("type", "related")
                weight = rel.get("weight", 1.0)
                self.network.add_edge(memory_id, target_id, EdgeType.RELATION, weight, rel_type)

        # 添加到时间线
        self.timeline.add_event(
            title=label,
            description=content,
            memory_id=memory_id
        )

    def generate_personalized_dashboard(
        self,
        user_stats: Dict[str, Any]
    ) -> Dashboard:
        """生成个性化仪表盘"""
        # 清空现有组件
        self.dashboard.widgets.clear()

        # 添加统计组件
        row, col = 0, 0
        stat_items = [
            ("总记忆数", user_stats.get("total_memories", 0)),
            ("今日添加", user_stats.get("today_added", 0)),
            ("本周回顾", user_stats.get("weekly_review", 0)),
            ("收藏数", user_stats.get("favorites", 0))
        ]

        for title, value in stat_items:
            self.dashboard.add_stat_widget(title, value, position=(col, row))
            col += 2
            if col >= 4:
                col = 0
                row += 1

        # 添加图表
        if "activity" in user_stats:
            self.dashboard.add_chart_widget(
                "活动趋势",
                "line_chart",
                user_stats["activity"],
                position=(0, row + 1)
            )

        if "categories" in user_stats:
            self.dashboard.add_chart_widget(
                "分类分布",
                "bar_chart",
                user_stats["categories"],
                position=(4, row + 1)
            )

        return self.dashboard.get_dashboard()

    def export_all(self) -> Dict[str, str]:
        """导出所有可视化数据"""
        return {
            "network": self.network.to_json(),
            "timeline": self.timeline.to_json(),
            "dashboard": self.dashboard.to_json()
        }


# 全局单例
_global_visualization: Optional[MemoryVisualizationSystem] = None


def get_visualization_system() -> MemoryVisualizationSystem:
    """获取可视化系统单例"""
    global _global_visualization
    if _global_visualization is None:
        _global_visualization = MemoryVisualizationSystem()
    return _global_visualization
