"""
状态机
用于状态管理和转换
"""

import time
import threading
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class StateTransition:
    """状态转换"""
    from_state: str
    to_state: str
    event: str
    condition: Optional[Callable] = None
    action: Optional[Callable] = None


@dataclass
class State:
    """状态"""
    state_id: str
    name: str
    is_initial: bool = False
    is_final: bool = False
    entry_action: Optional[Callable] = None
    exit_action: Optional[Callable] = None


class StateMachine:
    """状态机"""
    
    def __init__(self, name: str):
        self.name = name
        self.states: Dict[str, State] = {}
        self.transitions: List[StateTransition] = []
        self.current_state: Optional[str] = None
        self._lock = threading.Lock()
    
    def add_state(
        self,
        state_id: str,
        name: str,
        is_initial: bool = False,
        is_final: bool = False,
        entry_action: Optional[Callable] = None,
        exit_action: Optional[Callable] = None
    ) -> str:
        """添加状态"""
        with self._lock:
            state = State(
                state_id=state_id,
                name=name,
                is_initial=is_initial,
                is_final=is_final,
                entry_action=entry_action,
                exit_action=exit_action
            )
            
            self.states[state_id] = state
            
            if is_initial:
                self.current_state = state_id
            
            return state_id
    
    def add_transition(
        self,
        from_state: str,
        to_state: str,
        event: str,
        condition: Optional[Callable] = None,
        action: Optional[Callable] = None
    ) -> bool:
        """添加转换"""
        if from_state not in self.states or to_state not in self.states:
            return False
        
        transition = StateTransition(
            from_state=from_state,
            to_state=to_state,
            event=event,
            condition=condition,
            action=action
        )
        
        self.transitions.append(transition)
        return True
    
    def trigger(self, event: str, context: Any = None) -> bool:
        """触发事件"""
        if not self.current_state:
            return False
        
        for transition in self.transitions:
            if (transition.from_state == self.current_state and
                transition.event == event):
                
                if transition.condition and not transition.condition(context):
                    continue
                
                current = self.states[self.current_state]
                if current.exit_action:
                    current.exit_action(context)
                
                self.current_state = transition.to_state
                
                new_state = self.states[transition.to_state]
                if new_state.entry_action:
                    new_state.entry_action(context)
                
                if transition.action:
                    transition.action(context)
                
                return True
        
        return False
    
    def get_current_state(self) -> Optional[str]:
        """获取当前状态"""
        return self.current_state
    
    def is_final_state(self) -> bool:
        """检查是否为终态"""
        if not self.current_state:
            return False
        return self.states[self.current_state].is_final
    
    def reset(self) -> bool:
        """重置状态机"""
        for state in self.states.values():
            if state.is_initial:
                self.current_state = state.state_id
                return True
        return False
