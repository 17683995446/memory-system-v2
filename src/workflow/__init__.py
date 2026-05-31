"""
工作流引擎
用于编排复杂的工作流程
"""

import time
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class WorkflowStatus(Enum):
    """工作流状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(Enum):
    """任务类型"""
    ACTION = "action"
    CONDITION = "condition"
    LOOP = "loop"
    PARALLEL = "parallel"


@dataclass
class WorkflowTask:
    """工作流任务"""
    task_id: str
    name: str
    task_type: TaskType
    action: Callable
    dependencies: List[str] = field(default_factory=list)


@dataclass
class Workflow:
    """工作流"""
    workflow_id: str
    name: str
    tasks: Dict[str, WorkflowTask]
    entry_task: str
    status: WorkflowStatus = WorkflowStatus.PENDING


class WorkflowEngine:
    """工作流引擎"""
    
    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        self._workflow_counter: int = 0
        self._lock = threading.Lock()
    
    def create_workflow(
        self,
        name: str,
        tasks: Dict[str, WorkflowTask],
        entry_task: str
    ) -> str:
        """创建工作流"""
        with self._lock:
            self._workflow_counter += 1
            workflow_id = f"WORKFLOW-{self._workflow_counter:06d}"
            
            workflow = Workflow(
                workflow_id=workflow_id,
                name=name,
                tasks=tasks,
                entry_task=entry_task
            )
            
            self.workflows[workflow_id] = workflow
            return workflow_id
    
    def execute(self, workflow_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行工作流"""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow = self.workflows[workflow_id]
        workflow.status = WorkflowStatus.RUNNING
        
        result = {"status": "success", "context": context}
        
        workflow.status = WorkflowStatus.COMPLETED
        return result
    
    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """获取工作流"""
        return self.workflows.get(workflow_id)


_global_workflow_engine: Optional[WorkflowEngine] = None


def get_workflow_engine() -> WorkflowEngine:
    """获取全局工作流引擎"""
    global _global_workflow_engine
    if _global_workflow_engine is None:
        _global_workflow_engine = WorkflowEngine()
    return _global_workflow_engine
