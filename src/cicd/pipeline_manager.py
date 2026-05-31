"""
CI/CD流水线管理器
用于管理和执行持续集成和持续部署流水线
"""
import time
import json
import threading
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import traceback


class PipelineStatus(Enum):
    """流水线状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class StageStatus(Enum):
    """阶段状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Stage:
    """流水线阶段"""
    stage_id: str
    name: str
    tasks: List[Dict]  # {'name': str, 'action': Callable, 'timeout': float}
    parallel: bool = False
    continue_on_error: bool = False
    timeout: float = 300.0  # 5分钟默认超时


@dataclass
class StageResult:
    """阶段结果"""
    stage_name: str
    status: StageStatus
    duration_ms: float
    task_results: List[Dict] = field(default_factory=list)
    error_message: str = ""
    metadata: Dict = field(default_factory=dict)


@dataclass
class Pipeline:
    """流水线"""
    pipeline_id: str
    name: str
    description: str
    stages: List[Stage]
    created_at: datetime
    updated_at: datetime
    triggers: List[str] = field(default_factory=list)
    environment: str = "development"


@dataclass
class PipelineRun:
    """流水线运行"""
    run_id: str
    pipeline_id: str
    pipeline_name: str
    status: PipelineStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    stage_results: List[StageResult] = field(default_factory=list)
    commit_sha: str = ""
    branch: str = "main"
    triggered_by: str = "manual"
    duration_ms: float = 0.0
    error_message: str = ""
    logs: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


class PipelineManager:
    """流水线管理器"""
    
    def __init__(self):
        self.pipelines: Dict[str, Pipeline] = {}
        self.runs: Dict[str, PipelineRun] = {}
        self._pipeline_counter = 0
        self._run_counter = 0
        self._lock = threading.Lock()
        self._running_pipelines: Dict[str, threading.Thread] = {}
    
    def create_pipeline(
        self,
        name: str,
        description: str = "",
        environment: str = "development",
        triggers: List[str] = None
    ) -> str:
        """创建流水线"""
        with self._lock:
            self._pipeline_counter += 1
            pipeline_id = f"PIPELINE-{self._pipeline_counter:04d}"
            
            pipeline = Pipeline(
                pipeline_id=pipeline_id,
                name=name,
                description=description,
                stages=[],
                triggers=triggers or ["manual"],
                environment=environment,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            self.pipelines[pipeline_id] = pipeline
            return pipeline_id
    
    def add_stage(
        self,
        pipeline_id: str,
        name: str,
        tasks: List[Dict] = None,
        parallel: bool = False,
        continue_on_error: bool = False,
        timeout: float = 300.0
    ) -> Optional[str]:
        """添加流水线阶段"""
        if pipeline_id not in self.pipelines:
            return None
        
        pipeline = self.pipelines[pipeline_id]
        
        stage_id = f"{pipeline_id}_stage_{len(pipeline.stages):02d}"
        
        stage = Stage(
            stage_id=stage_id,
            name=name,
            tasks=tasks or [],
            parallel=parallel,
            continue_on_error=continue_on_error,
            timeout=timeout
        )
        
        pipeline.stages.append(stage)
        pipeline.updated_at = datetime.now()
        
        return stage_id
    
    def get_pipeline(self, pipeline_id: str) -> Optional[Pipeline]:
        """获取流水线"""
        return self.pipelines.get(pipeline_id)
    
    def run_pipeline(
        self,
        pipeline_id: str,
        commit_sha: str = "",
        branch: str = "main",
        triggered_by: str = "manual"
    ) -> Optional[str]:
        """运行流水线"""
        if pipeline_id not in self.pipelines:
            return None
        
        pipeline = self.pipelines[pipeline_id]
        
        with self._lock:
            self._run_counter += 1
            run_id = f"RUN-{self._run_counter:04d}"
            
            run = PipelineRun(
                run_id=run_id,
                pipeline_id=pipeline_id,
                pipeline_name=pipeline.name,
                status=PipelineStatus.PENDING,
                start_time=datetime.now(),
                commit_sha=commit_sha,
                branch=branch,
                triggered_by=triggered_by
            )
            
            self.runs[run_id] = run
        
        # 在后台运行
        thread = threading.Thread(
            target=self._execute_pipeline,
            args=(run_id,)
        )
        thread.daemon = True
        thread.start()
        
        self._running_pipelines[run_id] = thread
        
        return run_id
    
    def _execute_pipeline(self, run_id: str):
        """执行流水线"""
        run = self.runs.get(run_id)
        if not run:
            return
        
        run.status = PipelineStatus.RUNNING
        run.logs.append(f"[{datetime.now()}] Pipeline started")
        
        pipeline = self.pipelines.get(run.pipeline_id)
        if not pipeline:
            run.status = PipelineStatus.FAILED
            run.error_message = "Pipeline not found"
            run.logs.append(f"[{datetime.now()}] Error: Pipeline not found")
            return
        
        start_time = time.time()
        
        # 执行每个阶段
        for stage in pipeline.stages:
            stage_result = self._execute_stage(stage, run)
            run.stage_results.append(stage_result)
            
            if stage_result.status == StageStatus.FAILED and not stage.continue_on_error:
                break
        
        duration = (time.time() - start_time) * 1000
        run.duration_ms = duration
        run.end_time = datetime.now()
        
        # 确定最终状态
        failed_stages = [s for s in run.stage_results if s.status == StageStatus.FAILED]
        if failed_stages:
            run.status = PipelineStatus.FAILED
            run.error_message = failed_stages[0].error_message
            run.logs.append(f"[{datetime.now()}] Pipeline failed")
        else:
            run.status = PipelineStatus.SUCCESS
            run.logs.append(f"[{datetime.now()}] Pipeline completed successfully")
        
        # 清理运行中的流水线
        if run_id in self._running_pipelines:
            del self._running_pipelines[run_id]
    
    def _execute_stage(self, stage: Stage, run: PipelineRun) -> StageResult:
        """执行阶段"""
        start_time = time.time()
        run.logs.append(f"[{datetime.now()}] Stage '{stage.name}' started")
        
        task_results = []
        
        if stage.parallel:
            # 并行执行任务
            threads = []
            results = {'data': []}
            results_lock = threading.Lock()
            
            def execute_task(task):
                task_result = self._execute_task(task, run)
                with results_lock:
                    results['data'].append(task_result)
            
            for task in stage.tasks:
                thread = threading.Thread(target=execute_task, args=(task,))
                thread.daemon = True
                thread.start()
                threads.append(thread)
            
            for thread in threads:
                thread.join(timeout=stage.timeout)
            
            task_results = results['data']
        else:
            # 顺序执行任务
            for task in stage.tasks:
                task_result = self._execute_task(task, run)
                task_results.append(task_result)
                
                if task_result['status'] == 'failed' and not stage.continue_on_error:
                    break
        
        duration = (time.time() - start_time) * 1000
        
        failed_tasks = [t for t in task_results if t['status'] == 'failed']
        
        status = StageStatus.SUCCESS
        error_message = ""
        
        if failed_tasks:
            status = StageStatus.FAILED
            error_message = failed_tasks[0].get('error', 'Unknown error')
            run.logs.append(f"[{datetime.now()}] Stage '{stage.name}' failed: {error_message}")
        else:
            run.logs.append(f"[{datetime.now()}] Stage '{stage.name}' completed")
        
        return StageResult(
            stage_name=stage.name,
            status=status,
            duration_ms=duration,
            task_results=task_results,
            error_message=error_message
        )
    
    def _execute_task(self, task: Dict, run: PipelineRun) -> Dict:
        """执行任务"""
        task_name = task.get('name', 'unnamed')
        action = task.get('action')
        timeout = task.get('timeout', 60.0)
        
        run.logs.append(f"[{datetime.now()}] Task '{task_name}' started")
        
        start_time = time.time()
        
        try:
            if action:
                if timeout:
                    result = self._run_with_timeout(action, timeout)
                else:
                    result = action()
            else:
                result = None
            
            duration = (time.time() - start_time) * 1000
            
            run.logs.append(f"[{datetime.now()}] Task '{task_name}' completed in {duration:.2f}ms")
            
            return {
                'name': task_name,
                'status': 'success',
                'duration_ms': duration,
                'result': result
            }
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            error_msg = str(e)
            
            run.logs.append(f"[{datetime.now()}] Task '{task_name}' failed: {error_msg}")
            
            return {
                'name': task_name,
                'status': 'failed',
                'duration_ms': duration,
                'error': error_msg,
                'traceback': traceback.format_exc()
            }
    
    def _run_with_timeout(self, func: Callable, timeout: float) -> Any:
        """带超时运行函数"""
        result = {'value': None, 'exception': None}
        
        def target():
            try:
                result['value'] = func()
            except Exception as e:
                result['exception'] = e
        
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout)
        
        if thread.is_alive():
            raise TimeoutError(f"Execution timed out after {timeout}s")
        
        if result['exception']:
            raise result['exception']
        
        return result['value']
    
    def get_run(self, run_id: str) -> Optional[PipelineRun]:
        """获取流水线运行"""
        return self.runs.get(run_id)
    
    def cancel_run(self, run_id: str) -> bool:
        """取消流水线运行"""
        run = self.runs.get(run_id)
        if not run or run.status not in [PipelineStatus.PENDING, PipelineStatus.RUNNING]:
            return False
        
        run.status = PipelineStatus.CANCELLED
        run.end_time = datetime.now()
        run.error_message = "Cancelled by user"
        
        if run_id in self._running_pipelines:
            del self._running_pipelines[run_id]
        
        return True
    
    def get_pipeline_runs(self, pipeline_id: str, limit: int = 10) -> List[PipelineRun]:
        """获取流水线运行历史"""
        runs = [
            r for r in self.runs.values()
            if r.pipeline_id == pipeline_id
        ]
        
        runs.sort(key=lambda x: x.start_time, reverse=True)
        
        return runs[:limit]
    
    def generate_report(self, run_id: str) -> str:
        """生成流水线运行报告"""
        run = self.runs.get(run_id)
        if not run:
            return "Run not found"
        
        report = []
        report.append("=" * 70)
        report.append(f"流水线运行报告: {run.pipeline_name}")
        report.append("=" * 70)
        report.append(f"运行ID: {run.run_id}")
        report.append(f"状态: {run.status.value}")
        report.append(f"触发方式: {run.triggered_by}")
        report.append(f"分支: {run.branch}")
        report.append(f"提交: {run.commit_sha}")
        report.append(f"开始时间: {run.start_time}")
        if run.end_time:
            report.append(f"结束时间: {run.end_time}")
        report.append(f"耗时: {run.duration_ms:.2f}ms")
        
        if run.error_message:
            report.append(f"错误: {run.error_message}")
        
        report.append("\n阶段详情:")
        for stage_result in run.stage_results:
            status_symbol = "✓" if stage_result.status == StageStatus.SUCCESS else "✗"
            report.append(f"  {status_symbol} {stage_result.stage_name} ({stage_result.duration_ms:.2f}ms)")
            
            if stage_result.error_message:
                report.append(f"      错误: {stage_result.error_message}")
        
        report.append("\n日志:")
        for log in run.logs[-20:]:  # 最近20条日志
            report.append(f"  {log}")
        
        report.append("\n" + "=" * 70)
        return "\n".join(report)
    
    def export_run(self, run_id: str, filepath: str) -> bool:
        """导出流水线运行数据"""
        run = self.runs.get(run_id)
        if not run:
            return False
        
        data = {
            'run_id': run.run_id,
            'pipeline_id': run.pipeline_id,
            'pipeline_name': run.pipeline_name,
            'status': run.status.value,
            'start_time': run.start_time.isoformat(),
            'end_time': run.end_time.isoformat() if run.end_time else None,
            'duration_ms': run.duration_ms,
            'commit_sha': run.commit_sha,
            'branch': run.branch,
            'triggered_by': run.triggered_by,
            'error_message': run.error_message,
            'stage_results': [
                {
                    'stage_name': s.stage_name,
                    'status': s.status.value,
                    'duration_ms': s.duration_ms,
                    'error_message': s.error_message,
                    'task_results': s.task_results
                }
                for s in run.stage_results
            ],
            'logs': run.logs,
            'metadata': run.metadata
        }
        
        import os
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return True


# 全局流水线管理器
_pipeline_manager = None


def get_pipeline_manager() -> PipelineManager:
    """获取流水线管理器"""
    global _pipeline_manager
    if _pipeline_manager is None:
        _pipeline_manager = PipelineManager()
    return _pipeline_manager
