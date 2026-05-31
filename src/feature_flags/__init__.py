"""
特性开关系统
用于功能发布控制
"""

import time
import threading
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Feature:
    """特性"""
    feature_id: str
    name: str
    description: str
    enabled: bool = False
    rollout_percentage: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class FeatureFlagManager:
    """特性开关管理器"""
    
    def __init__(self):
        self.features: Dict[str, Feature] = {}
        self._feature_counter: int = 0
        self._lock = threading.Lock()
    
    def add_feature(
        self,
        name: str,
        description: str,
        rollout_percentage: int = 0
    ) -> str:
        """添加特性"""
        with self._lock:
            self._feature_counter += 1
            feature_id = f"FEATURE-{self._feature_counter:06d}"
            
            feature = Feature(
                feature_id=feature_id,
                name=name,
                description=description,
                rollout_percentage=rollout_percentage
            )
            
            self.features[name] = feature
            return feature_id
    
    def enable_feature(self, name: str) -> bool:
        """启用特性"""
        if name not in self.features:
            return False
        self.features[name].enabled = True
        return True
    
    def disable_feature(self, name: str) -> bool:
        """禁用特性"""
        if name not in self.features:
            return False
        self.features[name].enabled = False
        return True
    
    def is_enabled(self, name: str, user_id: Optional[str] = None) -> bool:
        """检查特性是否启用"""
        if name not in self.features:
            return False
        
        feature = self.features[name]
        
        if feature.enabled:
            if feature.rollout_percentage >= 100:
                return True
            elif feature.rollout_percentage > 0 and user_id:
                import hashlib
                hash_value = int(hashlib.md5(f"{name}:{user_id}".encode()).hexdigest(), 16)
                return (hash_value % 100) < feature.rollout_percentage
        
        return False
    
    def set_rollout_percentage(self, name: str, percentage: int) -> bool:
        """设置灰度发布百分比"""
        if name not in self.features:
            return False
        self.features[name].rollout_percentage = max(0, min(100, percentage))
        return True
    
    def get_feature(self, name: str) -> Optional[Feature]:
        """获取特性"""
        return self.features.get(name)


_global_feature_flags: Optional[FeatureFlagManager] = None


def get_feature_flag_manager() -> FeatureFlagManager:
    """获取全局特性开关管理器"""
    global _global_feature_flags
    if _global_feature_flags is None:
        _global_feature_flags = FeatureFlagManager()
    return _global_feature_flags
