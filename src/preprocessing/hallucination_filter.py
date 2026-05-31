"""
信息预处理模块 - 幻觉拦截
基于第一性原理：识别模型无依据输出、矛盾内容、虚假事实
"""
import re
from typing import List, Tuple


class HallucinationFilter:
    """幻觉内容过滤器"""
    
    def __init__(self):
        # 绝对化表述词（可能表示幻觉）
        self.absolute_words = [
            '绝对', '肯定', '一定', '必然', '肯定', '绝对是', 
            '百分之百', '100%', '绝对不', '从来不', '永远不'
        ]
        
        # 未验证的事实声明模式
        self.unverified_patterns = [
            r'据说',
            r'听说',
            r'据说',
            r'好像',
            r'大概是',
            r'可能是',
            r'我不确定',
            r'我不清楚',
        ]
        
        # 编译正则
        self.compiled_unverified = [
            re.compile(pattern) 
            for pattern in self.unverified_patterns
        ]
        
        # 自相矛盾的词对
        self.contradiction_pairs = [
            ('是', '不是'),
            ('有', '没有'),
            ('能', '不能'),
            ('可以', '不可以'),
        ]
    
    def is_hallucination(self, text: str) -> Tuple[bool, str]:
        """判断是否为幻觉内容，返回(是否幻觉, 原因)"""
        # 检查绝对化表述
        for word in self.absolute_words:
            if word in text:
                # 需要进一步验证，这里简化处理
                if '绝对' in word or '100%' in word or '永远' in word:
                    return True, f"包含绝对化表述: {word}"
        
        # 检查未验证声明
        for pattern in self.compiled_unverified:
            if pattern.search(text):
                return True, f"包含未验证声明"
        
        # 检查自相矛盾（简化版）
        if self._has_contradiction(text):
            return True, "包含自相矛盾内容"
        
        return False, ""
    
    def _has_contradiction(self, text: str) -> bool:
        """检查是否有自相矛盾"""
        for word1, word2 in self.contradiction_pairs:
            if word1 in text and word2 in text:
                return True
        return False
    
    def validate_fact(self, text: str, known_facts: List[str] = None) -> Tuple[bool, str]:
        """验证事实是否与已知事实冲突"""
        if known_facts is None:
            known_facts = []
        
        # 简化验证：检查是否包含已知事实中的否定
        for fact in known_facts:
            fact_lower = fact.lower()
            text_lower = text.lower()
            
            # 如果已知事实是"A是B"，但文本说"A不是B"
            if fact_lower in text_lower:
                # 检查是否有否定词
                if any(neg in text_lower for neg in ['不是', '不是', '非']):
                    return False, f"与已知事实冲突: {fact}"
        
        return True, ""
    
    def filter(self, text: str, known_facts: List[str] = None) -> Tuple[str, bool, str]:
        """
        过滤幻觉内容
        返回: (处理后文本, 是否通过, 原因)
        """
        is_hall, reason = self.is_hallucination(text)
        
        if is_hall:
            return text, False, reason
        
        if known_facts:
            valid, reason = self.validate_fact(text, known_facts)
            if not valid:
                return text, False, reason
        
        return text, True, ""


# 全局单例
_hallucination_filter = None


def get_hallucination_filter() -> HallucinationFilter:
    """获取幻觉过滤器"""
    global _hallucination_filter
    if _hallucination_filter is None:
        _hallucination_filter = HallucinationFilter()
    return _hallucination_filter
