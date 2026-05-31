"""
信息预处理模块 - 噪音过滤
基于第一性原理：剔除无意义闲聊、重复文本、空白字符
"""
import re
from typing import List, Set


class NoiseFilter:
    """噪音过滤器"""
    
    def __init__(self, min_length: int = 5):
        self.min_length = min_length
        
        # 无意义闲聊词库
        self.nonsense_patterns = [
            r'^哈哈+$',
            r'^嗯+$',
            r'^哦+$',
            r'^啊+$',
            r'^呀+$',
            r'^额+$',
            r'^[heh]+$',
            r'^[okOK]+$',
            r'^[好的]+$',
            r'^随便',
            r'^无所谓',
        ]
        
        # 编译正则
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in self.nonsense_patterns
        ]
    
    def is_noise(self, text: str) -> bool:
        """判断是否为噪音"""
        if not text or not text.strip():
            return True
        
        # 长度检查
        if len(text.strip()) < self.min_length:
            return True
        
        # 无意义闲聊检查
        for pattern in self.compiled_patterns:
            if pattern.match(text.strip()):
                return True
        
        # 重复内容检查
        if self._is_highly_repetitive(text):
            return True
        
        return False
    
    def _is_highly_repetitive(self, text: str) -> bool:
        """检查是否高度重复"""
        text = text.strip()
        if len(text) < 10:
            return False
        
        # 检查连续重复
        if len(set(text)) < len(text) * 0.3:
            return True
        
        return False
    
    def filter(self, texts: List[str]) -> List[str]:
        """批量过滤噪音"""
        return [text for text in texts if not self.is_noise(text)]
    
    def clean_text(self, text: str) -> str:
        """清理文本空白"""
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text)
        return text.strip()


# 全局单例
_noise_filter = None


def get_noise_filter() -> NoiseFilter:
    """获取噪音过滤器"""
    global _noise_filter
    if _noise_filter is None:
        _noise_filter = NoiseFilter()
    return _noise_filter
