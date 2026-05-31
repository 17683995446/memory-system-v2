"""
记忆摘要模块
基于第一性原理：快速、简洁、提供有价值的概览
"""

import time
from typing import Dict, List, Any, Optional
from collections import Counter


class MemorySummarizer:
    """记忆摘要生成器"""

    @staticmethod
    def summarize_l1(l1_memory, max_items: int = 5) -> Dict[str, Any]:
        """
        生成L1记忆摘要

        Args:
            l1_memory: L1记忆对象
            max_items: 最多展示的项目数

        Returns:
            摘要字典
        """
        all_items = l1_memory.get_all()

        # 按会话分组
        sessions = {}
        for item in all_items:
            session_id = item.get('session_id', item.get('task_id', 'unknown'))
            if session_id not in sessions:
                sessions[session_id] = []
            sessions[session_id].append(item)

        # 统计信息
        total_items = len(all_items)
        total_sessions = len(sessions)

        # 最近的项目
        recent_items = []
        for item in all_items[-max_items:]:
            recent_items.append({
                'text': item.get('text', '')[:50] + ('...' if len(item.get('text', '')) > 50 else ''),
                'session': item.get('session_id', item.get('task_id', 'unknown'))
            })

        return {
            'layer': 'L1',
            'total_items': total_items,
            'total_sessions': total_sessions,
            'sessions': list(sessions.keys()),
            'recent_items': recent_items,
            'summary': f"L1记忆包含 {total_items} 条记忆，分布在 {total_sessions} 个会话中"
        }

    @staticmethod
    def summarize_l2(l2_memory, max_items: int = 5) -> Dict[str, Any]:
        """
        生成L2记忆摘要

        Args:
            l2_memory: L2记忆对象
            max_items: 最多展示的项目数

        Returns:
            摘要字典
        """
        all_items = l2_memory.get_all()
        total_items = len(all_items)

        # 统计会话分布
        session_counts = Counter()
        for item in all_items:
            metadata = item.get('metadata', {})
            session_id = metadata.get('session_id', metadata.get('task_id', 'unknown'))
            session_counts[session_id] += 1

        # 最近访问的项目
        sorted_by_access = sorted(
            all_items,
            key=lambda x: x.get('last_access', 0),
            reverse=True
        )

        hot_items = []
        for item in sorted_by_access[:max_items]:
            hot_items.append({
                'text': item.get('text', '')[:50] + ('...' if len(item.get('text', '')) > 50 else ''),
                'access_count': item.get('access_count', 0),
                'id': item.get('id', '')
            })

        # 最近添加的项目
        recent_items = []
        for item in all_items[-max_items:]:
            recent_items.append({
                'text': item.get('text', '')[:50] + ('...' if len(item.get('text', '')) > 50 else ''),
                'id': item.get('id', '')
            })

        return {
            'layer': 'L2',
            'total_items': total_items,
            'sessions': dict(session_counts),
            'hot_items': hot_items,
            'recent_items': recent_items,
            'summary': f"L2记忆包含 {total_items} 条情景记忆"
        }

    @staticmethod
    def summarize_l3(l3_memory, max_entities: int = 10) -> Dict[str, Any]:
        """
        生成L3记忆摘要

        Args:
            l3_memory: L3记忆对象
            max_entities: 最多展示的实体数

        Returns:
            摘要字典
        """
        all_facts = l3_memory.get_all()
        total_facts = len(all_facts)

        # 统计实体
        entity_counts = Counter()
        entities = {}

        for fact in all_facts:
            entity = fact.get('entity', '')
            entity_counts[entity] += 1
            if entity not in entities:
                entities[entity] = []
            entities[entity].append({
                'attribute': fact.get('attribute', ''),
                'value': fact.get('value', '')
            })

        # 主要实体
        top_entities = entity_counts.most_common(max_entities)

        # 实体摘要
        entity_summaries = []
        for entity, count in top_entities:
            facts = entities.get(entity, [])
            preview = []
            for f in facts[:3]:  # 每个实体最多展示3个属性
                preview.append(f"{f['attribute']}={f['value']}")
            entity_summaries.append({
                'entity': entity,
                'fact_count': count,
                'preview': ', '.join(preview)
            })

        return {
            'layer': 'L3',
            'total_facts': total_facts,
            'total_entities': len(entities),
            'top_entities': entity_summaries,
            'summary': f"L3记忆包含 {total_facts} 条事实，覆盖 {len(entities)} 个实体"
        }

    @staticmethod
    def summarize_all(
        memory_system,
        max_l1_items: int = 5,
        max_l2_items: int = 5,
        max_l3_entities: int = 10
    ) -> Dict[str, Any]:
        """
        生成完整的记忆系统摘要

        Args:
            memory_system: 完整记忆系统对象
            max_l1_items: L1最多展示项目数
            max_l2_items: L2最多展示项目数
            max_l3_entities: L3最多展示实体数

        Returns:
            完整摘要字典
        """
        l1_summary = None
        l2_summary = None
        l3_summary = None

        if hasattr(memory_system, 'l1'):
            l1_summary = MemorySummarizer.summarize_l1(memory_system.l1, max_l1_items)

        if hasattr(memory_system, 'l2'):
            l2_summary = MemorySummarizer.summarize_l2(memory_system.l2, max_l2_items)

        if hasattr(memory_system, 'l3'):
            l3_summary = MemorySummarizer.summarize_l3(memory_system.l3, max_l3_entities)

        # 总统计
        total_items = 0
        if l1_summary:
            total_items += l1_summary.get('total_items', 0)
        if l2_summary:
            total_items += l2_summary.get('total_items', 0)
        if l3_summary:
            total_items += l3_summary.get('total_facts', 0)

        return {
            'timestamp': time.time(),
            'total_items': total_items,
            'l1': l1_summary,
            'l2': l2_summary,
            'l3': l3_summary,
            'system_summary': f"记忆系统包含 {total_items} 条记忆（L1+L2+L3）"
        }

    @staticmethod
    def format_summary(summary: Dict[str, Any], indent: int = 0) -> str:
        """
        将摘要格式化为可读文本

        Args:
            summary: 摘要字典
            indent: 缩进空格数

        Returns:
            格式化的字符串
        """
        prefix = ' ' * indent
        lines = []

        if 'system_summary' in summary:
            lines.append(f"{prefix}{summary['system_summary']}")
            lines.append('')

        if summary.get('l1'):
            l1 = summary['l1']
            lines.append(f"{prefix}=== L1 瞬时记忆 ===")
            lines.append(f"{prefix}{l1['summary']}")
            if l1.get('recent_items'):
                lines.append(f"{prefix}最近的记忆:")
                for item in l1['recent_items']:
                    lines.append(f"{prefix}  - [{item['session']}] {item['text']}")
            lines.append('')

        if summary.get('l2'):
            l2 = summary['l2']
            lines.append(f"{prefix}=== L2 情景记忆 ===")
            lines.append(f"{prefix}{l2['summary']}")
            if l2.get('sessions'):
                sessions_str = ', '.join([f"{k}({v})" for k, v in l2['sessions'].items()])
                lines.append(f"{prefix}会话分布: {sessions_str}")
            if l2.get('recent_items'):
                lines.append(f"{prefix}最近添加:")
                for item in l2['recent_items']:
                    lines.append(f"{prefix}  - {item['text']}")
            lines.append('')

        if summary.get('l3'):
            l3 = summary['l3']
            lines.append(f"{prefix}=== L3 事实记忆 ===")
            lines.append(f"{prefix}{l3['summary']}")
            if l3.get('top_entities'):
                lines.append(f"{prefix}主要实体:")
                for ent in l3['top_entities']:
                    lines.append(f"{prefix}  - {ent['entity']}: {ent['fact_count']} 条事实 ({ent['preview']})")
            lines.append('')

        return '\n'.join(lines)
