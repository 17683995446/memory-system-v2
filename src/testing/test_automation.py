"""
测试自动化工具
提供自动化测试运行、CI/CD集成、测试调度等功能
"""
import time
import threading
import subprocess
import os
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta


class TestScheduleType(Enum):
    """测试调度类型"""
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    HOURLY = "hourly"
    MANUAL = "manual"


@dataclass
class TestSchedule:
    """测试调度"""
    schedule_id: str
    name: str
    type: TestScheduleType
    target_suites: List[str]
    next_run: datetime
    last_run: Optional[datetime] = None
    last_result: Optional[Dict] = None
    enabled: bool = True
    cron_expression: str = ""
    metadata: Dict = field(default_factory=dict)


@dataclass
class CIJob:
    """CI任务"""
    job_id: str
    name: str
    status: str  # pending, running, completed, failed
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    results: Optional[Dict] = None
    logs: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


class TestAutomation:
    """测试自动化管理器"""
    
    def __init__(self, framework):
        self.framework = framework
        self.schedules: Dict[str, TestSchedule] = {}
        self.jobs: Dict[str, CIJob] = {}
        self._running = False
        self._scheduler_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._job_counter = 0
        self._schedule_counter = 0
    
    def create_schedule(
        self,
        name: str,
        schedule_type: TestScheduleType,
        target_suites: List[str],
        start_time: Optional[datetime] = None,
        enabled: bool = True
    ) -> str:
        """创建测试调度"""
        with self._lock:
            self._schedule_counter += 1
            schedule_id = f"SCHED-{self._schedule_counter:04d}"
            
            if start_time is None:
                start_time = datetime.now()
            
            schedule = TestSchedule(
                schedule_id=schedule_id,
                name=name,
                type=schedule_type,
                target_suites=target_suites,
                next_run=start_time,
                enabled=enabled
            )
            
            self.schedules[schedule_id] = schedule
            return schedule_id
    
    def update_schedule(
        self,
        schedule_id: str,
        enabled: Optional[bool] = None,
        next_run: Optional[datetime] = None
    ) -> bool:
        """更新测试调度"""
        with self._lock:
            if schedule_id not in self.schedules:
                return False
            
            schedule = self.schedules[schedule_id]
            if enabled is not None:
                schedule.enabled = enabled
            if next_run is not None:
                schedule.next_run = next_run
            
            return True
    
    def delete_schedule(self, schedule_id: str) -> bool:
        """删除测试调度"""
        with self._lock:
            if schedule_id not in self.schedules:
                return False
            
            del self.schedules[schedule_id]
            return True
    
    def get_schedule(self, schedule_id: str) -> Optional[TestSchedule]:
        """获取测试调度"""
        return self.schedules.get(schedule_id)
    
    def list_schedules(self) -> List[TestSchedule]:
        """列出所有测试调度"""
        return list(self.schedules.values())
    
    def create_ci_job(
        self,
        name: str,
        target_suites: Optional[List[str]] = None
    ) -> str:
        """创建CI任务"""
        with self._lock:
            self._job_counter += 1
            job_id = f"JOB-{self._job_counter:04d}"
            
            job = CIJob(
                job_id=job_id,
                name=name,
                status="pending"
            )
            
            if target_suites:
                job.metadata['target_suites'] = target_suites
            
            self.jobs[job_id] = job
            return job_id
    
    def run_ci_job(self, job_id: str) -> bool:
        """运行CI任务"""
        with self._lock:
            if job_id not in self.jobs:
                return False
            
            job = self.jobs[job_id]
            if job.status == "running":
                return False
            
            job.status = "running"
            job.start_time = datetime.now()
            job.logs.append(f"[{datetime.now()}] Job started")
        
        # 在后台运行
        thread = threading.Thread(
            target=self._run_job_background,
            args=(job_id,)
        )
        thread.daemon = True
        thread.start()
        
        return True
    
    def _run_job_background(self, job_id: str):
        """后台运行CI任务"""
        try:
            job = self.jobs[job_id]
            target_suites = job.metadata.get('target_suites')
            
            job.logs.append(f"[{datetime.now()}] Running tests...")
            
            # 运行测试
            if target_suites:
                results = {}
                for suite_name in target_suites:
                    suite = self.framework.get_suite(suite_name)
                    if suite:
                        results[suite_name] = suite.run()
            else:
                results = self.framework.run_all()
            
            job.results = results
            job.status = "completed"
            job.end_time = datetime.now()
            job.logs.append(f"[{datetime.now()}] Job completed successfully")
            
        except Exception as e:
            job = self.jobs[job_id]
            job.status = "failed"
            job.end_time = datetime.now()
            job.logs.append(f"[{datetime.now()}] Job failed: {str(e)}")
    
    def get_job(self, job_id: str) -> Optional[CIJob]:
        """获取CI任务"""
        return self.jobs.get(job_id)
    
    def list_jobs(self, status: Optional[str] = None) -> List[CIJob]:
        """列出CI任务"""
        jobs = list(self.jobs.values())
        if status:
            jobs = [j for j in jobs if j.status == status]
        return jobs
    
    def start_scheduler(self):
        """启动调度器"""
        if self._running:
            return
        
        self._running = True
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop)
        self._scheduler_thread.daemon = True
        self._scheduler_thread.start()
    
    def stop_scheduler(self):
        """停止调度器"""
        self._running = False
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5.0)
    
    def _scheduler_loop(self):
        """调度器主循环"""
        while self._running:
            now = datetime.now()
            
            with self._lock:
                for schedule in self.schedules.values():
                    if not schedule.enabled:
                        continue
                    
                    if now >= schedule.next_run:
                        # 触发调度
                        self._trigger_schedule(schedule)
                        
                        # 计算下次运行时间
                        self._calculate_next_run(schedule)
            
            time.sleep(60)  # 每分钟检查一次
    
    def _trigger_schedule(self, schedule: TestSchedule):
        """触发测试调度"""
        job_id = self.create_ci_job(
            name=f"Scheduled: {schedule.name}",
            target_suites=schedule.target_suites
        )
        
        schedule.last_run = datetime.now()
        self.run_ci_job(job_id)
        
        job = self.get_job(job_id)
        if job:
            schedule.last_result = {'job_id': job_id}
    
    def _calculate_next_run(self, schedule: TestSchedule):
        """计算下次运行时间"""
        now = datetime.now()
        
        if schedule.type == TestScheduleType.DAILY:
            schedule.next_run = now + timedelta(days=1)
        elif schedule.type == TestScheduleType.WEEKLY:
            schedule.next_run = now + timedelta(weeks=1)
        elif schedule.type == TestScheduleType.HOURLY:
            schedule.next_run = now + timedelta(hours=1)
        elif schedule.type == TestScheduleType.ONCE:
            schedule.enabled = False
    
    def generate_ci_report(self, job_id: str) -> str:
        """生成CI报告"""
        job = self.get_job(job_id)
        if not job:
            return "Job not found"
        
        report = []
        report.append("=" * 70)
        report.append(f"CI Job Report: {job.name}")
        report.append("=" * 70)
        report.append(f"Job ID: {job.job_id}")
        report.append(f"Status: {job.status}")
        report.append(f"Start Time: {job.start_time}")
        report.append(f"End Time: {job.end_time}")
        
        if job.results:
            report.append("\nTest Results:")
            for suite_name, result in job.results.items():
                report.append(f"\n  {suite_name}:")
                report.append(f"    Total: {result['total_tests']}")
                report.append(f"    Passed: {result['passed']}")
                report.append(f"    Failed: {result['failed']}")
                report.append(f"    Errors: {result['errors']}")
        
        report.append("\nLogs:")
        for log in job.logs:
            report.append(f"  {log}")
        
        report.append("\n" + "=" * 70)
        return "\n".join(report)
    
    def export_results(self, job_id: str, filepath: str) -> bool:
        """导出测试结果"""
        import json
        
        job = self.get_job(job_id)
        if not job or not job.results:
            return False
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                'job_id': job.job_id,
                'name': job.name,
                'status': job.status,
                'start_time': job.start_time.isoformat() if job.start_time else None,
                'end_time': job.end_time.isoformat() if job.end_time else None,
                'results': job.results
            }, f, ensure_ascii=False, indent=2)
        
        return True


# 全局测试自动化管理器
_test_automation = None


def get_test_automation(framework=None):
    """获取测试自动化管理器"""
    global _test_automation
    if _test_automation is None:
        if framework is None:
            from .test_framework import get_testing_framework
            framework = get_testing_framework()
        _test_automation = TestAutomation(framework)
    return _test_automation
