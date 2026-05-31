"""
高级记忆自治治理系统 - 遗忘量化阈值配置
基于第一性原理：时间+频次双维度遗忘量化
"""
import time
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class ForgetThresholds:
    """遗忘量化阈值"""
    # 时间维度
    l1_ttl_seconds: int = 3600  # L1: 1小时
    l2_max_days: int = 30  # L2: 30天
    l3_max_days: int = 3650  # L3: 10年
    
    # 频次维度
    l2_min_access_count: int = 3  # L2最低访问次数
    l2_access_decay_days: int = 7  # 访问衰减周期
    
    # 复合条件（时间AND频次）
    use_compound_threshold: bool = True  # 是否使用复合条件
    
    def should_forget_l1(self, last_access: float) -> bool:
        """判断L1是否应该遗忘"""
        return time.time() - last_access > self.l1_ttl_seconds
    
    def should_forget_l2(self, last_access: float, access_count: int) -> bool:
        """判断L2是否应该遗忘（双维度复合判断）"""
        days_since_access = (time.time() - last_access) / 86400
        
        if self.use_compound_threshold:
            # 复合条件：时间过长 或 访问频次过低
            time_expired = days_since_access > self.l2_max_days
            low_freq = access_count < self.l2_min_access_count and days_since_access > self.l2_access_decay_days
            return time_expired or low_freq
        else:
            # 单一条件：时间过长
            return days_since_access > self.l2_max_days
    
    def should_forget_l3(self, last_access: float) -> bool:
        """判断L3是否应该遗忘（仅人工）"""
        days_since_access = (time.time() - last_access) / 86400
        return days_since_access > self.l3_max_days


class AdaptiveForgetPolicy:
    """自适应遗忘策略"""
    
    def __init__(self, thresholds: ForgetThresholds = None):
        self.thresholds = thresholds or ForgetThresholds()
        self._history: List[Dict] = []
    
    def calculate_forget_priority(self, item: Dict) -> float:
        """计算遗忘优先级（0-1，越高越应该遗忘）"""
        last_access = item.get('last_access', time.time())
        access_count = item.get('access_count', 0)
        days_since_access = (time.time() - last_access) / 86400
        
        # 时间因子
        time_factor = min(days_since_access / self.thresholds.l2_max_days, 1.0)
        
        # 频次因子
        freq_factor = max(0, 1.0 - access_count / self.thresholds.l2_min_access_count)
        
        # 综合遗忘优先级
        priority = time_factor * 0.6 + freq_factor * 0.4
        
        return priority
    
    def should_forget(self, memory_level: str, item: Dict) -> Tuple[bool, str]:
        """判断是否应该遗忘"""
        if memory_level == 'l1':
            last_access = item.get('timestamp', time.time())
            if self.thresholds.should_forget_l1(last_access):
                return True, "时间过期"
        
        elif memory_level == 'l2':
            last_access = item.get('last_access', time.time())
            access_count = item.get('access_count', 0)
            if self.thresholds.should_forget_l2(last_access, access_count):
                priority = self.calculate_forget_priority(item)
                reason = f"遗忘优先级: {priority:.2f}"
                return True, reason
        
        return False, ""
    
    def record_forget_event(self, item_id: str, memory_level: str, reason: str) -> None:
        """记录遗忘事件"""
        self._history.append({
            'timestamp': time.time(),
            'item_id': item_id,
            'memory_level': memory_level,
            'reason': reason
        })
    
    def get_forget_history(self, limit: int = 100) -> List[Dict]:
        """获取遗忘历史"""
        return self._history[-limit:]


# 全局单例
_forget_thresholds = None
_adaptive_forget_policy = None


def get_forget_thresholds() -> ForgetThresholds:
    """获取遗忘阈值"""
    global _forget_thresholds
    if _forget_thresholds is None:
        _forget_thresholds = ForgetThresholds()
    return _forget_thresholds


def get_adaptive_forget_policy() -> AdaptiveForgetPolicy:
    """获取自适应遗忘策略"""
    global _adaptive_forget_policy
    if _adaptive_forget_policy is None:
        _adaptive_forget_policy = AdaptiveForgetPolicy()
    return _adaptive_forget_policy
