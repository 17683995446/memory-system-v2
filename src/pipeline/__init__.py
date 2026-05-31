"""
数据处理管道系统
用于构建和管理数据处理流程
"""

import time
import threading
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class PipelineStatus(Enum):
    """管道状态"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PipelineStage:
    """管道阶段"""
    stage_id: str
    name: str
    processor: Callable
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    timeout: int = 300
    retry_count: int = 3


@dataclass
class Pipeline:
    """数据处理管道"""
    pipeline_id: str
    name: str
    stages: List[PipelineStage]
    status: PipelineStatus = PipelineStatus.IDLE
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class PipelineExecution:
    """管道执行记录"""
    execution_id: str
    pipeline_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: PipelineStatus = PipelineStatus.IDLE
    stage_results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class DataPipeline:
    """数据管道"""
    
    def __init__(self):
        self.pipelines: Dict[str, Pipeline] = {}
        self.executions: Dict[str, PipelineExecution] = {}
        self._pipeline_counter: int = 0
        self._execution_counter: int = 0
        self._lock = threading.Lock()
    
    def create_pipeline(
        self,
        name: str,
        stages: List[PipelineStage]
    ) -> str:
        """创建管道"""
        with self._lock:
            self._pipeline_counter += 1
            pipeline_id = f"PIPELINE-{self._pipeline_counter:06d}"
            
            pipeline = Pipeline(
                pipeline_id=pipeline_id,
                name=name,
                stages=stages
            )
            
            self.pipelines[pipeline_id] = pipeline
            return pipeline_id
    
    def execute(
        self,
        pipeline_id: str,
        input_data: Any
    ) -> str:
        """执行管道"""
        if pipeline_id not in self.pipelines:
            raise ValueError(f"Pipeline {pipeline_id} not found")
        
        with self._lock:
            self._execution_counter += 1
            execution_id = f"EXEC-{self._execution_counter:06d}"
            
            execution = PipelineExecution(
                execution_id=execution_id,
                pipeline_id=pipeline_id,
                start_time=datetime.now()
            )
            
            self.executions[execution_id] = execution
        
        pipeline = self.pipelines[pipeline_id]
        pipeline.status = PipelineStatus.RUNNING
        execution.status = PipelineStatus.RUNNING
        
        data = input_data
        for stage in pipeline.stages:
            try:
                result = self._execute_stage(stage, data)
                execution.stage_results[stage.stage_id] = {
                    "status": "success",
                    "output": result,
                    "timestamp": datetime.now()
                }
                data = result
            except Exception as e:
                execution.errors.append(f"Stage {stage.name}: {str(e)}")
                execution.status = PipelineStatus.FAILED
                pipeline.status = PipelineStatus.FAILED
                break
        
        if execution.status == PipelineStatus.RUNNING:
            execution.status = PipelineStatus.COMPLETED
            pipeline.status = PipelineStatus.COMPLETED
        
        execution.end_time = datetime.now()
        return execution_id
    
    def _execute_stage(
        self,
        stage: PipelineStage,
        data: Any
    ) -> Any:
        """执行单个阶段"""
        return stage.processor(data)
    
    def pause_pipeline(self, pipeline_id: str) -> bool:
        """暂停管道"""
        if pipeline_id not in self.pipelines:
            return False
        
        self.pipelines[pipeline_id].status = PipelineStatus.PAUSED
        return True
    
    def resume_pipeline(self, pipeline_id: str) -> bool:
        """恢复管道"""
        if pipeline_id not in self.pipelines:
            return False
        
        self.pipelines[pipeline_id].status = PipelineStatus.IDLE
        return True
    
    def get_pipeline(self, pipeline_id: str) -> Optional[Pipeline]:
        """获取管道"""
        return self.pipelines.get(pipeline_id)
    
    def get_execution(self, execution_id: str) -> Optional[PipelineExecution]:
        """获取执行记录"""
        return self.executions.get(execution_id)
    
    def get_pipeline_executions(
        self,
        pipeline_id: str,
        limit: int = 10
    ) -> List[PipelineExecution]:
        """获取管道的执行历史"""
        return [
            e for e in self.executions.values()
            if e.pipeline_id == pipeline_id
        ][-limit:]


_global_pipeline: Optional[DataPipeline] = None


def get_data_pipeline() -> DataPipeline:
    """获取全局数据管道"""
    global _global_pipeline
    if _global_pipeline is None:
        _global_pipeline = DataPipeline()
    return _global_pipeline
