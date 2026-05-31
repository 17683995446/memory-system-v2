"""
规则引擎
用于业务规则执行
"""

import time
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Rule:
    """规则"""
    rule_id: str
    name: str
    condition: Callable[[Any], bool]
    action: Callable[[Any], Any]
    priority: int = 0
    enabled: bool = True


@dataclass
class RuleResult:
    """规则执行结果"""
    rule_id: str
    rule_name: str
    matched: bool
    action_executed: bool
    result: Any


class RuleEngine:
    """规则引擎"""
    
    def __init__(self):
        self.rules: Dict[str, Rule] = {}
        self._rule_counter: int = 0
        self._lock = threading.Lock()
    
    def add_rule(
        self,
        name: str,
        condition: Callable[[Any], bool],
        action: Callable[[Any], Any],
        priority: int = 0
    ) -> str:
        """添加规则"""
        with self._lock:
            self._rule_counter += 1
            rule_id = f"RULE-{self._rule_counter:06d}"
            
            rule = Rule(
                rule_id=rule_id,
                name=name,
                condition=condition,
                action=action,
                priority=priority
            )
            
            self.rules[rule_id] = rule
            return rule_id
    
    def evaluate(self, context: Any) -> List[RuleResult]:
        """评估规则"""
        results = []
        
        sorted_rules = sorted(
            self.rules.values(),
            key=lambda r: r.priority,
            reverse=True
        )
        
        for rule in sorted_rules:
            if not rule.enabled:
                continue
            
            try:
                matched = rule.condition(context)
                result = RuleResult(
                    rule_id=rule.rule_id,
                    rule_name=rule.name,
                    matched=matched,
                    action_executed=False,
                    result=None
                )
                
                if matched:
                    action_result = rule.action(context)
                    result.action_executed = True
                    result.result = action_result
                
                results.append(result)
            except Exception:
                pass
        
        return results
    
    def enable_rule(self, rule_id: str) -> bool:
        """启用规则"""
        if rule_id not in self.rules:
            return False
        self.rules[rule_id].enabled = True
        return True
    
    def disable_rule(self, rule_id: str) -> bool:
        """禁用规则"""
        if rule_id not in self.rules:
            return False
        self.rules[rule_id].enabled = False
        return True
    
    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """获取规则"""
        return self.rules.get(rule_id)


_global_rule_engine: Optional[RuleEngine] = None


def get_rule_engine() -> RuleEngine:
    """获取全局规则引擎"""
    global _global_rule_engine
    if _global_rule_engine is None:
        _global_rule_engine = RuleEngine()
    return _global_rule_engine
