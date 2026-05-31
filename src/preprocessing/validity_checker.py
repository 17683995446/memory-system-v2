"""
信息预处理模块 - 有效性校验
基于第一性原理：判断信息是否具备复用价值
"""
import re
from typing import Tuple


class ValidityChecker:
    """有效性校验器"""
    
    def __init__(self, min_value_length: int = 10):
        self.min_value_length = min_value_length
        
        # 无价值内容模式
        self.no_value_patterns = [
            r'^测试',
            r'^test',
            r'^调试',
            r'^\d+$',  # 纯数字
            r'^[a-zA-Z]+$',  # 纯字母
        ]
        
        # 有价值关键词
        self.value_keywords = [
            '任务', '问题', '解决', '方法', '步骤', '结果',
            '用户', '系统', '功能', '规则', '设置', '配置',
            '错误', '成功', '失败', '完成', '处理', '调用'
        ]
        
        self.compiled_no_value = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in self.no_value_patterns
        ]
    
    def has_value(self, text: str) -> Tuple[bool, str]:
        """判断是否有复用价值，返回(是否有价值, 原因)"""
        if not text or not text.strip():
            return False, "空文本"
        
        text = text.strip()
        
        # 长度检查
        if len(text) < self.min_value_length:
            return False, f"文本过短: {len(text)} < {self.min_value_length}"
        
        # 无价值模式检查
        for pattern in self.compiled_no_value:
            if pattern.match(text):
                return False, "匹配无价值模式"
        
        # 有价值关键词检查
        has_keyword = any(kw in text for kw in self.value_keywords)
        if not has_keyword:
            return False, "缺少有价值关键词"
        
        return True, ""
    
    def calculate_value_score(self, text: str) -> float:
        """计算价值分数 (0-1)"""
        if not text or not text.strip():
            return 0.0
        
        text = text.strip()
        score = 0.5  # 基础分
        
        # 长度加分
        length = len(text)
        if length > 50:
            score += 0.2
        elif length > 20:
            score += 0.1
        
        # 关键词加分
        keyword_count = sum(1 for kw in self.value_keywords if kw in text)
        if keyword_count >= 3:
            score += 0.2
        elif keyword_count >= 1:
            score += 0.1
        
        # 包含数字或具体信息加分
        if re.search(r'\d+', text):
            score += 0.1
        
        # 包含中文加分
        chinese_count = len(re.findall(r'[\u4e00-\u9fff]', text))
        if chinese_count > 5:
            score += 0.1
        
        return min(score, 1.0)
    
    def check(self, text: str, min_score: float = 0.5) -> Tuple[bool, str, float]:
        """
        综合检查有效性
        返回: (是否有效, 原因, 价值分数)
        """
        has_val, reason = self.has_value(text)
        
        if not has_val:
            return False, reason, 0.0
        
        score = self.calculate_value_score(text)
        
        if score < min_score:
            return False, f"价值分数过低: {score:.2f} < {min_score}", score
        
        return True, "", score


# 全局单例
_validity_checker = None


def get_validity_checker() -> ValidityChecker:
    """获取有效性校验器"""
    global _validity_checker
    if _validity_checker is None:
        _validity_checker = ValidityChecker()
    return _validity_checker
