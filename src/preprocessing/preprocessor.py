"""
信息预处理模块 - 统一封装
基于第一性原理：噪音过滤、隐私脱敏、幻觉拦截、有效性校验
"""
from typing import Dict, Any, Optional
from .noise_filter import NoiseFilter, get_noise_filter
from .privacy_mask import PrivacyMask, get_privacy_mask
from .hallucination_filter import HallucinationFilter, get_hallucination_filter
from .validity_checker import ValidityChecker, get_validity_checker


class Preprocessor:
    """统一预处理模块"""
    
    def __init__(
        self,
        noise_filter: Optional[NoiseFilter] = None,
        privacy_mask: Optional[PrivacyMask] = None,
        hallucination_filter: Optional[HallucinationFilter] = None,
        validity_checker: Optional[ValidityChecker] = None
    ):
        self.noise_filter = noise_filter or get_noise_filter()
        self.privacy_mask = privacy_mask or get_privacy_mask()
        self.hallucination_filter = hallucination_filter or get_hallucination_filter()
        self.validity_checker = validity_checker or get_validity_checker()
    
    def process(self, text: str, check_hallucination: bool = False) -> Dict[str, Any]:
        """
        完整预处理流程
        返回详细的处理结果
        """
        result = {
            'original_text': text,
            'processed_text': text,
            'passed': True,
            'reasons': [],
            'stats': {
                'privacy_masked': {},
                'noise_removed': False,
                'hallucination_blocked': False,
                'validity_score': 0.0
            }
        }
        
        # 步骤1: 噪音过滤
        if self.noise_filter.is_noise(text):
            result['passed'] = False
            result['reasons'].append('噪音内容')
            result['stats']['noise_removed'] = True
            return result
        
        # 步骤2: 清理空白
        processed_text = self.noise_filter.clean_text(text)
        result['processed_text'] = processed_text
        
        # 步骤3: 隐私脱敏
        processed_text, mask_stats = self.privacy_mask.mask_all(processed_text)
        result['processed_text'] = processed_text
        result['stats']['privacy_masked'] = mask_stats
        
        # 步骤4: 幻觉拦截（可选）
        if check_hallucination:
            is_hall, hall_reason = self.hallucination_filter.is_hallucination(processed_text)
            if is_hall:
                result['passed'] = False
                result['reasons'].append(f'幻觉内容: {hall_reason}')
                result['stats']['hallucination_blocked'] = True
                return result
        
        # 步骤5: 有效性校验
        is_valid, invalid_reason, score = self.validity_checker.check(processed_text)
        result['stats']['validity_score'] = score
        
        if not is_valid:
            result['passed'] = False
            result['reasons'].append(f'无效内容: {invalid_reason}')
        
        return result
    
    def filter(self, text: str, check_hallucination: bool = False) -> str:
        """快速过滤，返回处理后的文本"""
        result = self.process(text, check_hallucination)
        if result['passed']:
            return result['processed_text']
        return ""
    
    def should_store(self, text: str, check_hallucination: bool = False) -> bool:
        """判断是否应该存储"""
        result = self.process(text, check_hallucination)
        return result['passed']


# 全局单例
_preprocessor = None


def get_preprocessor() -> Preprocessor:
    """获取预处理器"""
    global _preprocessor
    if _preprocessor is None:
        _preprocessor = Preprocessor()
    return _preprocessor
