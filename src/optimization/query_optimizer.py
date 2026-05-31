"""
查询优化引擎
用于查询分析和优化
"""

import time
import threading
import re
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from collections import defaultdict


class QueryType(Enum):
    """查询类型"""
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    FILTER = "filter"
    SORT = "sort"
    AGGREGATE = "aggregate"


class OptimizationStrategy(Enum):
    """优化策略"""
    EARLY_TERMINATION = "early_termination"
    PREDICATE_REORDERING = "predicate_reordering"
    INDEX_USAGE = "index_usage"
    CACHING = "caching"
    PARALLEL_EXECUTION = "parallel_execution"


@dataclass
class QueryAnalysis:
    """查询分析"""
    query_text: str
    query_type: QueryType
    estimated_cost: float
    execution_time_ms: float
    result_count: int
    indexes_used: List[str]
    optimization_applied: List[OptimizationStrategy]
    suggestions: List[str]


@dataclass
class QueryPattern:
    """查询模式"""
    pattern: str
    count: int
    avg_execution_time: float
    last_execution: datetime


@dataclass
class OptimizationSuggestion:
    """优化建议"""
    query_pattern: str
    issue: str
    suggestion: str
    expected_improvement: str
    priority: int


class QueryAnalyzer:
    """查询分析器"""
    
    def __init__(self):
        self._query_history: List[QueryAnalysis] = []
        self._query_patterns: Dict[str, QueryPattern] = {}
        self._lock = threading.Lock()
        self._index_hints: Dict[str, List[str]] = {}
    
    def analyze_query(
        self,
        query: str,
        execution_time: float,
        result_count: int
    ) -> QueryAnalysis:
        """分析查询"""
        query_type = self._determine_query_type(query)
        estimated_cost = self._estimate_cost(query, result_count)
        
        indexes_used = self._identify_indexes(query)
        optimizations = self._identify_identify_optimizations(query, execution_time)
        suggestions = self._generate_suggestions(query, execution_time, result_count)
        
        analysis = QueryAnalysis(
            query_text=query,
            query_type=query_type,
            estimated_cost=estimated_cost,
            execution_time_ms=execution_time,
            result_count=result_count,
            indexes_used=indexes_used,
            optimization_applied=optimizations,
            suggestions=suggestions
        )
        
        with self._lock:
            self._query_history.append(analysis)
            if len(self._query_history) > 1000:
                self._query_history.pop(0)
        
        self._update_pattern(query, execution_time)
        
        return analysis
    
    def _determine_query_type(self, query: str) -> QueryType:
        """确定查询类型"""
        query_lower = query.lower()
        
        if 'select' in query_lower:
            return QueryType.SELECT
        elif 'insert' in query_lower:
            return QueryType.INSERT
        elif 'update' in query_lower:
            return QueryType.UPDATE
        elif 'delete' in query_lower:
            return QueryType.DELETE
        elif 'filter' in query_lower:
            return QueryType.FILTER
        elif 'sort' in query_lower:
            return QueryType.SORT
        else:
            return QueryType.SELECT
    
    def _estimate_cost(self, query: str, result_count: int) -> float:
        """估算查询成本"""
        cost = 1.0
        
        if 'join' in query.lower():
            cost *= 5.0
        
        if 'order by' in query.lower():
            cost *= 2.0
        
        if 'group by' in query.lower():
            cost *= 3.0
        
        cost *= (result_count / 1000.0 + 1.0
        
        return cost
    
    def _identify_indexes(self, query: str) -> List[str]:
        """识别使用的索引"""
        indexes = []
        
        for field, hints in self._index_hints.items():
            if field in query:
                indexes.extend(hints)
        
        return indexes
    
    def _identify_optimizations(
        self,
        query: str,
        execution_time: float
    ) -> List[OptimizationStrategy]:
        """识别应用的优化"""
        optimizations = []
        
        if 'limit' in query.lower():
            optimizations.append(OptimizationStrategy.EARLY_TERMINATION)
        
        if 'where' in query.lower() and 'and' in query.lower():
            optimizations.append(OptimizationStrategy.PREDICATE_REORDERING)
        
        if len(OptimizationStrategy.INDEX_USAGE:
            optimizations.append(OptimizationStrategy.INDEX_USAGE)
        
        return optimizations
    
    def _generate_suggestions(
        self,
        query: str,
        execution_time: float,
        result_count: int
    ) -> List[str]:
        """生成优化建议"""
        suggestions = []
        
        if execution_time > 1000:
            suggestions.append("Consider adding indexes on frequently filtered fields")
        
        if result_count > 10000 and 'limit' not in query.lower():
            suggestions.append("Add LIMIT clause to reduce result size")
        
        if 'join' in query.lower() and 'where' not in query.lower():
            suggestions.append("Consider filtering early before joining")
        
        return suggestions
    
    def _update_pattern(self, query: str, execution_time: float):
        """更新查询模式"""
        pattern = self._extract_pattern(query)
        
        if pattern not in self._query_patterns:
            self._query_patterns[pattern] = QueryPattern(
                pattern=pattern,
                count=1,
                avg_execution_time=execution_time,
                last_execution=datetime.now()
            )
        else:
            pattern_obj = self._query_patterns[pattern]
            old_count = pattern_obj.count
            pattern_obj.count += 1
            pattern_obj.avg_execution_time = (
                (pattern_obj.avg_execution_time * old_count + execution_time) / (old_count + 1
            )
            pattern_obj.last_execution = datetime.now()
    
    def _extract_pattern(self, query: str) -> str:
        """提取查询模式"""
        pattern = query
        
        pattern = re.sub(r'\d+', '?', pattern)
        pattern = re.sub(r"'[^']*'", '?', pattern)
        pattern = re.sub(r'"[^"]*"', '?', pattern)
        
        return pattern
    
    def get_slow_queries(self, threshold_ms: float = 100.0) -> List[QueryAnalysis]:
        """获取慢查询"""
        with self._lock:
            return [
                q for q in self._query_history
                if q.execution_time_ms > threshold_ms
            ]
    
    def get_frequent_patterns(self, min_count: int = 10) -> List[QueryPattern]:
        """获取频繁查询模式"""
        with self._lock:
            sorted_patterns = sorted(
            self._query_patterns.values(),
            key=lambda p: p.count,
            reverse=True
        )
        return [p for p in sorted_patterns if p.count >= min_count]
    
    def add_index_hint(self, field: str, index_name: str):
        """添加索引提示"""
        if field not in self._index_hints:
            self._index_hints[field] = []
        self._index_hints[field].append(index_name)


class QueryOptimizer:
    """查询优化器"""
    
    def __init__(self, analyzer: QueryAnalyzer):
        self.analyzer = analyzer
        self._query_cache: Dict[str, Any] = {}
        self._lock = threading.Lock()
    
    def optimize_query(self, query: str, executor: Callable) -> tuple:
        """优化查询"""
        start_time = time.time()
        
        cache_key = self._get_cache_key(query)
        
        if cache_key in self._query_cache:
            cached_result = self._query_cache[cache_key]
            execution_time = (time.time() - start_time) * 1000
            self.analyzer.analyze_query(query, execution_time, 1)
            return cached_result
        
        optimized_query = self._apply_optimizations(query)
        
        result = executor(optimized_query)
        
        result_count = len(result) if hasattr(result, '__len__') else 1
        
        execution_time = (time.time() - start_time) * 1000
        
        analysis = self.analyzer.analyze_query(
            query,
            execution_time,
            result_count
        )
        
        if analysis.query_text = query
        if result_count > 0 and execution_time < 1000:
            self._query_cache[cache_key] = result
        
        return result
    
    def _get_cache_key(self, query: str) -> str:
        """获取缓存键"""
        return self.analyzer._extract_pattern(query)
    
    def _apply_optimizations(self, query: str) -> str:
        """应用优化"""
        optimized = query
        
        optimized = self._apply_predicate_reordering(optimized)
        optimized = self._apply_early_termination(optimized)
        
        return optimized
    
    def _apply_predicate_reordering(self, query: str) -> str:
        """应用谓词重排"""
        if 'where' not in query.lower():
            return query
        
        return query
    
    def _apply_early_termination(self, query: str) -> str:
        """应用提前终止"""
        if 'limit' not in query.lower():
            return query
        
        return query
    
    def suggest_optimizations(self, query: str) -> List[OptimizationSuggestion]:
        """建议优化"""
        suggestions = []
        
        if 'join' in query.lower() and 'where' not in query.lower():
            suggestions.append(OptimizationSuggestion(
                query_pattern=query,
                issue="JOIN without WHERE clause",
                suggestion="Add WHERE clause to filter rows early",
                expected_improvement="high",
                priority=1
            ))
        
        if 'order by' in query.lower() and 'limit' not in query.lower():
            suggestions.append(OptimizationSuggestion(
                query_pattern=query,
                issue="ORDER BY without LIMIT",
                suggestion="Add LIMIT to reduce sorting cost",
                expected_improvement="medium",
                priority=2
            ))
        
        return suggestions
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """获取优化报告"""
        with self._lock:
            slow_queries = self.analyzer.get_slow_queries()
            frequent_patterns = self.analyzer.get_frequent_patterns()
            
            report = {
                "timestamp": datetime.now(),
                "total_queries_analyzed": len(self.analyzer._query_history),
                "slow_queries_count": len(slow_queries),
                "frequent_patterns_count": len(frequent_patterns),
                "slowest_queries": [
                    {
                        "query": q.query_text,
                        "time": q.execution_time_ms,
                        "type": q.query_type.value
                    }
                    for q in sorted(slow_queries, key=lambda x: x.execution_time_ms, reverse=True)[:10]
                ],
                "top_patterns": [
                    {
                        "pattern": p.pattern,
                        "count": p.count,
                        "avg_time": p.avg_execution_time
                    }
                    for p in frequent_patterns[:10]
                ]
            }
            
            return report


_global_query_analyzer: Optional[QueryAnalyzer] = None
_global_query_optimizer: Optional[QueryOptimizer] = None


def get_query_analyzer() -> QueryAnalyzer:
    """获取全局查询分析器"""
    global _global_query_analyzer
    if _global_query_analyzer is None:
        _global_query_analyzer = QueryAnalyzer()
    return _global_query_analyzer


def get_query_optimizer() -> QueryOptimizer:
    """获取全局查询优化器"""
    global _global_query_optimizer
    if _global_query_optimizer is None:
        _global_query_optimizer = QueryOptimizer(get_query_analyzer())
    return _global_query_optimizer
