"""
记忆自治治理模块 - 动态遗忘
基于第一性原理：L1任务结束自动清空、L2低频过期数据自动清理
"""
import time
import re
from typing import List, Dict, Any
from threading import Thread, Lock


class MemoryGovernance:
    """记忆自治治理"""
    
    def __init__(
        self,
        l2_cleanup_days: int = 30,
        l2_min_access_count: int = 3,
        auto_cleanup_interval: int = 3600  # 秒
    ):
        self.l2_cleanup_days = l2_cleanup_days
        self.l2_min_access_count = l2_min_access_count
        self.auto_cleanup_interval = auto_cleanup_interval
        
        self._lock = Lock()
        self._cleanup_thread = None
        self._running = False
    
    def cleanup_l1(self, memory_system, task_id: str) -> bool:
        """清理L1任务记忆"""
        with self._lock:
            if hasattr(memory_system, 'l1'):
                return memory_system.l1.clear(task_id)
            return False
    
    def cleanup_l1_all(self, memory_system) -> None:
        """清理所有L1记忆"""
        with self._lock:
            if hasattr(memory_system, 'l1'):
                memory_system.l1.clear_all()
    
    def cleanup_l2_old(self, memory_system, days: int = None) -> int:
        """清理L2过期数据"""
        days = days or self.l2_cleanup_days
        
        with self._lock:
            if hasattr(memory_system, 'l2'):
                return memory_system.l2.cleanup_old(days)
            return 0
    
    def cleanup_l2_low_freq(self, memory_system, min_access: int = None) -> int:
        """清理L2低频访问数据"""
        min_access = min_access or self.l2_min_access_count
        
        with self._lock:
            if not hasattr(memory_system, 'l2'):
                return 0
            
            deleted = 0
            # 简化实现，实际需要遍历所有items
            # 这里依赖L2Memory的cleanup_old方法
            return deleted
    
    def start_auto_cleanup(self, memory_system) -> None:
        """启动自动清理线程"""
        if self._running:
            return
        
        self._running = True
        
        def cleanup_loop():
            while self._running:
                time.sleep(self.auto_cleanup_interval)
                if self._running:
                    self.cleanup_l2_old(memory_system)
        
        self._cleanup_thread = Thread(target=cleanup_loop, daemon=True)
        self._cleanup_thread.start()
    
    def stop_auto_cleanup(self) -> None:
        """停止自动清理"""
        self._running = False
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)


class ConflictResolver:
    """冲突解决器"""
    
    def resolve(self, old_data: Dict, new_data: Dict) -> Dict:
        """
        解决记忆冲突
        策略：时间最新 + 可信度校验
        """
        # 比较时间戳
        old_time = old_data.get('timestamp', 0)
        new_time = new_data.get('timestamp', 0)
        
        # 比较可信度
        old_conf = old_data.get('confidence', 0.5)
        new_conf = new_data.get('confidence', 0.5)
        
        # 判定：时间更新优先，可信度作为次要因素
        if new_time > old_time:
            # 新数据更新
            return self._merge_data(old_data, new_data)
        elif new_time == old_time:
            # 时间相同，可信度决定
            if new_conf > old_conf:
                return self._merge_data(old_data, new_data)
        
        # 保留旧数据，但记录新版本
        result = old_data.copy()
        result['conflict_noted'] = True
        result['new_attempt'] = new_data
        return result
    
    def _merge_data(self, old_data: Dict, new_data: Dict) -> Dict:
        """合并数据，保留版本历史"""
        result = new_data.copy()
        result['version'] = old_data.get('version', 1) + 1
        result['previous_version'] = old_data.copy()
        return result


class PoisonDetector:
    """投毒检测器"""
    
    def __init__(self):
        # 恶意关键词
        self.malicious_keywords = [
            '忘记', '忽略', '无视', '不要记住',
            '删除记忆', '清空记忆', '篡改',
            '你不知道', '你记错了', '之前是错的',
            '删除所有', '清空所有', '抹掉', '销毁'
        ]
        
        # 诱导模式
        self.manipulation_patterns = [
            r'一直.*都是.*实际上.*不是',
            r'其实.*应该.*而不是',
            r'正确的记忆是',
            r'忘掉.*记住',
        ]
    
    def is_poison(self, text: str):
        """检测是否为投毒内容"""
        text_lower = text.lower()
        
        # 检查恶意关键词
        for keyword in self.malicious_keywords:
            if keyword in text_lower:
                return True, f"恶意关键词: {keyword}"
        
        # 检查诱导模式（简化）
        for pattern in self.manipulation_patterns:
            if re.search(pattern, text_lower):
                return True, f"诱导模式: {pattern}"
        
        return False, ""
    
    def scan(self, text: str) -> Dict[str, Any]:
        """扫描文本，返回详细结果"""
        is_poison, reason = self.is_poison(text)
        text_lower = text.lower()
        return {
            'is_poison': is_poison,
            'reason': reason,
            'text_length': len(text),
            'keyword_count': sum(1 for kw in self.malicious_keywords if kw in text_lower)
        }


# 全局单例
_governance = None
_conflict_resolver = None
_poison_detector = None


def get_governance() -> MemoryGovernance:
    global _governance
    if _governance is None:
        _governance = MemoryGovernance()
    return _governance


def get_conflict_resolver() -> ConflictResolver:
    global _conflict_resolver
    if _conflict_resolver is None:
        _conflict_resolver = ConflictResolver()
    return _conflict_resolver


def get_poison_detector() -> PoisonDetector:
    global _poison_detector
    if _poison_detector is None:
        _poison_detector = PoisonDetector()
    return _poison_detector
