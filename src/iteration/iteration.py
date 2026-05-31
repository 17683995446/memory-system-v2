"""
复盘迭代模块
基于第一性原理：任务闭环后自动复盘、提炼经验为规则、优化召回权重
"""
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class TaskRecord:
    """任务记录"""
    task_id: str
    task_type: str
    start_time: float
    end_time: Optional[float] = None
    status: str = "running"  # running, success, failed
    steps: List[Dict] = field(default_factory=list)
    memory_usage: Dict[str, int] = field(default_factory=dict)
    recall_effectiveness: float = 0.0
    lessons: List[str] = field(default_factory=list)


class Reviewer:
    """复盘器"""
    
    def __init__(self):
        self.task_records: Dict[str, TaskRecord] = {}
    
    def start_task(self, task_id: str, task_type: str) -> None:
        """记录任务开始"""
        self.task_records[task_id] = TaskRecord(
            task_id=task_id,
            task_type=task_type,
            start_time=time.time()
        )
    
    def end_task(self, task_id: str, status: str) -> Optional[TaskRecord]:
        """记录任务结束"""
        if task_id not in self.task_records:
            return None
        
        record = self.task_records[task_id]
        record.end_time = time.time()
        record.status = status
        
        # 自动复盘
        self._review(record)
        
        return record
    
    def add_step(self, task_id: str, step: Dict) -> None:
        """添加任务步骤"""
        if task_id in self.task_records:
            self.task_records[task_id].steps.append(step)
    
    def _review(self, record: TaskRecord) -> None:
        """执行复盘"""
        lessons = []
        
        # 分析任务耗时
        if record.end_time and record.start_time:
            duration = record.end_time - record.start_time
            if duration > 300:  # 超过5分钟
                lessons.append(f"任务耗时较长: {duration:.1f}秒")
        
        # 分析步骤数量
        if len(record.steps) > 20:
            lessons.append(f"任务步骤过多: {len(record.steps)}步")
        
        # 分析记忆召回效果
        if record.recall_effectiveness < 0.5:
            lessons.append("记忆召回效果不佳")
        
        # 分析任务状态
        if record.status == "failed":
            lessons.append("任务执行失败")
        
        record.lessons = lessons
    
    def get_review_summary(self, task_id: str) -> Optional[Dict]:
        """获取复盘总结"""
        if task_id not in self.task_records:
            return None
        
        record = self.task_records[task_id]
        
        return {
            'task_id': record.task_id,
            'task_type': record.task_type,
            'duration': record.end_time - record.start_time if record.end_time else None,
            'status': record.status,
            'step_count': len(record.steps),
            'lessons': record.lessons,
            'memory_usage': record.memory_usage,
            'recall_effectiveness': record.recall_effectiveness
        }


class ExperienceExtractor:
    """经验提取器"""
    
    def __init__(self):
        self.pattern_keywords = {
            'success': ['成功', '完成', '解决', '搞定'],
            'failure': ['失败', '错误', '异常', '问题'],
            'method': ['方法', '步骤', '使用', '调用'],
            'rule': ['规则', '必须', '应该', '注意']
        }
    
    def extract_success_pattern(self, steps: List[Dict]) -> Optional[Dict]:
        """提取成功模式"""
        success_steps = [
            step for step in steps 
            if any(kw in step.get('result', '') for kw in self.pattern_keywords['success'])
        ]
        
        if not success_steps:
            return None
        
        return {
            'type': 'success_pattern',
            'steps': len(success_steps),
            'pattern': self._summarize_steps(success_steps)
        }
    
    def extract_failure_pattern(self, steps: List[Dict]) -> Optional[Dict]:
        """提取失败模式"""
        failure_steps = [
            step for step in steps 
            if any(kw in step.get('result', '') for kw in self.pattern_keywords['failure'])
        ]
        
        if not failure_steps:
            return None
        
        return {
            'type': 'failure_pattern',
            'steps': len(failure_steps),
            'pattern': self._summarize_steps(failure_steps)
        }
    
    def extract_rules(self, steps: List[Dict]) -> List[str]:
        """提取可固化的规则"""
        rules = []
        
        for step in steps:
            text = str(step.get('result', ''))
            
            for keyword in self.pattern_keywords['rule']:
                if keyword in text:
                    rules.append(text)
                    break
        
        return rules
    
    def _summarize_steps(self, steps: List[Dict]) -> str:
        """总结步骤"""
        if not steps:
            return ""
        
        actions = [step.get('action', '') for step in steps[:5]]
        return " -> ".join(actions)


class WeightOptimizer:
    """权重优化器"""
    
    def __init__(self):
        self.recall_weights = {
            'task_match': 1.0,
            'time_decay': 0.8,
            'access_count': 0.6
        }
        self.adjustment_history: List[Dict] = []
    
    def adjust_weights(self, feedback: Dict) -> Dict:
        """
        根据反馈调整召回权重
        反馈: {'recall_type': 'l2', 'effectiveness': 0.7}
        """
        recall_type = feedback.get('recall_type')
        effectiveness = feedback.get('effectiveness', 0.5)
        
        # 简单策略：如果召回效果好，增加权重
        if effectiveness > 0.7:
            if recall_type == 'l2':
                self.recall_weights['task_match'] *= 1.1
            elif recall_type == 'l3':
                self.recall_weights['time_decay'] *= 1.1
        elif effectiveness < 0.3:
            if recall_type == 'l2':
                self.recall_weights['task_match'] *= 0.9
        
        # 记录调整历史
        self.adjustment_history.append({
            'time': time.time(),
            'feedback': feedback,
            'weights': self.recall_weights.copy()
        })
        
        return self.recall_weights.copy()
    
    def get_weights(self) -> Dict:
        """获取当前权重"""
        return self.recall_weights.copy()


# 全局单例
_reviewer = None
_experience_extractor = None
_weight_optimizer = None


def get_reviewer() -> Reviewer:
    global _reviewer
    if _reviewer is None:
        _reviewer = Reviewer()
    return _reviewer


def get_experience_extractor() -> ExperienceExtractor:
    global _experience_extractor
    if _experience_extractor is None:
        _experience_extractor = ExperienceExtractor()
    return _experience_extractor


def get_weight_optimizer() -> WeightOptimizer:
    global _weight_optimizer
    if _weight_optimizer is None:
        _weight_optimizer = WeightOptimizer()
    return _weight_optimizer
