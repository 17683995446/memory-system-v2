"""
批处理系统
用于大规模数据批处理
"""

import time
import threading
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class BatchJob:
    """批处理作业"""
    job_id: str
    name: str
    processor: Callable
    data: List[Any]
    batch_size: int = 100
    status: str = "pending"


@dataclass
class BatchResult:
    """批处理结果"""
    job_id: str
    total_items: int
    processed_items: int
    failed_items: int
    start_time: datetime
    end_time: Optional[datetime] = None


class BatchProcessor:
    """批处理器"""
    
    def __init__(self):
        self.jobs: Dict[str, BatchJob] = {}
        self.results: Dict[str, BatchResult] = {}
        self._job_counter: int = 0
        self._lock = threading.Lock()
    
    def create_job(
        self,
        name: str,
        processor: Callable,
        data: List[Any],
        batch_size: int = 100
    ) -> str:
        """创建批处理作业"""
        with self._lock:
            self._job_counter += 1
            job_id = f"JOB-{self._job_counter:06d}"
            
            job = BatchJob(
                job_id=job_id,
                name=name,
                processor=processor,
                data=data,
                batch_size=batch_size
            )
            
            self.jobs[job_id] = job
            return job_id
    
    def execute(self, job_id: str) -> str:
        """执行批处理作业"""
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")
        
        job = self.jobs[job_id]
        job.status = "running"
        
        processed = 0
        failed = 0
        
        for i in range(0, len(job.data), job.batch_size):
            batch = job.data[i:i + job.batch_size]
            for item in batch:
                try:
                    job.processor(item)
                    processed += 1
                except Exception:
                    failed += 1
        
        result = BatchResult(
            job_id=job_id,
            total_items=len(job.data),
            processed_items=processed,
            failed_items=failed,
            start_time=datetime.now(),
            end_time=datetime.now()
        )
        
        self.results[job_id] = result
        job.status = "completed"
        
        return job_id
    
    def get_job(self, job_id: str) -> Optional[BatchJob]:
        """获取作业"""
        return self.jobs.get(job_id)
    
    def get_result(self, job_id: str) -> Optional[BatchResult]:
        """获取结果"""
        return self.results.get(job_id)


_global_batch_processor: Optional[BatchProcessor] = None


def get_batch_processor() -> BatchProcessor:
    """获取全局批处理器"""
    global _global_batch_processor
    if _global_batch_processor is None:
        _global_batch_processor = BatchProcessor()
    return _global_batch_processor
