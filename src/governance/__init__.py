"""
记忆自治治理模块
基于第一性原理：动态遗忘、冲突解决、防投毒、版本管理、隔离控制
"""
from .governance import (
    MemoryGovernance,
    get_governance,
    ConflictResolver,
    get_conflict_resolver,
    PoisonDetector,
    get_poison_detector,
)

from .advanced_governance import (
    ForgetThresholds,
    get_forget_thresholds,
    AdaptiveForgetPolicy,
    get_adaptive_forget_policy,
)

from .version_manager import (
    VersionManager,
    get_version_manager,
    MemoryCorrection,
    get_memory_correction,
)

from .memory_isolation import (
    MemoryType,
    AccessLevel,
    MemoryIsolation,
    get_memory_isolation,
    MemorySwitch,
    get_memory_switch,
)

from .statistics import (
    StatisticsCollector,
    get_statistics_collector,
    AnomalyMarker,
    get_anomaly_marker,
)

from .auto_tasks import (
    TaskType,
    AutoTaskScheduler,
    get_auto_task_scheduler,
    ExperienceToRuleConverter,
    get_experience_converter,
)

__all__ = [
    # 基础治理
    'MemoryGovernance',
    'get_governance',
    'ConflictResolver',
    'get_conflict_resolver',
    'PoisonDetector',
    'get_poison_detector',
    
    # 遗忘策略
    'ForgetThresholds',
    'get_forget_thresholds',
    'AdaptiveForgetPolicy',
    'get_adaptive_forget_policy',
    
    # 版本管理
    'VersionManager',
    'get_version_manager',
    'MemoryCorrection',
    'get_memory_correction',
    
    # 隔离控制
    'MemoryType',
    'AccessLevel',
    'MemoryIsolation',
    'get_memory_isolation',
    'MemorySwitch',
    'get_memory_switch',
    
    # 统计监控
    'StatisticsCollector',
    'get_statistics_collector',
    'AnomalyMarker',
    'get_anomaly_marker',
    
    # 自动任务
    'TaskType',
    'AutoTaskScheduler',
    'get_auto_task_scheduler',
    'ExperienceToRuleConverter',
    'get_experience_converter',
]
