"""
记忆全文搜索功能模块
基于第一性原理：确定性、简洁性、可扩展性
"""

import re
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict


class MemorySearch:
    """
    记忆搜索器
    提供全文搜索、关键词匹配等功能
    """

    def __init__(self):
        # 索引：关键词 -> 记忆ID列表
        self._keyword_index: Dict[str, List[str]] = defaultdict(list)
        # 记忆ID -> 内容
        self._memory_content: Dict[str, str] = {}

    def index_memory(self, memory_id: str, content: str) -> bool:
        """
        为记忆建立索引

        Args:
            memory_id: 记忆ID
            content: 记忆内容

        Returns:
            是否成功索引
        """
        if not memory_id or not content:
            return False

        # 保存记忆内容
        self._memory_content[memory_id] = content

        # 简单分词（按空白和标点分割）
        words = self._tokenize(content)

        # 建立反向索引
        for word in words:
            # 避免重复索引
            if memory_id not in self._keyword_index[word]:
                self._keyword_index[word].append(memory_id)

        return True

    def remove_from_index(self, memory_id: str) -> bool:
        """
        从索引中移除记忆

        Args:
            memory_id: 记忆ID

        Returns:
            是否成功移除
        """
        if memory_id not in self._memory_content:
            return False

        # 从所有关键词索引中移除
        for word in list(self._keyword_index.keys()):
            if memory_id in self._keyword_index[word]:
                self._keyword_index[word].remove(memory_id)
                # 如果关键词没有记忆了，删除该索引
                if not self._keyword_index[word]:
                    del self._keyword_index[word]

        # 删除内容缓存
        del self._memory_content[memory_id]

        return True

    def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        搜索记忆

        Args:
            query: 搜索查询
            limit: 返回结果数量限制

        Returns:
            搜索结果列表，每个结果包含记忆ID、内容、匹配分数
        """
        if not query:
            return []

        query_words = self._tokenize(query)
        if not query_words:
            return []

        # 计算每个记忆的匹配分数
        scores: Dict[str, float] = defaultdict(float)

        # 对于每个查询词，找到匹配的记忆
        for word in query_words:
            # 精确匹配
            if word in self._keyword_index:
                for memory_id in self._keyword_index[word]:
                    scores[memory_id] += 1.0

            # 模糊匹配（子串包含）
            for keyword in self._keyword_index:
                if word in keyword or keyword in word:
                    for memory_id in self._keyword_index[keyword]:
                        scores[memory_id] += 0.5

        # 正则表达式匹配（额外加分）
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        for memory_id, content in self._memory_content.items():
            if pattern.search(content):
                scores[memory_id] += 2.0

        # 按分数排序
        sorted_results = sorted(
            scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # 格式化结果
        results = []
        for memory_id, score in sorted_results[:limit]:
            if score > 0:
                results.append({
                    "memory_id": memory_id,
                    "content": self._memory_content.get(memory_id, ""),
                    "score": score
                })

        return results

    def search_by_keywords(
        self,
        keywords: List[str],
        match_all: bool = True,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        按关键词列表搜索

        Args:
            keywords: 关键词列表
            match_all: 是否需要匹配所有关键词
            limit: 返回结果数量限制

        Returns:
            搜索结果列表
        """
        if not keywords:
            return []

        # 统一转为小写
        keywords = [word.lower() for word in keywords]

        if match_all:
            # 需要匹配所有关键词
            if len(keywords) == 0:
                return []

            # 取第一个关键词的结果作为基础
            base_word = keywords[0]
            if base_word not in self._keyword_index:
                return []
            candidates = set(self._keyword_index[base_word])

            # 与其他关键词的结果取交集
            for word in keywords[1:]:
                if word not in self._keyword_index:
                    return []
                candidates = candidates & set(self._keyword_index[word])

            # 计算分数
            results = []
            for memory_id in candidates:
                results.append({
                    "memory_id": memory_id,
                    "content": self._memory_content.get(memory_id, ""),
                    "score": float(len(keywords))
                })

            return results[:limit]
        else:
            # 匹配任意关键词，与search类似
            scores: Dict[str, float] = defaultdict(float)
            for word in keywords:
                if word in self._keyword_index:
                    for memory_id in self._keyword_index[word]:
                        scores[memory_id] += 1.0

            sorted_results = sorted(
                scores.items(),
                key=lambda x: x[1],
                reverse=True
            )

            results = []
            for memory_id, score in sorted_results[:limit]:
                results.append({
                    "memory_id": memory_id,
                    "content": self._memory_content.get(memory_id, ""),
                    "score": score
                })

            return results

    def get_all_indexed_memory_ids(self) -> List[str]:
        """获取所有已索引的记忆ID"""
        return list(self._memory_content.keys())

    def get_statistics(self) -> Dict[str, Any]:
        """获取索引统计信息"""
        return {
            "total_memories": len(self._memory_content),
            "total_keywords": len(self._keyword_index),
            "top_keywords": sorted(
                self._keyword_index.items(),
                key=lambda x: len(x[1]),
                reverse=True
            )[:10]
        }

    def clear_index(self) -> int:
        """清空所有索引"""
        count = len(self._memory_content)
        self._keyword_index.clear()
        self._memory_content.clear()
        return count

    def _tokenize(self, text: str) -> List[str]:
        """
        简单分词函数 - 支持中英文混合文本

        Args:
            text: 要分词的文本

        Returns:
            分词结果列表
        """
        # 转为小写
        text = text.lower()

        # 处理中英文混合文本
        # 先分割中文字符和英文字符/数字
        # 找到所有由中文字符、英文字符、数字组成的部分
        pattern = r'[a-zA-Z0-9]+|[\u4e00-\u9fff]+'
        words = re.findall(pattern, text)

        # 然后将每个连续的中文字符拆分成单个字（简单的中文分词方式）
        result = []
        for word in words:
            # 如果是英文字符或数字，保持原样
            if re.match(r'[a-zA-Z0-9]+', word):
                result.append(word)
            else:
                # 中文字符，拆成单个字
                for char in word:
                    result.append(char)

        # 同时添加整个词（这样可以同时支持整词匹配和单字匹配）
        # 这样既能搜索"python"，也能搜索"编程"
        for word in words:
            if word not in result:
                result.append(word)

        return result


class EnhancedMemorySearch:
    """
    增强的记忆搜索系统
    与记忆系统集成的搜索功能
    """

    def __init__(self, memory_system):
        self.memory_system = memory_system
        self.searcher = MemorySearch()
        self._initialize_index()

    def _initialize_index(self):
        """
        初始化索引
        遍历现有的记忆并建立索引
        """
        # 尝试从L2记忆系统读取所有记忆
        if hasattr(self.memory_system, 'l2') and hasattr(self.memory_system.l2, 'get_all'):
            all_memories = self.memory_system.l2.get_all()
            for mem in all_memories:
                memory_id = mem.get('id')
                content = mem.get('text', '')
                if memory_id and content:
                    self.searcher.index_memory(memory_id, content)

    def add_memory_and_index(
        self,
        text: str,
        task_id: str = "default",
        memory_level: Optional[str] = None
    ) -> str:
        """
        添加记忆并索引

        Args:
            text: 记忆内容
            task_id: 任务ID
            memory_level: 记忆层级

        Returns:
            记忆ID
        """
        memory_id = self.memory_system.add(text, task_id, memory_level)
        if memory_id and text:
            self.searcher.index_memory(memory_id, text)
        return memory_id

    def search_memories(
        self,
        query: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """搜索记忆"""
        return self.searcher.search(query, limit)

    def search_by_keywords(
        self,
        keywords: List[str],
        match_all: bool = True,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """按关键词搜索"""
        return self.searcher.search_by_keywords(keywords, match_all, limit)

    def get_search_statistics(self) -> Dict[str, Any]:
        """获取搜索统计"""
        return self.searcher.get_statistics()
