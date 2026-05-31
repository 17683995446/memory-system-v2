"""
第40阶段测试：记忆系统高级搜索与语义理解
遵循"图难于其易，为大于其细"原则
"""

import sys
import os
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.advanced_search import (
    Tokenizer,
    Vectorizer,
    Similarity,
    BM25,
    SearchResult,
    SearchQuery,
    SearchStrategy,
    ScoringMethod,
    SemanticSearchEngine,
    QueryAnalyzer,
    EnhancedMemoryWithSearch,
    get_enhanced_memory
)


def test_tokenizer():
    """测试分词器"""
    print("\n=== 测试分词器")
    
    tokenizer = Tokenizer()
    
    text = "The quick brown fox jumps over the lazy dog"
    tokens = tokenizer.tokenize(text)
    
    assert len(tokens) > 0, "应该生成分词"
    assert 'quick' in tokens, "应该包含关键单词"
    assert 'the' not in tokens, "应该移除停用词"
    
    print(f"分词结果: {tokens}")
    print("✓ 分词器测试通过")


def test_vectorizer():
    """测试向量化器"""
    print("\n=== 测试向量化器")
    
    tokenizer = Tokenizer()
    vectorizer = Vectorizer(tokenizer)
    
    documents = [
        "The quick brown fox jumps over the lazy dog",
        "A quick brown fox jumps over the lazy dog",
        "The quick brown fox jumps over the sleeping dog",
    ]
    
    vectorizer.fit(documents)
    assert len(vectorizer.vocab) > 0, "应该建立词汇表"
    
    vector = vectorizer.transform("quick brown fox")
    assert len(vector) == len(vectorizer.vocab), "向量长度应该等于词汇表大小"
    assert any(v > 0 for v in vector), "应该有非零值"
    
    print(f"词汇表大小: {len(vectorizer.vocab)}")
    print(f"向量长度: {len(vector)}")
    print("✓ 向量化器测试通过")


def test_similarity():
    """测试相似度计算"""
    print("\n=== 测试相似度计算")
    
    similarity = Similarity()
    
    # 余弦相似度
    v1 = [1.0, 0.0, 1.0]
    v2 = [1.0, 1.0, 0.0]
    cos_sim = similarity.cosine_similarity(v1, v2)
    assert 0 < cos_sim < 1, "余弦相似度应该在0-1之间"
    
    # Jaccard相似度
    s1 = {'quick', 'brown', 'fox'}
    s2 = {'quick', 'lazy', 'dog'}
    jaccard = similarity.jaccard_similarity(s1, s2)
    assert 0 <= jaccard <= 1, "Jaccard相似度应该在0-1之间"
    
    # Levenshtein距离
    dist = similarity.levenshtein_distance("kitten", "sitting")
    assert dist == 3, "编辑距离应该正确"
    
    # Dice系数
    dice = similarity.dice_coefficient("hello", "helloworld")
    assert 0 <= dice <= 1, "Dice系数应该在0-1之间"
    
    print(f"余弦相似度: {cos_sim:.2f}")
    print(f"Jaccard相似度: {jaccard:.2f}")
    print(f"Levenshtein距离: {dist}")
    print(f"Dice系数: {dice:.2f}")
    print("✓ 相似度计算测试通过")


def test_bm25():
    """测试BM25算法"""
    print("\n=== 测试BM25算法")
    
    bm25 = BM25()
    
    documents = [
        {'id': '1', 'content': "The quick brown fox jumps over the lazy dog"},
        {'id': '2', 'content': "A quick brown fox jumps over the sleeping dog"},
        {'id': '3', 'content': "The lazy dog sleeps all day"},
    ]
    
    bm25.fit(documents)
    assert len(bm25.documents) == 3, "应该有3个文档"
    
    score1 = bm25.score("quick fox", 0)
    score2 = bm25.score("quick fox", 1)
    score3 = bm25.score("lazy dog", 2)
    
    assert score1 > 0, "应该有正向得分"
    assert score3 > 0, "应该有正向得分"
    
    print(f"文档1得分: {score1:.2f}")
    print(f"文档2得分: {score2:.2f}")
    print(f"文档3得分: {score3:.2f}")
    print("✓ BM25算法测试通过")


def test_search_engine():
    """测试搜索引擎"""
    print("\n=== 测试搜索引擎")
    
    engine = SemanticSearchEngine()
    
    # 添加记忆
    memories = [
        "Python is a programming language",
        "Machine learning is a subset of artificial intelligence",
        "The Python programming language is great for data science",
        "Artificial intelligence and machine learning are important fields",
        "Data science uses Python and machine learning",
    ]
    
    for idx, content in enumerate(memories):
        memory_id = f"mem_{idx}"
        engine.add_memory(memory_id, content, {'index': idx})
    
    # 测试关键词搜索
    query = SearchQuery(
        query="Python",
        strategy=SearchStrategy.KEYWORD_MATCH,
        scoring=ScoringMethod.BM25,
        limit=5
    )
    
    results = engine.search(query)
    assert len(results) > 0, "应该返回结果"
    print(f"关键词搜索 'Python' 返回 {len(results)} 个结果")
    
    for result in results[:3]:
        print(f"  #{result.rank} 得分: {result.score:.2f} - {result.content[:50]}")
    
    # 测试语义搜索
    query2 = SearchQuery(
        query="programming language",
        strategy=SearchStrategy.SEMANTIC_MATCH,
        scoring=ScoringMethod.COSINE,
        limit=5
    )
    
    results2 = engine.search(query2)
    assert len(results2) > 0, "应该返回结果"
    print(f"语义搜索 'programming language' 返回 {len(results2)} 个结果")
    
    # 测试精确搜索
    query3 = SearchQuery(
        query="Python is a programming",
        strategy=SearchStrategy.EXACT_MATCH,
        limit=5
    )
    
    results3 = engine.search(query3)
    assert len(results3) > 0, "应该返回结果"
    print(f"精确搜索返回 {len(results3)} 个结果")
    
    print("✓ 搜索引擎测试通过")


def test_query_analyzer():
    """测试查询分析器"""
    print("\n=== 测试查询分析器")
    
    analyzer = QueryAnalyzer()
    
    # 测试查询分析
    analysis1 = analyzer.analyze("What is machine learning?")
    assert analysis1['is_question'], "应该识别为问题"
    assert analysis1['intent'] == 'question', "应该识别意图"
    
    analysis2 = analyzer.analyze("Find information about Python")
    assert analysis2['intent'] == 'search', "应该识别为搜索意图"
    
    print(f"查询分析结果1: {analysis1}")
    print(f"查询分析结果2: {analysis2}")
    
    # 测试查询扩展
    expansions = analyzer.expand_query("machine learning")
    assert len(expansions) > 1, "应该有查询扩展"
    print(f"查询扩展: {expansions}")
    
    print("✓ 查询分析器测试通过")


def test_enhanced_memory():
    """测试增强记忆系统"""
    print("\n=== 测试增强记忆系统")
    
    memory = EnhancedMemoryWithSearch()
    
    # 添加记忆
    contents = [
        "The Earth is the third planet from the Sun",
        "Mars is known as the Red Planet",
        "Jupiter is the largest planet in our solar system",
        "Saturn has beautiful rings around it",
        "Venus is the hottest planet in our solar system",
    ]
    
    for content in contents:
        memory.add(content, {'category': 'astronomy'})
    
    # 测试基础搜索
    results = memory.search("planet", SearchStrategy.KEYWORD_MATCH)
    assert len(results) > 0, "应该返回结果"
    print(f"基础搜索返回 {len(results)} 个结果")
    
    # 测试智能搜索
    smart_results = memory.smart_search("What is the largest planet?")
    assert len(smart_results) > 0, "应该返回结果"
    print(f"智能搜索返回 {len(smart_results)} 个结果")
    
    for result in smart_results:
        print(f"  #{result.rank} 得分: {result.score:.2f} - {result.content}")
    
    # 测试不同评分方法
    tfidf_results = memory.search(
        "planet rings", 
        SearchStrategy.KEYWORD_MATCH, 
        ScoringMethod.TF_IDF
    )
    
    hybrid_results = memory.search(
        "planet rings", 
        SearchStrategy.KEYWORD_MATCH, 
        ScoringMethod.HYBRID
    )
    
    print(f"TF-IDF搜索: {len(tfidf_results)} 结果")
    print(f"混合搜索: {len(hybrid_results)} 结果")
    
    # 测试统计信息
    stats = memory.get_statistics()
    assert stats['total_memories'] == 5, "应该有5个记忆"
    print(f"统计信息: {stats}")
    
    print("✓ 增强记忆系统测试通过")


def test_search_strategies():
    """测试不同搜索策略"""
    print("\n=== 测试不同搜索策略")
    
    memory = EnhancedMemoryWithSearch()
    
    # 添加测试数据
    test_data = [
        "Cats like to eat fish and sleep in the sun",
        "Dogs enjoy playing fetch and going for walks",
        "Birds can fly and build nests in trees",
        "Fish live in water and swim around",
    ]
    
    for data in test_data:
        memory.add(data)
    
    strategies = [
        SearchStrategy.EXACT_MATCH,
        SearchStrategy.KEYWORD_MATCH,
        SearchStrategy.SEMANTIC_MATCH,
        SearchStrategy.RERANKED,
    ]
    
    for strategy in strategies:
        results = memory.search("fish", strategy=strategy)
        print(f"{strategy.value}: {len(results)} 结果")
    
    print("✓ 搜索策略测试通过")


def test_highlights():
    """测试高亮功能"""
    print("\n=== 测试高亮功能")
    
    engine = SemanticSearchEngine()
    engine.add_memory("mem_1", "The quick brown fox jumps over the lazy dog", {})
    
    highlighted = engine.highlight("fox jumps", "The quick brown fox jumps over the lazy dog")
    
    assert '<mark>' in highlighted, "应该包含高亮标签"
    print(f"高亮结果: {highlighted}")
    print("✓ 高亮功能测试通过")


def test_global_instance():
    """测试全局实例"""
    print("\n=== 测试全局实例")
    
    mem1 = get_enhanced_memory()
    mem2 = get_enhanced_memory()
    
    assert mem1 is mem2, "应该是同一个实例"
    print("✓ 全局实例测试通过")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("第40阶段测试：记忆系统高级搜索与语义理解")
    print("遵循原则：图难于其易，为大于其细")
    print("=" * 60)
    
    try:
        test_tokenizer()
        test_vectorizer()
        test_similarity()
        test_bm25()
        test_search_engine()
        test_query_analyzer()
        test_enhanced_memory()
        test_search_strategies()
        test_highlights()
        test_global_instance()
        
        print("\n" + "=" * 60)
        print("✓ 所有第40阶段测试通过！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
