"""
基于第一性原理的Agent可靠记忆系统

本系统采用三层记忆架构，提供确定性的记忆存储、召回和治理能力。

核心特点：
- 三层记忆架构：L1瞬时记忆、L2情景记忆、L3事实记忆
- 确定性设计：核心逻辑全部硬编码，拒绝模型概率随机性
- 安全防护：防投毒、隐私脱敏、记忆隔离
- 自治治理：动态遗忘、冲突解决、版本管理
- 复盘迭代：任务复盘、经验提取、权重优化

作者: Memory System Team
版本: 1.0.0
创建: 2026-05-25
"""

from .memory.memory_system import MemorySystem, get_memory_system
from .config.settings import Settings, get_settings
from .preprocessing import get_preprocessor
from .governance import (
    get_governance,
    get_conflict_resolver,
    get_poison_detector,
    get_forget_thresholds,
    get_adaptive_forget_policy,
    get_version_manager,
    get_memory_correction,
    get_memory_isolation,
    get_memory_switch,
    get_statistics_collector,
    get_anomaly_marker,
    get_auto_task_scheduler,
    get_experience_converter,
)
from .iteration import get_reviewer, get_experience_extractor, get_weight_optimizer

__version__ = "1.0.0"
__all__ = [
    "MemorySystem",
    "get_memory_system",
    "Settings",
    "get_settings",
    "get_preprocessor",
    "get_governance",
    "get_conflict_resolver",
    "get_poison_detector",
    "get_forget_thresholds",
    "get_adaptive_forget_policy",
    "get_version_manager",
    "get_memory_correction",
    "get_memory_isolation",
    "get_memory_switch",
    "get_statistics_collector",
    "get_anomaly_marker",
    "get_auto_task_scheduler",
    "get_experience_converter",
    "get_reviewer",
    "get_experience_extractor",
    "get_weight_optimizer",
]
