"""
记忆摘要与总结系统
基于第一性原理：简洁性、准确性、可配置性
"""
import time
import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, Counter
from datetime import datetime

logger = logging.getLogger(__name__)


class SummaryLevel(Enum):
    """摘要级别"""
    BRIEF = "brief"  # 简短摘要
    NORMAL = "normal"  # 标准摘要
    DETAILED = "detailed"  # 详细摘要


class SummaryType(Enum):
    """摘要类型"""
    RECENT = "recent"  # 最近内容摘要
    TOPIC = "topic"  # 按主题摘要
    IMPORTANT = "important"  # 重要内容摘要
    COMPREHENSIVE = "comprehensive"  # 综合摘要


@dataclass
class SummaryResult:
    """摘要结果"""
    summary_id: str
    summary_type: SummaryType
    summary_level: SummaryLevel
    content: str
    key_points: List[str]
    word_count: int
    memory_count: int
    generated_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


class TextAnalyzer:
    """文本分析器"""

    @staticmethod
    def extract_keywords(text: str, max_count: int = 10) -> List[str]:
        """提取关键词"""
        # 简单实现：基于词频统计（实际项目可使用更复杂的NLP方法）
        words = re.findall(r'[\w\u4e00-\u9fff]+', text.lower())
        # 过滤停用词
        stop_words = set([
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at',
            'to', 'for', 'of', 'is', 'are', 'was', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does',
            'did', 'will', 'would', 'could', 'should', 'may', 'might',
            'must', 'shall', 'can', 'need', 'dare', 'ought', 'used',
            '的', '了', '和', '是', '就', '都', '而', '及', '与',
            '着', '或', '但', '去', '来', '很', '也', '不', '这',
            '那', '有', '我', '你', '他', '她', '它', '我们', '你们',
            '他们', '它们', '什么', '怎么', '为什么', '哪', '哪里'
        ])
        filtered_words = [w for w in words if w not in stop_words and len(w) > 1]
        word_counts = Counter(filtered_words)
        return [word for word, _ in word_counts.most_common(max_count)]

    @staticmethod
    def split_into_sentences(text: str) -> List[str]:
        """分句"""
        # 简单的分句实现
        sentences = re.split(r'[。！？.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]

    @staticmethod
    def calculate_importance(sentence: str) -> float:
        """计算句子重要性（简单实现）"""
        score = 0.0
        # 长度因素
        length = len(sentence)
        if length > 50:
            score += 0.3
        # 关键词因素
        keywords = ['重要', '关键', '必须', '应该', '需要', '记得', '注意',
                   'important', 'key', 'critical', 'essential', 'must', 'should']
        for kw in keywords:
            if kw in sentence.lower():
                score += 0.2
        # 数字因素
        if any(char.isdigit() for char in sentence):
            score += 0.1
        return min(score, 1.0)


class MemorySummarizer:
    """记忆摘要器"""

    def __init__(self, memory_system=None):
        self.memory_system = memory_system
        self.analyzer = TextAnalyzer()
        self._cache: Dict[str, SummaryResult] = {}

    def summarize_memories(
        self,
        memories: List[Dict[str, Any]],
        summary_type: SummaryType = SummaryType.COMPREHENSIVE,
        summary_level: SummaryLevel = SummaryLevel.NORMAL,
        max_sentences: Optional[int] = None
    ) -> SummaryResult:
        """生成记忆摘要"""
        if not memories:
            return SummaryResult(
                summary_id=self._generate_id(),
                summary_type=summary_type,
                summary_level=summary_level,
                content="暂无记忆内容",
                key_points=[],
                word_count=0,
                memory_count=0
            )

        # 根据摘要级别确定最大句子数
        if max_sentences is None:
            level_map = {
                SummaryLevel.BRIEF: 3,
                SummaryLevel.NORMAL: 5,
                SummaryLevel.DETAILED: 10
            }
            max_sentences = level_map.get(summary_level, 5)

        # 收集所有文本
        all_text = self._collect_memory_text(memories)

        # 提取关键词
        keywords = self.analyzer.extract_keywords(all_text, max_count=8)

        # 分句并排序
        sentences = self.analyzer.split_into_sentences(all_text)
        if not sentences:
            return self._create_empty_summary(summary_type, summary_level, len(memories))

        # 选择最重要的句子
        scored_sentences = [
            (self.analyzer.calculate_importance(s), s)
            for s in sentences
        ]
        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        selected_sentences = [s for _, s in scored_sentences[:max_sentences]]

        # 生成摘要内容
        content = self._build_summary_content(selected_sentences, summary_level)

        # 提取要点
        key_points = self._extract_key_points(selected_sentences, keywords)

        # 创建结果
        result = SummaryResult(
            summary_id=self._generate_id(),
            summary_type=summary_type,
            summary_level=summary_level,
            content=content,
            key_points=key_points,
            word_count=len(content),
            memory_count=len(memories),
            metadata={
                "keywords": keywords,
                "total_sentences": len(sentences)
            }
        )

        return result

    def summarize_by_level(
        self,
        level: str = "l1",
        limit: Optional[int] = None,
        summary_level: SummaryLevel = SummaryLevel.NORMAL
    ) -> Optional[SummaryResult]:
        """按记忆层级生成摘要"""
        if not self.memory_system:
            return None

        memories = self._get_memories_by_level(level, limit)
        return self.summarize_memories(
            memories,
            summary_type=SummaryType.COMPREHENSIVE,
            summary_level=summary_level
        )

    def summarize_by_session(
        self,
        session_id: str,
        summary_level: SummaryLevel = SummaryLevel.NORMAL
    ) -> Optional[SummaryResult]:
        """按会话生成摘要"""
        if not self.memory_system:
            return None

        memories = self._get_memories_by_session(session_id)
        return self.summarize_memories(
            memories,
            summary_type=SummaryType.RECENT,
            summary_level=summary_level
        )

    def summarize_topic(
        self,
        topic_keyword: str,
        summary_level: SummaryLevel = SummaryLevel.NORMAL
    ) -> Optional[SummaryResult]:
        """按主题生成摘要"""
        if not self.memory_system:
            return None

        memories = self._search_memories_by_keyword(topic_keyword)
        return self.summarize_memories(
            memories,
            summary_type=SummaryType.TOPIC,
            summary_level=summary_level
        )

    def generate_weekly_summary(
        self,
        summary_level: SummaryLevel = SummaryLevel.NORMAL
    ) -> Optional[SummaryResult]:
        """生成周摘要"""
        if not self.memory_system:
            return None

        memories = self._get_recent_memories(days=7)
        result = self.summarize_memories(
            memories,
            summary_type=SummaryType.RECENT,
            summary_level=summary_level
        )
        result.metadata["period"] = "weekly"
        return result

    def _collect_memory_text(self, memories: List[Dict[str, Any]]) -> str:
        """收集记忆文本"""
        texts = []
        for mem in memories:
            if isinstance(mem, dict):
                if 'text' in mem:
                    texts.append(str(mem['text']))
                elif 'content' in mem:
                    texts.append(str(mem['content']))
                elif 'value' in mem:
                    texts.append(str(mem['value']))
            elif isinstance(mem, str):
                texts.append(mem)
        return "\n".join(texts)

    def _build_summary_content(self, sentences: List[str], level: SummaryLevel) -> str:
        """构建摘要内容"""
        if level == SummaryLevel.BRIEF:
            if sentences:
                return sentences[0]
            return ""
        elif level == SummaryLevel.NORMAL:
            return " ".join(sentences)
        else:  # DETAILED
            return "\n".join(f"- {s}" for s in sentences)

    def _extract_key_points(self, sentences: List[str], keywords: List[str]) -> List[str]:
        """提取要点"""
        key_points = []
        # 添加包含关键词的句子
        for sentence in sentences:
            if any(kw in sentence.lower() for kw in keywords):
                if sentence not in key_points:
                    key_points.append(sentence)
        # 如果不够，添加剩余的句子
        for sentence in sentences:
            if sentence not in key_points:
                key_points.append(sentence)
        return key_points[:5]  # 最多5个要点

    def _get_memories_by_level(self, level: str, limit: Optional[int]) -> List[Dict[str, Any]]:
        """获取指定层级的记忆"""
        memories = []
        try:
            if level == "l1" and hasattr(self.memory_system, 'l1'):
                memories = self.memory_system.l1.get_all()
            elif level == "l2" and hasattr(self.memory_system, 'l2'):
                memories = self.memory_system.l2.get_all()
            elif level == "l3" and hasattr(self.memory_system, 'l3'):
                memories = self.memory_system.l3.get_all()
        except Exception as e:
            logger.warning(f"获取记忆失败: {e}")
        if limit:
            memories = memories[:limit]
        return memories

    def _get_memories_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """获取指定会话的记忆"""
        memories = []
        try:
            if hasattr(self.memory_system, 'l1'):
                l1_memories = self.memory_system.l1.get_all()
                memories.extend([
                    m for m in l1_memories
                    if m.get('session_id') == session_id or m.get('task_id') == session_id
                ])
        except Exception as e:
            logger.warning(f"获取会话记忆失败: {e}")
        return memories

    def _search_memories_by_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索包含关键词的记忆"""
        memories = []
        try:
            if hasattr(self.memory_system, 'l1'):
                memories.extend(self.memory_system.l1.get_all())
            if hasattr(self.memory_system, 'l2'):
                memories.extend(self.memory_system.l2.get_all())
            if hasattr(self.memory_system, 'l3'):
                memories.extend(self.memory_system.l3.get_all())
        except Exception as e:
            logger.warning(f"搜索记忆失败: {e}")
        
        # 简单过滤
        keyword_lower = keyword.lower()
        filtered = []
        for mem in memories:
            text = str(mem.get('text', mem.get('content', mem.get('value', ''))))
            if keyword_lower in text.lower():
                filtered.append(mem)
        return filtered

    def _get_recent_memories(self, days: int = 7) -> List[Dict[str, Any]]:
        """获取最近的记忆"""
        # 简单实现：返回所有记忆
        memories = []
        try:
            if hasattr(self.memory_system, 'l1'):
                memories.extend(self.memory_system.l1.get_all())
            if hasattr(self.memory_system, 'l2'):
                memories.extend(self.memory_system.l2.get_all())
            if hasattr(self.memory_system, 'l3'):
                memories.extend(self.memory_system.l3.get_all())
        except Exception as e:
            logger.warning(f"获取最近记忆失败: {e}")
        return memories

    def _create_empty_summary(
        self,
        summary_type: SummaryType,
        summary_level: SummaryLevel,
        memory_count: int
    ) -> SummaryResult:
        """创建空摘要"""
        return SummaryResult(
            summary_id=self._generate_id(),
            summary_type=summary_type,
            summary_level=summary_level,
            content="没有足够的内容生成摘要",
            key_points=[],
            word_count=0,
            memory_count=memory_count
        )

    @staticmethod
    def _generate_id() -> str:
        """生成摘要ID"""
        timestamp = int(time.time() * 1000)
        return f"sum_{timestamp}"


# 全局单例
_global_summarizer: Optional[MemorySummarizer] = None


def get_summarizer(memory_system=None) -> MemorySummarizer:
    """获取摘要器单例"""
    global _global_summarizer
    if _global_summarizer is None:
        _global_summarizer = MemorySummarizer(memory_system)
    elif memory_system is not None and _global_summarizer.memory_system is None:
        _global_summarizer.memory_system = memory_system
    return _global_summarizer
