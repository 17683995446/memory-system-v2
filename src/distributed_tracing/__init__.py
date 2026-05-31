"""
分布式追踪
用于请求链路追踪
"""

import time
import threading
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Trace:
    """追踪"""
    trace_id: str
    spans: List['Span'] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)


@dataclass
class Span:
    """跨度"""
    span_id: str
    parent_id: Optional[str]
    operation_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    tags: Dict[str, str] = field(default_factory=dict)
    logs: List[Dict] = field(default_factory=list)


class DistributedTracer:
    """分布式追踪器"""
    
    def __init__(self):
        self.traces: Dict[str, Trace] = {}
        self.active_spans: Dict[str, Span] = {}
        self._lock = threading.Lock()
    
    def start_trace(self, operation_name: str) -> str:
        """开始追踪"""
        trace_id = f"TRACE-{uuid.uuid4().hex[:16]}"
        
        with self._lock:
            trace = Trace(trace_id=trace_id)
            self.traces[trace_id] = trace
            
            span_id = f"SPAN-{uuid.uuid4().hex[:12]}"
            span = Span(
                span_id=span_id,
                parent_id=None,
                operation_name=operation_name,
                start_time=datetime.now()
            )
            
            trace.spans.append(span)
            self.active_spans[span_id] = span
        
        return trace_id
    
    def start_span(
        self,
        trace_id: str,
        operation_name: str,
        parent_span_id: Optional[str] = None
    ) -> str:
        """开始跨度"""
        with self._lock:
            span_id = f"SPAN-{uuid.uuid4().hex[:12]}"
            span = Span(
                span_id=span_id,
                parent_id=parent_span_id,
                operation_name=operation_name,
                start_time=datetime.now()
            )
            
            if trace_id in self.traces:
                self.traces[trace_id].spans.append(span)
            
            self.active_spans[span_id] = span
        
        return span_id
    
    def end_span(self, span_id: str):
        """结束跨度"""
        with self._lock:
            if span_id in self.active_spans:
                span = self.active_spans[span_id]
                span.end_time = datetime.now()
                del self.active_spans[span_id]
    
    def add_span_tag(self, span_id: str, key: str, value: str):
        """添加跨度标签"""
        with self._lock:
            if span_id in self.active_spans:
                self.active_spans[span_id].tags[key] = value
    
    def add_span_log(self, span_id: str, event: str, data: Optional[Dict] = None):
        """添加跨度日志"""
        with self._lock:
            if span_id in self.active_spans:
                self.active_spans[span_id].logs.append({
                    "timestamp": datetime.now(),
                    "event": event,
                    "data": data or {}
                })
    
    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """获取追踪"""
        return self.traces.get(trace_id)
    
    def get_trace_duration(self, trace_id: str) -> Optional[float]:
        """获取追踪持续时间"""
        trace = self.traces.get(trace_id)
        if not trace or not trace.spans:
            return None
        
        start_time = min(span.start_time for span in trace.spans)
        end_time = max(
            span.end_time for span in trace.spans
            if span.end_time
        ) or datetime.now()
        
        return (end_time - start_time).total_seconds() * 1000


_global_tracer: Optional[DistributedTracer] = None


def get_distributed_tracer() -> DistributedTracer:
    """获取全局追踪器"""
    global _global_tracer
    if _global_tracer is None:
        _global_tracer = DistributedTracer()
    return _global_tracer
