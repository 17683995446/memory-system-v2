"""
记忆智能问答系统
基于第一性原理：确定性、简洁性、实用性
"""

import re
import json
import time
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from collections import defaultdict


class QuestionType(Enum):
    """问题类型枚举"""
    FACTUAL = "factual"  # 事实性问题
    SUMMARY = "summary"  # 总结性问题
    LIST = "list"  # 列举类问题
    TIME_RANGE = "time_range"  # 时间范围问题
    SEARCH = "search"  # 搜索类问题
    UNKNOWN = "unknown"  # 未知类型


class AnswerQuality(Enum):
    """答案质量枚举"""
    EXCELLENT = "excellent"  # 完美匹配
    GOOD = "good"  # 良好匹配
    FAIR = "fair"  # 一般匹配
    POOR = "poor"  # 较差匹配
    NO_ANSWER = "no_answer"  # 无答案


class QueryAnalyzer:
    """查询分析器"""

    def __init__(self):
        # 关键词映射
        self.question_patterns = {
            QuestionType.FACTUAL: [
                r"什么是|是什么|谁是|哪是|哪里|何时|多少|为什么|怎么",
                r"what is|who is|where is|when is|how many|why",
            ],
            QuestionType.SUMMARY: [
                r"总结|概述|概括|简介|回顾|整理一下",
                r"summarize|summary|overview|recap",
            ],
            QuestionType.LIST: [
                r"列出|列举|有哪些|什么哪些|哪些",
                r"list|what are|which are",
            ],
            QuestionType.TIME_RANGE: [
                r"最近|今天|昨天|本周|上周|本月|上月|今年|去年|.*天内|.*周内|.*月内",
                r"recent|today|yesterday|this week|last week|this month|last month",
            ],
            QuestionType.SEARCH: [
                r"找|搜索|查找|查询|看看|有没有",
                r"find|search|look for|check|is there",
            ],
        }

        # 时间关键词
        self.time_keywords = {
            "今天": 0,
            "昨天": 1,
            "前天": 2,
            "本周": 7,
            "上周": 14,
            "本月": 30,
            "上月": 60,
            "今年": 365,
            "去年": 730,
        }

    def analyze(self, question: str) -> Dict[str, Any]:
        """分析问题"""
        result = {
            "original": question,
            "question_type": QuestionType.UNKNOWN,
            "keywords": [],
            "time_range": None,
            "entities": [],
            "cleaned": self._clean_text(question),
        }

        # 识别问题类型
        for qtype, patterns in self.question_patterns.items():
            for pattern in patterns:
                if re.search(pattern, question, re.IGNORECASE):
                    result["question_type"] = qtype
                    break
            if result["question_type"] != QuestionType.UNKNOWN:
                break

        # 提取关键词
        result["keywords"] = self._extract_keywords(question)

        # 提取时间范围
        result["time_range"] = self._extract_time_range(question)

        # 提取实体（简化版）
        result["entities"] = self._extract_entities(question)

        return result

    def _clean_text(self, text: str) -> str:
        """清理文本"""
        # 移除特殊字符
        cleaned = re.sub(r'[^\w\s]', ' ', text)
        # 合并多个空格
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip()

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词（简化版）"""
        # 移除停用词（简化版）
        stopwords = {
            "的", "是", "在", "了", "和", "有", "我", "你", "他", "她", "它",
            "这", "那", "个", "些", "就", "都", "也", "还", "很", "最",
            "什么", "怎么", "如何", "哪里", "何时", "多少", "为什么",
            "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "must", "shall", "can", "need", "dare",
            "what", "when", "where", "why", "how", "which", "who", "whom", "whose",
        }
        
        cleaned_text = self._clean_text(text).lower()
        
        # 对于中文，我们采用简单的关键词提取
        keywords = []
        
        # 常见关键词
        common_keywords = ["项目", "启动", "会议", "张三", "李四", "API", "文档", "预算",
                          "开发", "负责", "前端", "后端", "测试", "bug"]
        
        for keyword in common_keywords:
            if keyword in cleaned_text:
                keywords.append(keyword)
        
        # 对于英文，按空格分割
        if any(ord(c) < 128 for c in cleaned_text):
            words = cleaned_text.split()
            for word in words:
                if word not in stopwords and len(word) > 1:
                    keywords.append(word)
        
        # 去重
        keywords = list(dict.fromkeys(keywords))
        
        # 如果没有提取到关键词，返回清理后的文本
        if not keywords:
            keywords = [cleaned_text]
        
        return keywords

    def _extract_time_range(self, text: str) -> Optional[Dict[str, Any]]:
        """提取时间范围"""
        for keyword, days in self.time_keywords.items():
            if keyword in text:
                return {
                    "keyword": keyword,
                    "days": days,
                    "start_time": time.time() - (days * 86400),
                    "end_time": time.time(),
                }
        return None

    def _extract_entities(self, text: str) -> List[str]:
        """提取实体（简化版）"""
        entities = []
        
        # 简单的实体识别：查找大写开头的词（英文）或特定模式
        # 中文实体识别简化处理
        patterns = [
            r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*',  # 英文专有名词
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            entities.extend(matches)
        
        return list(dict.fromkeys(entities))


class MemoryRetriever:
    """记忆检索器"""

    def __init__(self):
        self.min_relevance = 0.1

    def retrieve(
        self,
        question_analysis: Dict[str, Any],
        memories: List[Dict[str, Any]],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """检索相关记忆"""
        if not memories:
            return []

        # 计算相关性分数
        scored_memories = []
        for memory in memories:
            score = self._calculate_relevance(question_analysis, memory)
            if score >= self.min_relevance:
                scored_memories.append({
                    "memory": memory,
                    "score": score,
                })

        # 按分数排序
        scored_memories.sort(key=lambda x: x["score"], reverse=True)
        
        # 返回 top_k
        return scored_memories[:top_k]

    def _calculate_relevance(
        self,
        question_analysis: Dict[str, Any],
        memory: Dict[str, Any],
    ) -> float:
        """计算相关性分数"""
        score = 0.0
        keywords = question_analysis.get("keywords", [])
        memory_text = self._get_memory_text(memory).lower()

        # 关键词匹配
        if keywords:
            matched_count = sum(1 for keyword in keywords if keyword in memory_text)
            keyword_score = matched_count / len(keywords)
            score += keyword_score * 0.6

        # 时间范围过滤
        time_range = question_analysis.get("time_range")
        if time_range:
            mem_time = memory.get("timestamp", 0)
            if time_range["start_time"] <= mem_time <= time_range["end_time"]:
                score += 0.2
            else:
                score -= 0.1

        # 实体匹配
        entities = question_analysis.get("entities", [])
        if entities:
            entity_matches = sum(1 for entity in entities if entity.lower() in memory_text)
            if entity_matches > 0:
                score += 0.2

        return min(score, 1.0)

    def _get_memory_text(self, memory: Dict[str, Any]) -> str:
        """获取记忆文本"""
        if "text" in memory:
            return memory["text"]
        elif "content" in memory:
            return memory["content"]
        elif "data" in memory and isinstance(memory["data"], dict):
            return str(memory["data"])
        return str(memory)


class AnswerGenerator:
    """答案生成器"""

    def __init__(self):
        self.templates = {
            QuestionType.FACTUAL: self._generate_factual_answer,
            QuestionType.SUMMARY: self._generate_summary_answer,
            QuestionType.LIST: self._generate_list_answer,
            QuestionType.TIME_RANGE: self._generate_time_range_answer,
            QuestionType.SEARCH: self._generate_search_answer,
            QuestionType.UNKNOWN: self._generate_generic_answer,
        }

    def generate(
        self,
        question: str,
        question_analysis: Dict[str, Any],
        retrieved_memories: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """生成答案"""
        qtype = question_analysis.get("question_type", QuestionType.UNKNOWN)
        
        if not retrieved_memories:
            return {
                "answer": "抱歉，我没有找到相关的记忆来回答您的问题。",
                "quality": AnswerQuality.NO_ANSWER,
                "sources": [],
                "confidence": 0.0,
            }

        # 调用对应类型的答案生成器
        generator = self.templates.get(qtype, self._generate_generic_answer)
        result = generator(question, question_analysis, retrieved_memories)
        
        return result

    def _generate_factual_answer(
        self,
        question: str,
        question_analysis: Dict[str, Any],
        retrieved_memories: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """生成事实性答案"""
        best_memory = retrieved_memories[0]
        memory_text = self._get_memory_text(best_memory["memory"])
        
        answer = f"根据我的记忆，{memory_text}"
        
        return {
            "answer": answer,
            "quality": AnswerQuality.GOOD if best_memory["score"] > 0.6 else AnswerQuality.FAIR,
            "sources": [best_memory["memory"]],
            "confidence": best_memory["score"],
        }

    def _generate_summary_answer(
        self,
        question: str,
        question_analysis: Dict[str, Any],
        retrieved_memories: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """生成总结性答案"""
        summaries = []
        for item in retrieved_memories:
            text = self._get_memory_text(item["memory"])
            # 取前100个字符作为摘要
            summary = text[:100] + "..." if len(text) > 100 else text
            summaries.append(summary)
        
        answer = "以下是相关记忆的总结：\n\n"
        for i, summary in enumerate(summaries, 1):
            answer += f"{i}. {summary}\n"
        
        return {
            "answer": answer,
            "quality": AnswerQuality.GOOD,
            "sources": [item["memory"] for item in retrieved_memories],
            "confidence": sum(item["score"] for item in retrieved_memories) / len(retrieved_memories),
        }

    def _generate_list_answer(
        self,
        question: str,
        question_analysis: Dict[str, Any],
        retrieved_memories: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """生成列表式答案"""
        items = []
        for item in retrieved_memories:
            text = self._get_memory_text(item["memory"])
            items.append(text)
        
        answer = f"找到了 {len(items)} 条相关记忆：\n\n"
        for i, item_text in enumerate(items, 1):
            answer += f"{i}. {item_text}\n"
        
        return {
            "answer": answer,
            "quality": AnswerQuality.GOOD,
            "sources": [item["memory"] for item in retrieved_memories],
            "confidence": sum(item["score"] for item in retrieved_memories) / len(retrieved_memories),
        }

    def _generate_time_range_answer(
        self,
        question: str,
        question_analysis: Dict[str, Any],
        retrieved_memories: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """生成时间范围答案"""
        time_range = question_analysis.get("time_range", {})
        keyword = time_range.get("keyword", "指定时间范围")
        
        answer = f"在{keyword}的记忆中，找到了以下内容：\n\n"
        for i, item in enumerate(retrieved_memories, 1):
            text = self._get_memory_text(item["memory"])
            timestamp = item["memory"].get("timestamp", time.time())
            time_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(timestamp))
            answer += f"{i}. [{time_str}] {text}\n"
        
        return {
            "answer": answer,
            "quality": AnswerQuality.GOOD,
            "sources": [item["memory"] for item in retrieved_memories],
            "confidence": sum(item["score"] for item in retrieved_memories) / len(retrieved_memories),
        }

    def _generate_search_answer(
        self,
        question: str,
        question_analysis: Dict[str, Any],
        retrieved_memories: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """生成搜索答案"""
        answer = f"为您找到了 {len(retrieved_memories)} 条相关记忆：\n\n"
        for i, item in enumerate(retrieved_memories, 1):
            text = self._get_memory_text(item["memory"])
            score = item["score"]
            answer += f"{i}. (相关度: {score:.2f}) {text}\n"
        
        return {
            "answer": answer,
            "quality": AnswerQuality.GOOD,
            "sources": [item["memory"] for item in retrieved_memories],
            "confidence": sum(item["score"] for item in retrieved_memories) / len(retrieved_memories),
        }

    def _generate_generic_answer(
        self,
        question: str,
        question_analysis: Dict[str, Any],
        retrieved_memories: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """生成通用答案"""
        answer = "以下是一些可能相关的记忆：\n\n"
        for i, item in enumerate(retrieved_memories, 1):
            text = self._get_memory_text(item["memory"])
            answer += f"{i}. {text}\n"
        
        return {
            "answer": answer,
            "quality": AnswerQuality.FAIR,
            "sources": [item["memory"] for item in retrieved_memories],
            "confidence": sum(item["score"] for item in retrieved_memories) / len(retrieved_memories),
        }

    def _get_memory_text(self, memory: Dict[str, Any]) -> str:
        """获取记忆文本"""
        if "text" in memory:
            return memory["text"]
        elif "content" in memory:
            return memory["content"]
        return str(memory)


class ConversationManager:
    """对话管理器"""

    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.history: List[Dict[str, Any]] = []
        self.conversations: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    def add_interaction(
        self,
        question: str,
        answer: Dict[str, Any],
        conversation_id: Optional[str] = None,
    ) -> str:
        """添加交互记录"""
        if conversation_id is None:
            conversation_id = self._generate_conversation_id()

        interaction = {
            "timestamp": time.time(),
            "question": question,
            "answer": answer,
        }

        self.history.append(interaction)
        self.conversations[conversation_id].append(interaction)

        # 限制历史长度
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

        if len(self.conversations[conversation_id]) > self.max_history:
            self.conversations[conversation_id] = self.conversations[conversation_id][-self.max_history:]

        return conversation_id

    def get_history(self, conversation_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取对话历史"""
        if conversation_id:
            return self.conversations.get(conversation_id, [])
        return self.history

    def clear_history(self, conversation_id: Optional[str] = None):
        """清除历史"""
        if conversation_id:
            if conversation_id in self.conversations:
                del self.conversations[conversation_id]
        else:
            self.history.clear()

    def _generate_conversation_id(self) -> str:
        """生成对话ID"""
        timestamp = str(time.time()).encode()
        return hashlib.md5(timestamp).hexdigest()[:12]


class MemoryQASystem:
    """记忆问答系统"""

    def __init__(self):
        self.analyzer = QueryAnalyzer()
        self.retriever = MemoryRetriever()
        self.generator = AnswerGenerator()
        self.conversation = ConversationManager()

    def ask(
        self,
        question: str,
        memories: List[Dict[str, Any]],
        conversation_id: Optional[str] = None,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """提问并获取答案"""
        # 分析问题
        analysis = self.analyzer.analyze(question)
        
        # 检索记忆
        retrieved = self.retriever.retrieve(analysis, memories, top_k)
        
        # 生成答案
        answer = self.generator.generate(question, analysis, retrieved)
        
        # 记录交互
        new_conversation_id = self.conversation.add_interaction(
            question, answer, conversation_id
        )
        
        return {
            "question": question,
            "analysis": analysis,
            "answer": answer,
            "retrieved_memories": retrieved,
            "conversation_id": new_conversation_id,
            "timestamp": time.time(),
        }

    def batch_ask(
        self,
        questions: List[str],
        memories: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """批量提问"""
        results = []
        conversation_id = None
        
        for question in questions:
            result = self.ask(question, memories, conversation_id)
            conversation_id = result["conversation_id"]
            results.append(result)
        
        return results

    def get_conversation_history(self, conversation_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取对话历史"""
        return self.conversation.get_history(conversation_id)

    def clear_conversation(self, conversation_id: Optional[str] = None):
        """清除对话"""
        self.conversation.clear_history(conversation_id)
