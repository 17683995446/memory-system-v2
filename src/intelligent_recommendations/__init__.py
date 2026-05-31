"""
记忆系统智能建议和推荐功能
基于第一性原理：从用户行为出发，实现个性化、可解释的推荐
"""

import time
import math
import json
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, Counter
from datetime import datetime, timedelta


class ActionType(Enum):
    """用户行为类型"""
    VIEW = "view"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    SEARCH = "search"
    RECOMMEND_CLICK = "recommend_click"
    FAVORITE = "favorite"


class RecommendationType(Enum):
    """推荐类型"""
    RECENT = "recent"
    SIMILAR = "similar"
    TRENDING = "trending"
    ASSOCIATIVE = "associative"
    PERSONALIZED = "personalized"
    SURPRISING = "surprising"


@dataclass
class UserAction:
    """用户行为记录"""
    user_id: str
    action_type: ActionType
    memory_id: Optional[str] = None
    query: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryInteraction:
    """记忆交互记录"""
    memory_id: str
    view_count: int = 0
    create_count: int = 0
    update_count: int = 0
    search_match_count: int = 0
    recommend_click_count: int = 0
    favorite_count: int = 0
    last_interaction_time: float = 0.0
    total_time_spent: float = 0.0


@dataclass
class Recommendation:
    """推荐结果"""
    memory_id: str
    score: float
    reason: str
    type: RecommendationType
    confidence: float = 0.5
    metadata: Dict[str, Any] = field(default_factory=dict)


class UserBehaviorAnalyzer:
    """用户行为分析器"""
    
    def __init__(self):
        self.user_actions: Dict[str, List[UserAction]] = defaultdict(list)
        self.memory_interactions: Dict[str, Dict[str, MemoryInteraction]] = defaultdict(dict)
        self.user_profiles: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.co_occurrence_matrix: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    
    def record_action(self, action: UserAction) -> None:
        """记录用户行为"""
        self.user_actions[action.user_id].append(action)
        
        # 更新记忆交互
        if action.memory_id:
            if action.user_id not in self.memory_interactions:
                self.memory_interactions[action.user_id] = {}
            
            if action.memory_id not in self.memory_interactions[action.user_id]:
                self.memory_interactions[action.user_id][action.memory_id] = MemoryInteraction(
                    memory_id=action.memory_id
                )
            
            interaction = self.memory_interactions[action.user_id][action.memory_id]
            
            if action.action_type == ActionType.VIEW:
                interaction.view_count += 1
            elif action.action_type == ActionType.CREATE:
                interaction.create_count += 1
            elif action.action_type == ActionType.UPDATE:
                interaction.update_count += 1
            elif action.action_type == ActionType.SEARCH:
                interaction.search_match_count += 1
            elif action.action_type == ActionType.RECOMMEND_CLICK:
                interaction.recommend_click_count += 1
            elif action.action_type == ActionType.FAVORITE:
                interaction.favorite_count += 1
            
            interaction.last_interaction_time = action.timestamp
            
            # 记录共现
            self._record_co_occurrence(action.user_id, action.memory_id)
    
    def _record_co_occurrence(self, user_id: str, memory_id: str) -> None:
        """记录记忆共现关系"""
        recent_memories = self._get_recent_memory_ids(user_id, time_window=3600)
        
        for other_id in recent_memories:
            if other_id != memory_id:
                self.co_occurrence_matrix[memory_id][other_id] += 1
                self.co_occurrence_matrix[other_id][memory_id] += 1
    
    def _get_recent_memory_ids(self, user_id: str, time_window: float = 3600) -> List[str]:
        """获取最近访问的记忆ID"""
        cutoff = time.time() - time_window
        recent_ids = []
        
        for action in reversed(self.user_actions.get(user_id, [])):
            if action.timestamp < cutoff:
                break
            if action.memory_id and action.memory_id not in recent_ids:
                recent_ids.append(action.memory_id)
        
        return recent_ids
    
    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """获取用户画像"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = self._build_user_profile(user_id)
        
        return self.user_profiles[user_id]
    
    def _build_user_profile(self, user_id: str) -> Dict[str, Any]:
        """构建用户画像"""
        actions = self.user_actions.get(user_id, [])
        interactions = self.memory_interactions.get(user_id, {})
        
        profile = {
            "user_id": user_id,
            "total_actions": len(actions),
            "active_memory_count": len(interactions),
            "preferred_times": self._analyze_preferred_times(actions),
            "interest_signals": self._extract_interest_signals(interactions),
            "recency_bias": self._calculate_recency_bias(interactions),
            "search_patterns": self._analyze_search_patterns(actions)
        }
        
        return profile
    
    def _analyze_preferred_times(self, actions: List[UserAction]) -> Dict[int, int]:
        """分析用户偏好时间段"""
        hour_counts = defaultdict(int)
        for action in actions:
            dt = datetime.fromtimestamp(action.timestamp)
            hour_counts[dt.hour] += 1
        return dict(hour_counts)
    
    def _extract_interest_signals(self, interactions: Dict[str, MemoryInteraction]) -> Dict[str, float]:
        """提取兴趣信号"""
        signals = {}
        
        for memory_id, interaction in interactions.items():
            # 计算综合兴趣评分
            score = (
                interaction.view_count * 0.3 +
                interaction.update_count * 1.0 +
                interaction.search_match_count * 0.5 +
                interaction.recommend_click_count * 0.8 +
                interaction.favorite_count * 2.0
            )
            signals[memory_id] = score
        
        return signals
    
    def _calculate_recency_bias(self, interactions: Dict[str, MemoryInteraction]) -> float:
        """计算时效性偏好"""
        times = [
            inter.last_interaction_time
            for inter in interactions.values()
            if inter.last_interaction_time > 0
        ]
        
        if not times:
            return 0.5
        
        now = time.time()
        avg_recency = sum(now - t for t in times) / len(times)
        
        # 归一化到0-1范围，平均越近得分越高
        max_recency = 7 * 24 * 3600  # 一周
        return max(0, min(1, 1 - avg_recency / max_recency))
    
    def _analyze_search_patterns(self, actions: List[UserAction]) -> List[str]:
        """分析搜索模式"""
        search_queries = [
            action.query
            for action in actions
            if action.action_type == ActionType.SEARCH and action.query
        ]
        return search_queries


class MemoryAssociator:
    """记忆关联发现器"""
    
    def __init__(self):
        self.co_occurrence = defaultdict(lambda: defaultdict(int))
        self.similarity_cache = {}
    
    def add_co_occurrence(self, memory_a: str, memory_b: str) -> None:
        """添加共现记录"""
        self.co_occurrence[memory_a][memory_b] += 1
        self.co_occurrence[memory_b][memory_a] += 1
    
    def get_associated_memories(
        self,
        memory_id: str,
        limit: int = 10
    ) -> List[Tuple[str, float]]:
        """获取关联记忆"""
        if memory_id not in self.co_occurrence:
            return []
        
        associations = []
        for other_id, count in self.co_occurrence[memory_id].items():
            if other_id != memory_id:
                # 计算关联强度
                strength = self._calculate_association_strength(memory_id, other_id)
                associations.append((other_id, strength))
        
        # 排序并限制
        associations.sort(key=lambda x: x[1], reverse=True)
        return associations[:limit]
    
    def _calculate_association_strength(self, memory_a: str, memory_b: str) -> float:
        """计算关联强度（基于Jaccard和PMI）"""
        # 简单版：使用计数的平方根作为强度
        count = self.co_occurrence[memory_a][memory_b]
        return math.sqrt(count) if count > 0 else 0.0


class MemoryRecommender:
    """记忆推荐系统"""
    
    def __init__(self):
        self.analyzer = UserBehaviorAnalyzer()
        self.associator = MemoryAssociator()
        self.memory_content_cache: Dict[str, str] = {}
        self.memory_metadata_cache: Dict[str, Dict[str, Any]] = {}
    
    def register_memory(self, memory_id: str, content: str, metadata: Dict[str, Any] = None) -> None:
        """注册记忆内容"""
        self.memory_content_cache[memory_id] = content
        if metadata:
            self.memory_metadata_cache[memory_id] = metadata
    
    def record_user_action(self, action: UserAction) -> None:
        """记录用户行为"""
        self.analyzer.record_action(action)
        
        # 更新共现
        if action.memory_id:
            recent = self.analyzer._get_recent_memory_ids(action.user_id, 3600)
            for other_id in recent:
                if other_id != action.memory_id:
                    self.associator.add_co_occurrence(action.memory_id, other_id)
    
    def get_recommendations(
        self,
        user_id: str,
        types: Optional[List[RecommendationType]] = None,
        limit: int = 10
    ) -> List[Recommendation]:
        """获取综合推荐"""
        if types is None:
            types = list(RecommendationType)
        
        all_recommendations = []
        
        # 获取各类推荐
        if RecommendationType.RECENT in types:
            all_recommendations.extend(self._recommend_recent(user_id))
        
        if RecommendationType.SIMILAR in types:
            all_recommendations.extend(self._recommend_similar(user_id))
        
        if RecommendationType.TRENDING in types:
            all_recommendations.extend(self._recommend_trending(user_id))
        
        if RecommendationType.ASSOCIATIVE in types:
            all_recommendations.extend(self._recommend_associative(user_id))
        
        if RecommendationType.PERSONALIZED in types:
            all_recommendations.extend(self._recommend_personalized(user_id))
        
        if RecommendationType.SURPRISING in types:
            all_recommendations.extend(self._recommend_surprising(user_id))
        
        # 去重、排序、限制
        return self._aggregate_recommendations(all_recommendations, limit)
    
    def _recommend_recent(self, user_id: str, limit: int = 5) -> List[Recommendation]:
        """推荐最近访问的记忆"""
        profile = self.analyzer.get_user_profile(user_id)
        interest_signals = profile.get("interest_signals", {})
        
        # 按最近交互时间排序
        interactions = self.analyzer.memory_interactions.get(user_id, {})
        recent_sorted = sorted(
            interactions.items(),
            key=lambda x: x[1].last_interaction_time,
            reverse=True
        )
        
        recommendations = []
        for memory_id, interaction in recent_sorted[:limit]:
            recency_score = min(1.0, max(0.1,
                1 - (time.time() - interaction.last_interaction_time) / (7 * 24 * 3600)
            ))
            
            recommendations.append(Recommendation(
                memory_id=memory_id,
                score=recency_score,
                reason="Recently accessed",
                type=RecommendationType.RECENT,
                confidence=0.8
            ))
        
        return recommendations
    
    def _recommend_similar(self, user_id: str, limit: int = 5) -> List[Recommendation]:
        """推荐相似记忆"""
        # 基于用户兴趣找到相似的记忆
        profile = self.analyzer.get_user_profile(user_id)
        interest_signals = profile.get("interest_signals", {})
        
        if not interest_signals:
            return []
        
        recommendations = []
        
        # 对用户最感兴趣的记忆，找相似的
        top_interests = sorted(interest_signals.items(), key=lambda x: x[1], reverse=True)[:3]
        
        for memory_id, score in top_interests:
            associated = self.associator.get_associated_memories(memory_id, limit=2)
            for assoc_id, assoc_strength in associated:
                recommendations.append(Recommendation(
                    memory_id=assoc_id,
                    score=assoc_strength * 0.7,
                    reason=f"Similar to frequently accessed memory: {memory_id[:20]}",
                    type=RecommendationType.SIMILAR,
                    confidence=0.6
                ))
        
        return recommendations
    
    def _recommend_trending(self, user_id: str, limit: int = 5) -> List[Recommendation]:
        """推荐热门记忆（简化版）"""
        # 统计全局活跃度
        all_interactions = []
        for user_interactions in self.analyzer.memory_interactions.values():
            for memory_id, interaction in user_interactions.items():
                total_activity = (
                    interaction.view_count +
                    interaction.update_count * 2 +
                    interaction.favorite_count * 3
                )
                all_interactions.append((memory_id, total_activity))
        
        # 排序
        all_interactions.sort(key=lambda x: x[1], reverse=True)
        
        recommendations = []
        for memory_id, activity in all_interactions[:limit]:
            # 排除用户已经看过很多的
            user_inter = self.analyzer.memory_interactions.get(user_id, {})
            if memory_id not in user_inter or user_inter[memory_id].view_count < 2:
                recommendations.append(Recommendation(
                    memory_id=memory_id,
                    score=min(1.0, activity / 10.0),
                    reason="Popular among users",
                    type=RecommendationType.TRENDING,
                    confidence=0.5
                ))
        
        return recommendations
    
    def _recommend_associative(self, user_id: str, limit: int = 5) -> List[Recommendation]:
        """推荐关联记忆"""
        recommendations = []
        recent_memories = self.analyzer._get_recent_memory_ids(user_id, time_window=86400)
        
        for memory_id in recent_memories:
            associated = self.associator.get_associated_memories(memory_id, limit=2)
            for assoc_id, strength in associated:
                recommendations.append(Recommendation(
                    memory_id=assoc_id,
                    score=strength * 0.6,
                    reason=f"Associated with memory: {memory_id[:20]}",
                    type=RecommendationType.ASSOCIATIVE,
                    confidence=0.6
                ))
        
        return recommendations
    
    def _recommend_personalized(self, user_id: str, limit: int = 5) -> List[Recommendation]:
        """个性化推荐"""
        profile = self.analyzer.get_user_profile(user_id)
        interest_signals = profile.get("interest_signals", {})
        
        if not interest_signals:
            return []
        
        # 基于用户兴趣评分推荐
        recommendations = []
        for memory_id, interest_score in interest_signals.items():
            normalized_score = min(1.0, interest_score / 10.0)
            recommendations.append(Recommendation(
                memory_id=memory_id,
                score=normalized_score,
                reason="Based on your interests",
                type=RecommendationType.PERSONALIZED,
                confidence=0.7
            ))
        
        recommendations.sort(key=lambda x: x.score, reverse=True)
        return recommendations[:limit]
    
    def _recommend_surprising(self, user_id: str, limit: int = 3) -> List[Recommendation]:
        """惊喜推荐（探索性）"""
        # 找到用户不太常访问但可能感兴趣的
        user_inter = self.analyzer.memory_interactions.get(user_id, {})
        all_memory_ids = set(self.memory_content_cache.keys())
        user_memory_ids = set(user_inter.keys())
        
        # 找用户没看过的记忆
        unexplored = all_memory_ids - user_memory_ids
        
        if not unexplored:
            return []
        
        # 选择一些有一定活跃度但用户没看的
        candidates = []
        for memory_id in list(unexplored)[:20]:
            # 检查是否在其他用户那里有一些活跃度
            global_activity = 0
            for user_memories in self.analyzer.memory_interactions.values():
                if memory_id in user_memories:
                    global_activity += 1
            
            if global_activity > 0:
                candidates.append((memory_id, global_activity))
        
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        recommendations = []
        for memory_id, activity in candidates[:limit]:
            recommendations.append(Recommendation(
                memory_id=memory_id,
                score=0.4 + activity * 0.05,
                reason="You might find this interesting",
                type=RecommendationType.SURPRISING,
                confidence=0.4
            ))
        
        return recommendations
    
    def _aggregate_recommendations(
        self,
        recommendations: List[Recommendation],
        limit: int
    ) -> List[Recommendation]:
        """聚合和排序推荐"""
        # 按ID去重，保留最高得分
        dedup = {}
        for rec in recommendations:
            if rec.memory_id not in dedup or rec.score > dedup[rec.memory_id].score:
                dedup[rec.memory_id] = rec
        
        # 排序
        sorted_recs = sorted(dedup.values(), key=lambda x: x.score, reverse=True)
        
        # 设置排名
        for i, rec in enumerate(sorted_recs[:limit]):
            rec.metadata['rank'] = i + 1
        
        return sorted_recs[:limit]


class PersonalizedLearner:
    """个性化学习器"""
    
    def __init__(self):
        self.user_feedback: Dict[str, List[Tuple[str, bool, float]]] = defaultdict(list)
        self.recommendation_feedback: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    
    def record_feedback(
        self,
        user_id: str,
        memory_id: str,
        is_positive: bool,
        timestamp: float = None
    ) -> None:
        """记录用户反馈"""
        ts = timestamp or time.time()
        self.user_feedback[user_id].append((memory_id, is_positive, ts))
        
        key = f"{user_id}:{memory_id}"
        self.recommendation_feedback[key][is_positive] += 1
    
    def get_adaptive_score(
        self,
        user_id: str,
        memory_id: str
    ) -> Tuple[float, str]:
        """获取自适应评分"""
        key = f"{user_id}:{memory_id}"
        feedback = self.recommendation_feedback.get(key, {})
        
        positives = feedback.get(True, 0)
        negatives = feedback.get(False, 0)
        total = positives + negatives
        
        if total == 0:
            return 0.5, "No feedback yet"
        
        score = positives / total
        return score, f"Based on {total} feedback signals"
    
    def optimize_recommendations(
        self,
        user_id: str,
        recommendations: List[Recommendation]
    ) -> List[Recommendation]:
        """优化推荐（基于反馈）"""
        optimized = []
        for rec in recommendations:
            adaptive_score, reason = self.get_adaptive_score(user_id, rec.memory_id)
            
            # 融合原始得分和自适应得分
            final_score = rec.score * 0.7 + adaptive_score * 0.3
            
            optimized_rec = Recommendation(
                memory_id=rec.memory_id,
                score=final_score,
                reason=f"{rec.reason} | {reason}",
                type=rec.type,
                confidence=min(1.0, rec.confidence + adaptive_score * 0.2)
            )
            optimized.append(optimized_rec)
        
        # 重新排序
        optimized.sort(key=lambda x: x.score, reverse=True)
        return optimized


class IntelligentSuggestionEngine:
    """智能建议引擎（综合类）"""
    
    def __init__(self):
        self.recommender = MemoryRecommender()
        self.learner = PersonalizedLearner()
        self.suggestion_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    
    def register_memory(self, memory_id: str, content: str, metadata: Dict[str, Any] = None) -> None:
        """注册记忆"""
        self.recommender.register_memory(memory_id, content, metadata)
    
    def record_user_action(
        self,
        user_id: str,
        action_type: ActionType,
        memory_id: Optional[str] = None,
        query: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ) -> None:
        """记录用户行为"""
        action = UserAction(
            user_id=user_id,
            action_type=action_type,
            memory_id=memory_id,
            query=query,
            metadata=metadata or {}
        )
        self.recommender.record_user_action(action)
    
    def record_feedback(
        self,
        user_id: str,
        memory_id: str,
        is_positive: bool
    ) -> None:
        """记录反馈"""
        self.learner.record_feedback(user_id, memory_id, is_positive)
    
    def get_suggestions(
        self,
        user_id: str,
        types: Optional[List[RecommendationType]] = None,
        limit: int = 10,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Recommendation]:
        """获取建议"""
        # 获取初始推荐
        recommendations = self.recommender.get_recommendations(user_id, types, limit)
        
        # 个性化优化
        optimized = self.learner.optimize_recommendations(user_id, recommendations)
        
        # 记录历史
        self.suggestion_history[user_id].append({
            "timestamp": time.time(),
            "recommendations": optimized,
            "context": context
        })
        
        return optimized
    
    def get_smart_completion(
        self,
        user_id: str,
        partial_content: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """智能补全建议"""
        profile = self.recommender.analyzer.get_user_profile(user_id)
        
        # 简单版本：基于最近的记忆内容提供补全
        suggestions = []
        recent_memories = self.recommender.analyzer._get_recent_memory_ids(user_id)
        
        for memory_id in recent_memories[:limit]:
            if memory_id in self.recommender.memory_content_cache:
                content = self.recommender.memory_content_cache[memory_id]
                if partial_content.lower() in content.lower():
                    suggestions.append({
                        "memory_id": memory_id,
                        "suggested_content": content,
                        "type": "recent_content"
                    })
        
        return suggestions[:limit]
    
    def get_contextual_reminders(
        self,
        user_id: str,
        current_context: Dict[str, Any],
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """上下文提醒"""
        reminders = []
        
        # 基于时间的提醒
        current_hour = datetime.now().hour
        profile = self.recommender.analyzer.get_user_profile(user_id)
        preferred_times = profile.get("preferred_times", {})
        
        if current_hour in preferred_times:
            # 这是用户活跃时段，推荐相关内容
            recent_recs = self.recommender._recommend_recent(user_id, limit=3)
            for rec in recent_recs:
                reminders.append({
                    "memory_id": rec.memory_id,
                    "type": "time_based",
                    "reason": "You usually access this content around this time"
                })
        
        return reminders[:limit]


# 全局实例
_global_engine: Optional[IntelligentSuggestionEngine] = None


def get_intelligent_engine() -> IntelligentSuggestionEngine:
    """获取智能建议引擎单例"""
    global _global_engine
    if _global_engine is None:
        _global_engine = IntelligentSuggestionEngine()
    return _global_engine
