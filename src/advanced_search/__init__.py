"""
记忆系统高级搜索与语义理解
基于第一性原理：可扩展性、准确性、性能优化
"""

import math
import re
import time
import json
import hashlib
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, Counter
import heapq
from functools import lru_cache


class ScoringMethod(Enum):
    """评分方法"""
    TF_IDF = "tf_idf"
    BM25 = "bm25"
    COSINE = "cosine"
    JACCARD = "jaccard"
    HYBRID = "hybrid"


class SearchStrategy(Enum):
    """搜索策略"""
    EXACT_MATCH = "exact_match"
    KEYWORD_MATCH = "keyword_match"
    SEMANTIC_MATCH = "semantic_match"
    FTS = "full_text_search"
    FILTERED = "filtered"
    RERANKED = "reranked"


@dataclass
class SearchResult:
    """搜索结果"""
    memory_id: str
    content: str
    score: float
    rank: int
    highlight: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    explanation: Optional[str] = None


@dataclass
class SearchQuery:
    """搜索查询"""
    query: str
    filters: Dict[str, Any] = field(default_factory=dict)
    strategy: SearchStrategy = SearchStrategy.KEYWORD_MATCH
    scoring: ScoringMethod = ScoringMethod.TF_IDF
    limit: int = 10
    offset: int = 0
    threshold: float = 0.0


class Tokenizer:
    """文本分词器"""
    
    def __init__(self):
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 
            'for', 'of', 'by', 'with', 'is', 'are', 'was', 'were', 'be', 
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 
            'will', 'would', 'shall', 'should', 'can', 'could', 'may', 
            'might', 'must', 'dare', 'need', 'ought', 'used', 'the', 'a', 
            'an', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 
            'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 
            'your', 'his', 'its', 'our', 'their', 'mine', 'yours', 'hers', 
            'ours', 'theirs', 'myself', 'yourself', 'himself', 'herself', 
            'itself', 'ourselves', 'yourselves', 'themselves', 'what', 
            'which', 'who', 'whom', 'whose', 'where', 'when', 'why', 'how', 
            'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other', 
            'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 
            'than', 'too', 'very', 'just', 'also', 'now', 'here', 'there', 
            'then', 'once', 'if', 'about', 'after', 'again', 'against', 
            'is', 'it', 'its', 'it\'s'
        }
    
    def tokenize(self, text: str) -> List[str]:
        """分词"""
        # 转为小写
        text = text.lower()
        
        # 移除标点符号
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # 分割为单词
        tokens = text.split()
        
        # 移除停用词
        tokens = [token for token in tokens if token not in self.stop_words]
        
        return tokens
    
    def ngrams(self, text: str, n: int = 2) -> List[str]:
        """生成n-gram"""
        tokens = self.tokenize(text)
        if len(tokens) < n:
            return []
        return [' '.join(tokens[i:i+n]) for i in range(len(tokens)-n+1)]


class Vectorizer:
    """文本向量化器"""
    
    def __init__(self, tokenizer: Tokenizer = None):
        self.tokenizer = tokenizer or Tokenizer()
        self.vocab: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.doc_count: int = 0
    
    def fit(self, documents: List[str]) -> None:
        """拟合数据"""
        # 构建词汇表
        all_tokens = set()
        doc_freq: Dict[str, int] = defaultdict(int)
        
        for doc in documents:
            tokens = self.tokenizer.tokenize(doc)
            unique_tokens = set(tokens)
            for token in unique_tokens:
                doc_freq[token] += 1
            all_tokens.update(tokens)
        
        # 构建词汇表索引
        self.vocab = {token: idx for idx, token in enumerate(sorted(all_tokens))}
        self.doc_count = len(documents)
        
        # 计算IDF
        for token, freq in doc_freq.items():
            self.idf[token] = math.log(self.doc_count / (freq + 1)) + 1
    
    def transform(self, text: str) -> List[float]:
        """转换文本为向量"""
        tokens = self.tokenizer.tokenize(text)
        token_counts = Counter(tokens)
        max_freq = max(token_counts.values()) if token_counts else 1
        
        # 生成TF-IDF向量
        vector = [0.0] * len(self.vocab)
        for token, count in token_counts.items():
            if token in self.vocab:
                idx = self.vocab[token]
                tf = 0.5 + 0.5 * (count / max_freq)
                tfidf = tf * self.idf.get(token, 1.0)
                vector[idx] = tfidf
        
        return vector
    
    def get_bow(self, text: str) -> Dict[str, int]:
        """获取词袋模型"""
        tokens = self.tokenizer.tokenize(text)
        return Counter(tokens)


class Similarity:
    """相似度计算"""
    
    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        """余弦相似度"""
        dot_product = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    @staticmethod
    def jaccard_similarity(set1: Set[str], set2: Set[str]) -> float:
        """Jaccard相似度"""
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0
    
    @staticmethod
    def levenshtein_distance(s1: str, s2: str) -> int:
        """Levenshtein编辑距离"""
        if len(s1) < len(s2):
            return Similarity.levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    @staticmethod
    def dice_coefficient(s1: str, s2: str) -> float:
        """Dice系数"""
        if not s1 or not s2:
            return 0.0
        
        s1_ngrams = set(s1[i:i+2] for i in range(len(s1)-1))
        s2_ngrams = set(s2[i:i+2] for i in range(len(s2)-1))
        
        if not s1_ngrams and not s2_ngrams:
            return 1.0 if s1 == s2 else 0.0
        
        intersection = len(s1_ngrams & s2_ngrams)
        return 2.0 * intersection / (len(s1_ngrams) + len(s2_ngrams))


class BM25:
    """BM25排名算法"""
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_len: Dict[str, int] = {}
        self.avg_doc_len: float = 0
        self.doc_freq: Dict[str, int] = defaultdict(int)
        self.documents: List[Dict] = []
        self.tokenizer = Tokenizer()
    
    def fit(self, documents: List[Dict[str, Any]]) -> None:
        """拟合数据"""
        self.documents = documents
        total_len = 0
        
        for doc in documents:
            doc_id = doc.get('id', '')
            content = doc.get('content', '')
            tokens = self.tokenizer.tokenize(content)
            doc_len = len(tokens)
            self.doc_len[doc_id] = doc_len
            total_len += doc_len
            
            unique_tokens = set(tokens)
            for token in unique_tokens:
                self.doc_freq[token] += 1
        
        self.avg_doc_len = total_len / len(documents) if documents else 0
    
    def score(self, query: str, doc_index: int) -> float:
        """计算文档得分"""
        doc = self.documents[doc_index]
        doc_id = doc.get('id', '')
        doc_content = doc.get('content', '')
        
        query_tokens = self.tokenizer.tokenize(query)
        doc_tokens = self.tokenizer.tokenize(doc_content)
        doc_token_counts = Counter(doc_tokens)
        
        score = 0.0
        doc_len = self.doc_len.get(doc_id, 0)
        
        for token in query_tokens:
            if token not in self.doc_freq:
                continue
            
            q_tf = doc_token_counts.get(token, 0)
            doc_count = len(self.documents)
            df_t = self.doc_freq[token]
            
            idf = math.log((doc_count - df_t + 0.5) / (df_t + 0.5) + 1)
            numerator = q_tf * (self.k1 + 1)
            denominator = q_tf + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_len)
            score += idf * (numerator / denominator)
        
        return score


class IndexManager:
    """索引管理器"""
    
    def __init__(self):
        self.inverted_index: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
        self.forward_index: Dict[str, Dict] = {}
        self.vector_cache: Dict[str, List[float]] = {}
        self.tokenizer = Tokenizer()
        self.vectorizer = Vectorizer(self.tokenizer)
        self.cache_hits = 0
        self.cache_misses = 0
    
    def add_to_index(self, memory_id: str, content: str, metadata: Dict[str, Any] = None) -> None:
        """添加到索引"""
        metadata = metadata or {}
        
        # 添加到正向索引
        self.forward_index[memory_id] = {
            'id': memory_id,
            'content': content,
            'metadata': metadata,
            'tokens': self.tokenizer.tokenize(content)
        }
        
        # 添加到倒排索引
        tokens = self.tokenizer.tokenize(content)
        token_counts = Counter(tokens)
        max_freq = max(token_counts.values()) if token_counts else 1
        
        for token, count in token_counts.items():
            tf = count / max_freq
            self.inverted_index[token].append((memory_id, tf))
    
    def remove_from_index(self, memory_id: str) -> None:
        """从索引移除"""
        if memory_id not in self.forward_index:
            return
        
        # 移除正向索引
        doc = self.forward_index.pop(memory_id)
        tokens = doc.get('tokens', [])
        
        # 移除倒排索引
        for token in tokens:
            if token in self.inverted_index:
                self.inverted_index[token] = [
                    (mid, score) for mid, score in self.inverted_index[token] 
                    if mid != memory_id
                ]
                if not self.inverted_index[token]:
                    del self.inverted_index[token]
        
        # 清除缓存
        if memory_id in self.vector_cache:
            del self.vector_cache[memory_id]
    
    def update_vectorizer(self) -> None:
        """更新向量化器"""
        contents = [doc['content'] for doc in self.forward_index.values()]
        if contents:
            self.vectorizer.fit(contents)
    
    def get_cached_vector(self, memory_id: str) -> Optional[List[float]]:
        """获取缓存的向量"""
        if memory_id in self.vector_cache:
            self.cache_hits += 1
            return self.vector_cache[memory_id]
        self.cache_misses += 1
        return None
    
    def cache_vector(self, memory_id: str, vector: List[float]) -> None:
        """缓存向量"""
        self.vector_cache[memory_id] = vector


class SemanticSearchEngine:
    """语义搜索引擎"""
    
    def __init__(self):
        self.index = IndexManager()
        self.tokenizer = Tokenizer()
        self.bm25 = BM25()
        self.similarity = Similarity()
        self._fit_required = True
    
    def add_memory(self, memory_id: str, content: str, metadata: Dict[str, Any] = None) -> None:
        """添加记忆"""
        self.index.add_to_index(memory_id, content, metadata)
        self._fit_required = True
    
    def remove_memory(self, memory_id: str) -> None:
        """移除记忆"""
        self.index.remove_from_index(memory_id)
        self._fit_required = True
    
    def _ensure_fit(self) -> None:
        """确保已拟合"""
        if self._fit_required:
            docs = list(self.index.forward_index.values())
            if docs:
                self.bm25.fit(docs)
                self.index.update_vectorizer()
            self._fit_required = False
    
    def search(self, search_query: SearchQuery) -> List[SearchResult]:
        """执行搜索"""
        self._ensure_fit()
        
        if search_query.strategy == SearchStrategy.EXACT_MATCH:
            results = self._search_exact(search_query)
        elif search_query.strategy == SearchStrategy.KEYWORD_MATCH:
            results = self._search_keyword(search_query)
        elif search_query.strategy == SearchStrategy.SEMANTIC_MATCH:
            results = self._search_semantic(search_query)
        elif search_query.strategy == SearchStrategy.FTS:
            results = self._search_fts(search_query)
        elif search_query.strategy == SearchStrategy.FILTERED:
            results = self._search_filtered(search_query)
        elif search_query.strategy == SearchStrategy.RERANKED:
            results = self._search_reranked(search_query)
        else:
            results = self._search_keyword(search_query)
        
        return self._apply_threshold(results, search_query.threshold)
    
    def _search_exact(self, search_query: SearchQuery) -> List[SearchResult]:
        """精确匹配搜索"""
        query = search_query.query.lower()
        results = []
        
        for doc_id, doc in self.index.forward_index.items():
            content = doc['content'].lower()
            if query in content:
                score = 1.0
                results.append(SearchResult(
                    memory_id=doc_id,
                    content=doc['content'],
                    score=score,
                    rank=0,
                    metadata=doc.get('metadata', {})
                ))
        
        return self._rank_and_limit(results, search_query.limit)
    
    def _search_keyword(self, search_query: SearchQuery) -> List[SearchResult]:
        """关键词匹配搜索"""
        query = search_query.query
        query_tokens = self.tokenizer.tokenize(query)
        doc_scores: Dict[str, float] = defaultdict(float)
        
        if search_query.scoring == ScoringMethod.TF_IDF:
            doc_scores = self._score_tfidf(query_tokens)
        elif search_query.scoring == ScoringMethod.BM25:
            doc_scores = self._score_bm25(query)
        elif search_query.scoring == ScoringMethod.JACCARD:
            doc_scores = self._score_jaccard(query_tokens)
        elif search_query.scoring == ScoringMethod.HYBRID:
            doc_scores = self._score_hybrid(query, query_tokens)
        else:
            doc_scores = self._score_bm25(query)
        
        return self._build_results(doc_scores, search_query.limit)
    
    def _search_semantic(self, search_query: SearchQuery) -> List[SearchResult]:
        """语义匹配搜索"""
        query = search_query.query
        
        if not self.index.vectorizer.vocab:
            self._ensure_fit()
        
        query_vector = self.index.vectorizer.transform(query)
        doc_scores: Dict[str, float] = {}
        
        for doc_id, doc in self.index.forward_index.items():
            doc_vector = self.index.get_cached_vector(doc_id)
            if doc_vector is None:
                doc_vector = self.index.vectorizer.transform(doc['content'])
                self.index.cache_vector(doc_id, doc_vector)
            
            similarity = self.similarity.cosine_similarity(query_vector, doc_vector)
            doc_scores[doc_id] = similarity
        
        return self._build_results(doc_scores, search_query.limit)
    
    def _search_fts(self, search_query: SearchQuery) -> List[SearchResult]:
        """全文搜索"""
        return self._search_keyword(search_query)
    
    def _search_filtered(self, search_query: SearchQuery) -> List[SearchResult]:
        """过滤搜索"""
        base_results = self._search_keyword(search_query)
        
        filtered = []
        for result in base_results:
            match = True
            for key, value in search_query.filters.items():
                if result.metadata.get(key) != value:
                    match = False
                    break
            if match:
                filtered.append(result)
        
        return filtered[:search_query.limit]
    
    def _search_reranked(self, search_query: SearchQuery) -> List[SearchResult]:
        """重排序搜索"""
        base_results = self._search_keyword(search_query)
        return self._rerank(base_results, search_query.query)
    
    def _score_tfidf(self, query_tokens: List[str]) -> Dict[str, float]:
        """TF-IDF评分"""
        doc_scores: Dict[str, float] = defaultdict(float)
        
        for token in query_tokens:
            if token in self.index.inverted_index:
                postings = self.index.inverted_index[token]
                for doc_id, tf in postings:
                    idf = math.log(len(self.index.forward_index) / (len(postings) + 1))
                    doc_scores[doc_id] += tf * idf
        
        return doc_scores
    
    def _score_bm25(self, query: str) -> Dict[str, float]:
        """BM25评分"""
        doc_scores: Dict[str, float] = {}
        
        for idx, doc in enumerate(self.index.forward_index.values()):
            doc_id = doc['id']
            score = self.bm25.score(query, idx)
            doc_scores[doc_id] = score
        
        return doc_scores
    
    def _score_jaccard(self, query_tokens: List[str]) -> Dict[str, float]:
        """Jaccard评分"""
        doc_scores: Dict[str, float] = {}
        query_set = set(query_tokens)
        
        for doc_id, doc in self.index.forward_index.items():
            doc_tokens = doc.get('tokens', [])
            doc_set = set(doc_tokens)
            score = self.similarity.jaccard_similarity(query_set, doc_set)
            doc_scores[doc_id] = score
        
        return doc_scores
    
    def _score_hybrid(self, query: str, query_tokens: List[str]) -> Dict[str, float]:
        """混合评分"""
        bm25_scores = self._score_bm25(query)
        jaccard_scores = self._score_jaccard(query_tokens)
        
        doc_scores: Dict[str, float] = {}
        all_docs = set(bm25_scores.keys()) | set(jaccard_scores.keys())
        
        for doc_id in all_docs:
            bm25 = bm25_scores.get(doc_id, 0)
            jaccard = jaccard_scores.get(doc_id, 0)
            doc_scores[doc_id] = 0.7 * bm25 + 0.3 * jaccard
        
        return doc_scores
    
    def _rerank(self, results: List[SearchResult], query: str) -> List[SearchResult]:
        """重排序结果"""
        reranked = []
        for result in results:
            content = result.content
            # 使用Dice系数进行精排
            dice_score = self.similarity.dice_coefficient(query.lower(), content.lower())
            # 结合原始得分和重排得分
            final_score = 0.6 * result.score + 0.4 * dice_score
            reranked.append(SearchResult(
                memory_id=result.memory_id,
                content=result.content,
                score=final_score,
                rank=0,
                metadata=result.metadata
            ))
        
        return self._rank_and_limit(reranked, len(reranked))
    
    def _build_results(self, doc_scores: Dict[str, float], limit: int) -> List[SearchResult]:
        """构建搜索结果"""
        results = []
        for doc_id, score in doc_scores.items():
            if doc_id in self.index.forward_index:
                doc = self.index.forward_index[doc_id]
                results.append(SearchResult(
                    memory_id=doc_id,
                    content=doc['content'],
                    score=score,
                    rank=0,
                    metadata=doc.get('metadata', {})
                ))
        
        return self._rank_and_limit(results, limit)
    
    def _rank_and_limit(self, results: List[SearchResult], limit: int) -> List[SearchResult]:
        """排序和限制结果"""
        results.sort(key=lambda x: x.score, reverse=True)
        for idx, result in enumerate(results[:limit]):
            result.rank = idx + 1
        return results[:limit]
    
    def _apply_threshold(self, results: List[SearchResult], threshold: float) -> List[SearchResult]:
        """应用阈值"""
        if threshold <= 0:
            return results
        return [result for result in results if result.score >= threshold]
    
    def highlight(self, query: str, content: str) -> str:
        """高亮查询词"""
        query_tokens = self.tokenizer.tokenize(query.lower())
        result = content
        
        for token in query_tokens:
            pattern = re.compile(re.escape(token), re.IGNORECASE)
            result = pattern.sub(f'<mark>{token}</mark>', result)
        
        return result


class QueryAnalyzer:
    """查询分析器"""
    
    def __init__(self):
        self.tokenizer = Tokenizer()
        self.common_intents = {
            'how': 'question',
            'what': 'question',
            'why': 'question',
            'when': 'question',
            'where': 'question',
            'which': 'question',
            'who': 'question',
            'find': 'search',
            'search': 'search',
            'look': 'search',
            'remember': 'recall',
            'recall': 'recall',
            'get': 'retrieve',
            'show': 'retrieve'
        }
    
    def analyze(self, query: str) -> Dict[str, Any]:
        """分析查询"""
        tokens = self.tokenizer.tokenize(query)
        lower_query = query.lower()
        
        intent = 'neutral'
        for keyword, intent_type in self.common_intents.items():
            if keyword in lower_query:
                intent = intent_type
                break
        
        # 检测查询类型
        is_question = any(q in lower_query for q in ['?', 'how', 'what', 'why', 'when', 'where', 'which', 'who'])
        
        return {
            'query': query,
            'tokens': tokens,
            'intent': intent,
            'is_question': is_question,
            'complexity': min(1.0, len(tokens) / 10.0),
            'length': len(query)
        }
    
    def expand_query(self, query: str) -> List[str]:
        """查询扩展"""
        base_queries = [query]
        tokens = self.tokenizer.tokenize(query)
        
        # 添加n-gram变体
        for n in [2, 3]:
            base_queries.extend(self.tokenizer.ngrams(query, n))
        
        return base_queries


class EnhancedMemoryWithSearch:
    """增强的记忆系统（带高级搜索）"""
    
    def __init__(self):
        self.search_engine = SemanticSearchEngine()
        self.query_analyzer = QueryAnalyzer()
        self.memories: Dict[str, Dict] = {}
    
    def add(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """添加记忆"""
        import uuid
        memory_id = str(uuid.uuid4())
        self.memories[memory_id] = {
            'id': memory_id,
            'content': content,
            'metadata': metadata or {},
            'created_at': time.time()
        }
        self.search_engine.add_memory(memory_id, content, metadata)
        return memory_id
    
    def remove(self, memory_id: str) -> bool:
        """移除记忆"""
        if memory_id in self.memories:
            del self.memories[memory_id]
            self.search_engine.remove_memory(memory_id)
            return True
        return False
    
    def search(
        self, 
        query: str, 
        strategy: SearchStrategy = SearchStrategy.KEYWORD_MATCH,
        scoring: ScoringMethod = ScoringMethod.BM25,
        limit: int = 10,
        threshold: float = 0.0
    ) -> List[SearchResult]:
        """搜索记忆"""
        search_query = SearchQuery(
            query=query,
            strategy=strategy,
            scoring=scoring,
            limit=limit,
            threshold=threshold
        )
        return self.search_engine.search(search_query)
    
    def smart_search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """智能搜索"""
        analysis = self.query_analyzer.analyze(query)
        
        # 根据查询复杂度选择策略
        if analysis['complexity'] > 0.7:
            strategy = SearchStrategy.SEMANTIC_MATCH
            scoring = ScoringMethod.COSINE
        elif analysis['is_question']:
            strategy = SearchStrategy.RERANKED
            scoring = ScoringMethod.HYBRID
        else:
            strategy = SearchStrategy.KEYWORD_MATCH
            scoring = ScoringMethod.BM25
        
        return self.search(query, strategy, scoring, limit)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'total_memories': len(self.memories),
            'vocab_size': len(self.search_engine.index.vectorizer.vocab),
            'cache_hits': self.search_engine.index.cache_hits,
            'cache_misses': self.search_engine.index.cache_misses
        }


# 全局实例
_global_search_engine: Optional[SemanticSearchEngine] = None
_global_enhanced_memory: Optional[EnhancedMemoryWithSearch] = None


def get_search_engine() -> SemanticSearchEngine:
    """获取搜索引擎单例"""
    global _global_search_engine
    if _global_search_engine is None:
        _global_search_engine = SemanticSearchEngine()
    return _global_search_engine


def get_enhanced_memory() -> EnhancedMemoryWithSearch:
    """获取增强记忆系统单例"""
    global _global_enhanced_memory
    if _global_enhanced_memory is None:
        _global_enhanced_memory = EnhancedMemoryWithSearch()
    return _global_enhanced_memory
