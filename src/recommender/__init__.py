"""
记忆推荐系统模块
基于第一性原理：确定性、简洁性、可扩展性
"""

import time
from typing import Dict, List, Optional, Set, Any, Callable
from collections import defaultdict
from enum import Enum


class RecommendationStrategy(Enum):
    """推荐策略枚举"""
    RECENTLY_ACCESSED = "recently_accessed"
    RELATED = "related"
    IMPORTANT = "important"
    TAGGED = "tagged"
    COMBINED = "combined"


class MemoryRecommendation:
    """单条记忆推荐结果"""

    def __init__(
        self,
        memory_id: str,
        score: float,
        reason: str,
        strategy: RecommendationStrategy,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.memory_id = memory_id
        self.score = score
        self.reason = reason
        self.strategy = strategy
        self.metadata = metadata or {}
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "score": self.score,
            "reason": self.reason,
            "strategy": self.strategy.value,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }


class MemoryRecommender:
    """记忆推荐系统"""

    def __init__(self):
        # 访问历史: memory_id -> list of access timestamps
        self.access_history: Dict[str, List[float]] = defaultdict(list)
        # 记忆内容缓存
        self.memory_content: Dict[str, str] = {}
        # 记忆元数据
        self.memory_metadata: Dict[str, Dict[str, Any]] = defaultdict(dict)
        # 关系映射
        self.relations: Dict[str, List[str]] = defaultdict(list)
        # 标签映射
        self.tags: Dict[str, List[str]] = defaultdict(list)
        # 重要性评分
        self.importance: Dict[str, float] = defaultdict(float)

    def register_memory(
        self,
        memory_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """注册记忆到推荐系统"""
        self.memory_content[memory_id] = content
        if metadata:
            self.memory_metadata[memory_id].update(metadata)

    def register_access(self, memory_id: str):
        """记录记忆访问"""
        self.access_history[memory_id].append(time.time())

    def register_relation(self, memory_id: str, related_id: str):
        """注册记忆间关系"""
        if related_id not in self.relations[memory_id]:
            self.relations[memory_id].append(related_id)

    def register_tag(self, memory_id: str, tag: str):
        """注册记忆标签"""
        if tag not in self.tags[memory_id]:
            self.tags[memory_id].append(tag)

    def register_importance(self, memory_id: str, score: float):
        """注册记忆重要性评分 (0-10)"""
        self.importance[memory_id] = max(0, min(10, score))

    def recommend_recently_accessed(
        self,
        limit: int = 10,
        hours: int = 24
    ) -> List[MemoryRecommendation]:
        """推荐最近访问的记忆"""
        recommendations = []
        cutoff_time = time.time() - (hours * 3600)

        for memory_id, access_times in self.access_history.items():
            recent_accesses = [t for t in access_times if t >= cutoff_time]
            if recent_accesses:
                # 按访问频率和最近时间计算分数
                latest = max(recent_accesses)
                count = len(recent_accesses)
                recency_score = min(1, (latest - cutoff_time) / (hours * 3600))
                frequency_score = min(1, count / 10)
                total_score = (recency_score * 0.7) + (frequency_score * 0.3)

                recommendations.append(MemoryRecommendation(
                    memory_id=memory_id,
                    score=total_score,
                    reason=f"最近访问过{count}次",
                    strategy=RecommendationStrategy.RECENTLY_ACCESSED,
                    metadata={"last_access": latest, "access_count": count}
                ))

        # 按分数排序并限制数量
        recommendations.sort(key=lambda r: r.score, reverse=True)
        return recommendations[:limit]

    def recommend_related(
        self,
        context_memory_id: str,
        limit: int = 10
    ) -> List[MemoryRecommendation]:
        """推荐与给定记忆相关的记忆"""
        if context_memory_id not in self.relations:
            return []

        recommendations = []
        for related_id in self.relations[context_memory_id]:
            recommendations.append(MemoryRecommendation(
                memory_id=related_id,
                score=0.8,
                reason=f"与{context_memory_id}相关",
                strategy=RecommendationStrategy.RELATED
            ))

        recommendations.sort(key=lambda r: r.score, reverse=True)
        return recommendations[:limit]

    def recommend_important(
        self,
        limit: int = 10,
        min_importance: float = 5.0
    ) -> List[MemoryRecommendation]:
        """推荐重要的记忆"""
        recommendations = []

        for memory_id, score in self.importance.items():
            if score >= min_importance:
                recommendations.append(MemoryRecommendation(
                    memory_id=memory_id,
                    score=score / 10,
                    reason=f"重要性评分为{score:.1f}",
                    strategy=RecommendationStrategy.IMPORTANT,
                    metadata={"importance_score": score}
                ))

        recommendations.sort(key=lambda r: r.score, reverse=True)
        return recommendations[:limit]

    def recommend_by_tag(
        self,
        target_tags: List[str],
        limit: int = 10
    ) -> List[MemoryRecommendation]:
        """按标签推荐记忆"""
        recommendations = []

        for memory_id, tags in self.tags.items():
            matching_tags = [t for t in tags if t in target_tags]
            if matching_tags:
                score = len(matching_tags) / len(target_tags)
                recommendations.append(MemoryRecommendation(
                    memory_id=memory_id,
                    score=score,
                    reason=f"匹配标签: {', '.join(matching_tags)}",
                    strategy=RecommendationStrategy.TAGGED,
                    metadata={"matching_tags": matching_tags}
                ))

        recommendations.sort(key=lambda r: r.score, reverse=True)
        return recommendations[:limit]

    def recommend_combined(
        self,
        context: Optional[str] = None,
        context_memory_id: Optional[str] = None,
        target_tags: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[MemoryRecommendation]:
        """
        综合推荐，结合多种策略
        """
        all_recommendations = defaultdict(list)

        # 收集各种策略的推荐
        rec1 = self.recommend_recently_accessed(limit=20)
        rec2 = self.recommend_important(limit=20)
        rec3 = []
        if context_memory_id:
            rec3 = self.recommend_related(context_memory_id, limit=20)
        rec4 = []
        if target_tags:
            rec4 = self.recommend_by_tag(target_tags, limit=20)

        # 合并并加权评分
        memory_scores = defaultdict(float)
        memory_metadata = defaultdict(dict)

        for rec_list, weight in [(rec1, 0.3), (rec2, 0.3), (rec3, 0.2), (rec4, 0.2)]:
            for rec in rec_list:
                memory_scores[rec.memory_id] += rec.score * weight
                memory_metadata[rec.memory_id][rec.strategy.value] = rec.reason

        # 创建推荐结果
        final_recommendations = []
        for memory_id, total_score in sorted(
            memory_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]:
            # 找出得分最高的策略
            best_reason = "综合推荐"
            best_strategy = RecommendationStrategy.COMBINED
            if memory_metadata[memory_id]:
                best_reason = "; ".join(memory_metadata[memory_id].values())

            final_recommendations.append(MemoryRecommendation(
                memory_id=memory_id,
                score=total_score,
                reason=best_reason,
                strategy=best_strategy,
                metadata=memory_metadata[memory_id]
            ))

        return final_recommendations

    def get_recommendations(
        self,
        strategy: RecommendationStrategy = RecommendationStrategy.COMBINED,
        context_memory_id: Optional[str] = None,
        target_tags: Optional[List[str]] = None,
        context_text: Optional[str] = None,
        limit: int = 10
    ) -> List[MemoryRecommendation]:
        """统一的推荐接口"""
        if strategy == RecommendationStrategy.RECENTLY_ACCESSED:
            return self.recommend_recently_accessed(limit=limit)
        elif strategy == RecommendationStrategy.RELATED and context_memory_id:
            return self.recommend_related(context_memory_id, limit=limit)
        elif strategy == RecommendationStrategy.IMPORTANT:
            return self.recommend_important(limit=limit)
        elif strategy == RecommendationStrategy.TAGGED and target_tags:
            return self.recommend_by_tag(target_tags, limit=limit)
        else:
            return self.recommend_combined(
                context=context_text,
                context_memory_id=context_memory_id,
                target_tags=target_tags,
                limit=limit
            )

    def get_statistics(self) -> Dict[str, Any]:
        """获取推荐系统统计信息"""
        return {
            "registered_memories": len(self.memory_content),
            "total_accesses": sum(len(times) for times in self.access_history.values()),
            "memories_with_relations": len(self.relations),
            "memories_with_tags": len(self.tags),
            "memories_with_importance": len(self.importance)
        }


class EnhancedMemoryWithRecommender:
    """
    增强的记忆系统（带推荐功能）
    装饰器模式实现
    """

    def __init__(self, memory_system):
        self.memory_system = memory_system
        self.recommender = MemoryRecommender()

    def add_with_recommendation(
        self,
        text: str,
        task_id: str = "default",
        memory_level: Optional[str] = None,
        tags: Optional[List[str]] = None,
        importance: Optional[float] = None
    ) -> str:
        """添加记忆并注册到推荐系统"""
        memory_id = self.memory_system.add(text, task_id, memory_level)

        # 注册到推荐系统
        self.recommender.register_memory(memory_id, text, {"task_id": task_id})

        if tags:
            for tag in tags:
                self.recommender.register_tag(memory_id, tag)

        if importance is not None:
            self.recommender.register_importance(memory_id, importance)

        return memory_id

    def access_memory(self, memory_id: str):
        """记录记忆访问"""
        self.recommender.register_access(memory_id)

    def add_memory_relation(self, memory_id: str, related_id: str):
        """添加记忆间关系"""
        self.recommender.register_relation(memory_id, related_id)

    def get_recommendations(
        self,
        strategy: RecommendationStrategy = RecommendationStrategy.COMBINED,
        context_memory_id: Optional[str] = None,
        target_tags: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[MemoryRecommendation]:
        """获取推荐"""
        return self.recommender.get_recommendations(
            strategy=strategy,
            context_memory_id=context_memory_id,
            target_tags=target_tags,
            limit=limit
        )

    def get_recommendation_stats(self) -> Dict[str, Any]:
        """获取推荐系统统计"""
        return self.recommender.get_statistics()
