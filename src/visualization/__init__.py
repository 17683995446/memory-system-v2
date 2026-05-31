"""
记忆可视化/展示功能模块
基于第一性原理：确定性、简洁性、可扩展性
"""

import time
import re
from typing import Dict, List, Optional, Any
from collections import defaultdict


class MemoryDisplay:
    """记忆展示类"""

    @staticmethod
    def format_content(content: str, format_type: str = "text") -> str:
        """格式化记忆内容"""
        if format_type == "text":
            return MemoryDisplay._format_text(content)
        elif format_type == "markdown":
            return MemoryDisplay._format_markdown(content)
        elif format_type == "html":
            return MemoryDisplay._format_html(content)
        elif format_type == "pretty":
            return MemoryDisplay._format_pretty(content)
        else:
            return content

    @staticmethod
    def _format_text(content: str) -> str:
        """纯文本格式化"""
        if not content:
            return ""
        # 基础清理
        content = content.strip()
        # 统一换行
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        return content

    @staticmethod
    def _format_markdown(content: str) -> str:
        """Markdown格式化"""
        if not content:
            return ""
        # 标题转换
        lines = content.split('\n')
        formatted = []
        for line in lines:
            line = line.strip()
            if not line:
                formatted.append('')
                continue
            # 识别并格式化标题
            if len(line) < 50 and (':' not in line or line.endswith(':')) and len(line.split()) < 10:
                if not formatted or (formatted and formatted[-1].strip() == ''):
                    formatted.append(f"## {line}")
                    continue
            # 列表处理
            if line.startswith('- ') or line.startswith('* ') or line.startswith('• '):
                formatted.append(line)
            else:
                formatted.append(line)
        return '\n'.join(formatted)

    @staticmethod
    def _format_html(content: str) -> str:
        """HTML格式化"""
        if not content:
            return ""
        # 转义特殊字符
        import html
        escaped = html.escape(content)
        # 分段
        paragraphs = escaped.split('\n\n')
        html_parts = []
        for para in paragraphs:
            if para.strip():
                html_parts.append(f"<p>{para}</p>")
        return '\n'.join(html_parts)

    @staticmethod
    def _format_pretty(content: str) -> str:
        """美观格式化"""
        if not content:
            return ""
        # 清理
        content = content.strip()
        # 统一换行
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        # 添加行首空格，便于阅读
        lines = content.split('\n')
        pretty_lines = []
        for line in lines:
            if not line:
                pretty_lines.append('')
            else:
                # 根据内容类型调整
                if line.startswith('#') or line.startswith('##') or line.startswith('###'):
                    pretty_lines.append(f"\n{line}\n")
                else:
                    pretty_lines.append(line)
        return '\n'.join(pretty_lines)

    @staticmethod
    def highlight_keywords(content: str, keywords: List[str]) -> str:
        """高亮关键词"""
        if not content or not keywords:
            return content
        for keyword in keywords:
            if keyword:
                # 使用正则替换，忽略大小写
                pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                content = pattern.sub(f"**{keyword}**", content)
        return content


class MemoryCard:
    """记忆卡片展示类"""

    @staticmethod
    def create_card(
        memory_id: str,
        content: str,
        memory_level: str = "L2",
        created_at: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """创建记忆卡片"""
        if created_at is None:
            created_at = time.time()
        return {
            "memory_id": memory_id,
            "content": content,
            "content_preview": MemoryCard._generate_preview(content),
            "memory_level": memory_level,
            "created_at": created_at,
            "created_at_str": MemoryCard._format_time(created_at),
            "metadata": metadata or {}
        }

    @staticmethod
    def _generate_preview(content: str, max_length: int = 150) -> str:
        """生成内容预览"""
        if not content:
            return ""
        content = content.strip()
        if len(content) <= max_length:
            return content
        # 找到最近的空格截断
        preview = content[:max_length]
        last_space = preview.rfind(' ')
        if last_space > 0:
            preview = preview[:last_space]
        return preview + "..."

    @staticmethod
    def _format_time(timestamp: float) -> str:
        """格式化时间"""
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))

    @staticmethod
    def render_cards(cards: List[Dict[str, Any]], display_format: str = "compact") -> str:
        """渲染多个卡片"""
        if not cards:
            return ""
        if display_format == "compact":
            return MemoryCard._render_compact(cards)
        elif display_format == "detailed":
            return MemoryCard._render_detailed(cards)
        elif display_format == "grid":
            return MemoryCard._render_grid(cards)
        else:
            return MemoryCard._render_compact(cards)

    @staticmethod
    def _render_compact(cards: List[Dict[str, Any]]) -> str:
        """紧凑格式渲染"""
        output = []
        for idx, card in enumerate(cards):
            output.append(f"#{idx + 1} [{card['memory_level']}] {card['memory_id']}")
            output.append(f"   {card['content_preview']}")
            output.append(f"   ({card['created_at_str']})")
            output.append("")
        return '\n'.join(output)

    @staticmethod
    def _render_detailed(cards: List[Dict[str, Any]]) -> str:
        """详细格式渲染"""
        output = []
        for idx, card in enumerate(cards):
            output.append(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            output.append(f"#{idx + 1} 记忆ID: {card['memory_id']}")
            output.append(f"层级: {card['memory_level']}")
            output.append(f"创建时间: {card['created_at_str']}")
            output.append("──────────────────────────────────────────────")
            output.append(card['content'])
            output.append("")
        return '\n'.join(output)

    @staticmethod
    def _render_grid(cards: List[Dict[str, Any]]) -> str:
        """网格格式渲染"""
        output = []
        cols = 3
        for i in range(0, len(cards), cols):
            row = cards[i:i+cols]
            row_str = []
            for card in row:
                preview = card['content_preview'][:30].ljust(30)
                row_str.append(f"[{card['memory_level']}] {preview}")
            output.append('  |  '.join(row_str))
        return '\n'.join(output)


class MemoryNavigator:
    """记忆导航类"""

    def __init__(self, memories: List[Dict[str, Any]]):
        self.memories = memories
        self.current_index = 0
        self.filters = {}
        self.sorts = []

    def filter_by_level(self, level: str):
        """按层级过滤"""
        self.filters['level'] = level

    def filter_by_date_range(self, start_date: float, end_date: float):
        """按日期范围过滤"""
        self.filters['date_range'] = (start_date, end_date)

    def sort_by_date(self, ascending: bool = True):
        """按日期排序"""
        self.sorts.append(('date', ascending))

    def apply_filters(self) -> List[Dict[str, Any]]:
        """应用过滤器"""
        filtered = self.memories.copy()
        # 层级过滤
        if 'level' in self.filters:
            filtered = [
                m for m in filtered
                if m.get('memory_level') == self.filters['level']
            ]
        # 日期范围过滤
        if 'date_range' in self.filters:
            start, end = self.filters['date_range']
            filtered = [
                m for m in filtered
                if start <= m.get('created_at', 0) <= end
            ]
        # 排序
        for sort_type, ascending in self.sorts:
            if sort_type == 'date':
                filtered.sort(
                    key=lambda x: x.get('created_at', 0),
                    reverse=not ascending
                )
        return filtered

    def get_current(self) -> Optional[Dict[str, Any]]:
        """获取当前记忆"""
        filtered = self.apply_filters()
        if not filtered:
            return None
        return filtered[self.current_index % len(filtered)]

    def next(self) -> Optional[Dict[str, Any]]:
        """下一个记忆"""
        self.current_index += 1
        return self.get_current()

    def previous(self) -> Optional[Dict[str, Any]]:
        """上一个记忆"""
        self.current_index -= 1
        return self.get_current()

    def go_to(self, index: int):
        """跳转到指定索引"""
        self.current_index = index

    def reset(self):
        """重置导航"""
        self.current_index = 0
        self.filters = {}
        self.sorts = []


class EnhancedMemoryWithVisualization:
    """
    增强的记忆系统（带可视化功能）
    装饰器模式实现
    """

    def __init__(self, memory_system):
        self.memory_system = memory_system
        self.navigator = None

    def _ensure_navigator(self):
        """确保导航器已创建"""
        if self.navigator is None:
            # 收集记忆
            memories = []
            # 获取 L1 记忆
            if hasattr(self.memory_system, 'l1') and hasattr(self.memory_system.l1, 'get_all'):
                l1_memories = self.memory_system.l1.get_all()
                memories.extend([
                    {
                        'memory_id': f"L1-{i}",
                        'content': getattr(m, 'text', ''),
                        'memory_level': 'L1',
                        'created_at': time.time()
                    } for i, m in enumerate(l1_memories)
                ])
            # 获取 L2 记忆
            if hasattr(self.memory_system, 'l2') and hasattr(self.memory_system.l2, 'get_all'):
                l2_memories = self.memory_system.l2.get_all()
                memories.extend([
                    {
                        'memory_id': f"L2-{i}",
                        'content': getattr(m, 'text', ''),
                        'memory_level': 'L2',
                        'created_at': time.time()
                    } for i, m in enumerate(l2_memories)
                ])
            # 获取 L3 记忆
            if hasattr(self.memory_system, 'l3') and hasattr(self.memory_system.l3, 'get_all'):
                l3_memories = self.memory_system.l3.get_all()
                memories.extend([
                    {
                        'memory_id': f"L3-{i}",
                        'content': getattr(m, 'text', ''),
                        'memory_level': 'L3',
                        'created_at': time.time()
                    } for i, m in enumerate(l3_memories)
                ])
            self.navigator = MemoryNavigator(memories)

    def display_memory(self, memory_id: str, format_type: str = "pretty") -> str:
        """展示单个记忆"""
        # 尝试从各层级获取
        content = ""
        level = ""
        # 这里简化处理，实际应该根据 ID 查找
        if hasattr(self.memory_system, 'l2') and hasattr(self.memory_system.l2, 'get_all'):
            l2_memories = self.memory_system.l2.get_all()
            for m in l2_memories:
                if hasattr(m, 'text'):
                    content = getattr(m, 'text')
                    level = "L2"
                    break
        # 格式化
        if content:
            return MemoryDisplay.format_content(content, format_type)
        return ""

    def display_all_memories(self, display_format: str = "compact") -> str:
        """展示所有记忆"""
        self._ensure_navigator()
        cards = []
        filtered = self.navigator.apply_filters()
        for mem in filtered:
            card = MemoryCard.create_card(
                mem['memory_id'],
                mem['content'],
                mem['memory_level'],
                mem['created_at']
            )
            cards.append(card)
        return MemoryCard.render_cards(cards, display_format)

    def highlight_memory_content(self, memory_id: str, keywords: List[str]) -> str:
        """高亮关键词展示记忆"""
        content = self.display_memory(memory_id)
        if content:
            return MemoryDisplay.highlight_keywords(content, keywords)
        return ""

    def create_navigator(self) -> MemoryNavigator:
        """创建导航器"""
        self._ensure_navigator()
        return self.navigator

    def browse_memories(self):
        """浏览记忆"""
        self._ensure_navigator()
        current = self.navigator.get_current()
        if current:
            # 创建完整的卡片对象
            card = MemoryCard.create_card(
                current['memory_id'],
                current['content'],
                current['memory_level'],
                current.get('created_at')
            )
            return MemoryCard.render_cards([card], 'detailed')
        return ""

    def next_memory(self) -> str:
        """下一个记忆"""
        self._ensure_navigator()
        self.navigator.next()
        return self.browse_memories()

    def previous_memory(self) -> str:
        """上一个记忆"""
        self._ensure_navigator()
        self.navigator.previous()
        return self.browse_memories()
