"""
A/B测试框架
用于实验和对照测试
"""

import time
import threading
import random
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Experiment:
    """实验"""
    experiment_id: str
    name: str
    variants: Dict[str, Callable]
    weights: Dict[str, float]
    enabled: bool = True


@dataclass
class ExperimentResult:
    """实验结果"""
    experiment_id: str
    variant: str
    user_id: str
    timestamp: datetime
    converted: bool = False


class ABTestingFramework:
    """A/B测试框架"""
    
    def __init__(self):
        self.experiments: Dict[str, Experiment] = {}
        self.results: Dict[str, ExperimentResult] = []
        self._experiment_counter: int = 0
        self._lock = threading.Lock()
    
    def create_experiment(
        self,
        name: str,
        variants: Dict[str, Callable],
        weights: Dict[str, float]
    ) -> str:
        """创建实验"""
        with self._lock:
            self._experiment_counter += 1
            experiment_id = f"EXP-{self._experiment_counter:06d}"
            
            experiment = Experiment(
                experiment_id=experiment_id,
                name=name,
                variants=variants,
                weights=weights
            )
            
            self.experiments[experiment_id] = experiment
            return experiment_id
    
    def get_variant(self, experiment_id: str, user_id: str) -> Optional[str]:
        """获取用户对应的变体"""
        if experiment_id not in self.experiments:
            return None
        
        experiment = self.experiments[experiment_id]
        if not experiment.enabled:
            return None
        
        variant_names = list(experiment.weights.keys())
        variant_weights = list(experiment.weights.values())
        
        random.seed(hash(user_id))
        variant_index = random.choices(
            range(len(variant_names)),
            weights=variant_weights
        )[0]
        
        return variant_names[variant_index]
    
    def execute_variant(
        self,
        experiment_id: str,
        user_id: str,
        context: Any
    ) -> Any:
        """执行变体"""
        variant = self.get_variant(experiment_id, user_id)
        if not variant:
            return None
        
        experiment = self.experiments[experiment_id]
        if variant not in experiment.variants:
            return None
        
        result = ExperimentResult(
            experiment_id=experiment_id,
            variant=variant,
            user_id=user_id,
            timestamp=datetime.now()
        )
        
        with self._lock:
            self.results.append(result)
        
        return experiment.variants[variant](context)
    
    def record_conversion(
        self,
        experiment_id: str,
        user_id: str
    ) -> bool:
        """记录转化"""
        with self._lock:
            for result in self.results:
                if (result.experiment_id == experiment_id and
                    result.user_id == user_id and
                    not result.converted):
                    result.converted = True
                    return True
            return False
    
    def get_experiment_stats(self, experiment_id: str) -> Dict[str, Any]:
        """获取实验统计"""
        if experiment_id not in self.experiments:
            return {}
        
        results = [r for r in self.results if r.experiment_id == experiment_id]
        
        stats = {}
        for variant in self.experiments[experiment_id].variants.keys():
            variant_results = [r for r in results if r.variant == variant]
            total = len(variant_results)
            converted = sum(1 for r in variant_results if r.converted)
            
            stats[variant] = {
                "total": total,
                "converted": converted,
                "rate": (converted / total * 100) if total > 0 else 0
            }
        
        return stats


_global_ab_framework: Optional[ABTestingFramework] = None


def get_ab_testing_framework() -> ABTestingFramework:
    """获取全局A/B测试框架"""
    global _global_ab_framework
    if _global_ab_framework is None:
        _global_ab_framework = ABTestingFramework()
    return _global_ab_framework
