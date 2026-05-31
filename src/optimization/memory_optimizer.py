"""
内存优化工具
用于内存使用分析和优化
"""

import gc
import sys
import threading
import weakref
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import tracemalloc


class MemoryOptimizationLevel(Enum):
    """内存优化级别"""
    LIGHT = "light"
    MEDIUM = "medium"
    AGGRESSIVE = "aggressive"


@dataclass
class MemoryUsage:
    """内存使用情况"""
    timestamp: datetime
    total_allocated: int
    peak_allocated: int
    object_count: int
    gc_stats: Dict[str, Any]


@dataclass
class ObjectLeak:
    """内存泄漏检测"""
    object_type: str
    count: int
    size: int
    sample_objects: List[Any]


@dataclass
class OptimizationSuggestion:
    """优化建议"""
    category: str
    issue: str
    suggestion: str
    priority: int
    estimated_impact: str


class MemoryOptimizer:
    """内存优化器"""
    
    def __init__(self):
        self._usage_history: List[MemoryUsage] = []
        self._object_tracking: Dict[str, int] = {}
        self._lock = threading.Lock()
        self._tracing = False
    
    def get_current_memory_usage(self) -> MemoryUsage:
        """获取当前内存使用情况"""
        gc.collect()
        
        gc_stats = {
            f"generation_{i}": gc.get_stats()[i]
            for i in range(3)
        }
        
        usage = MemoryUsage(
            timestamp=datetime.now(),
            total_allocated=sum(obj.size for obj in gc.get_objects() if hasattr(obj, '__sizeof__')),
            peak_allocated=0,
            object_count=len(gc.get_objects()),
            gc_stats=gc_stats
        )
        
        with self._lock:
            self._usage_history.append(usage)
            if len(self._usage_history) > 100:
                self._usage_history.pop(0)
        
        return usage
    
    def start_tracing(self):
        """开始内存追踪"""
        if not self._tracing:
            tracemalloc.start()
            self._tracing = True
    
    def stop_tracing(self):
        """停止内存追踪"""
        if self._tracing:
            tracemalloc.stop()
            self._tracing = False
    
    def get_snapshot(self):
        """获取内存快照"""
        if self._tracing:
            return tracemalloc.take_snapshot()
        return None
    
    def analyze_memory_usage(self) -> Dict[str, Any]:
        """分析内存使用"""
        snapshot = self.get_snapshot()
        
        if not snapshot:
            return {"error": "Memory tracing not started"}
        
        top_stats = snapshot.statistics('lineno')
        
        analysis = {
            "timestamp": datetime.now(),
            "total_objects": len(gc.get_objects()),
            "top_allocations": [],
            "suggestions": []
        }
        
        for stat in top_stats[:10]:
            analysis["top_allocations"].append({
                "traceback": str(stat.traceback),
                "size": stat.size,
                "count": stat.count
            })
        
        usage = self.get_current_memory_usage()
        
        if usage.total_allocated > 500 * 1024 * 1024:
            analysis["suggestions"].append(OptimizationSuggestion(
                category="memory",
                issue="High memory usage",
                suggestion="Consider reducing object count or using more efficient data structures",
                priority=1,
                estimated_impact="high"
            ))
        
        return analysis
    
    def detect_memory_leaks(self, duration_seconds: int = 5) -> List[ObjectLeak]:
        """检测内存泄漏"""
        gc.collect()
        
        initial_counts = {}
        for obj in gc.get_objects():
            obj_type = type(obj).__name__
            initial_counts[obj_type] = initial_counts.get(obj_type, 0) + 1
        
        import time
        time.sleep(duration_seconds)
        
        gc.collect()
        
        final_counts = {}
        for obj in gc.get_objects():
            obj_type = type(obj).__name__
            final_counts[obj_type] = final_counts.get(obj_type, 0) + 1
        
        leaks = []
        for obj_type, final_count in final_counts.items():
            initial_count = initial_counts.get(obj_type, 0)
            if final_count > initial_count * 1.2 and final_count > 100:
                sample_objects = [obj for obj in gc.get_objects() 
                               if type(obj).__name__ == obj_type][:5]
                
                leak = ObjectLeak(
                    object_type=obj_type,
                    count=final_count - initial_count,
                    size=sum(sys.getsizeof(obj) for obj in sample_objects),
                    sample_objects=sample_objects
                )
                leaks.append(leak)
        
        return leaks
    
    def optimize_memory(self, level: MemoryOptimizationLevel = MemoryOptimizationLevel.MEDIUM):
        """优化内存使用"""
        results = {
            "timestamp": datetime.now(),
            "level": level.value,
            "actions": [],
            "before": self.get_current_memory_usage(),
            "after": None
        }
        
        if level == MemoryOptimizationLevel.LIGHT:
            gc.collect()
            results["actions"].append("light_gc_collect")
        
        elif level == MemoryOptimizationLevel.MEDIUM:
            gc.collect()
            gc.collect()
            gc.collect()
            results["actions"].append("full_gc_collect")
        
        elif level == MemoryOptimizationLevel.AGGRESSIVE:
            gc.collect()
            gc.collect()
            gc.collect()
            
            try:
                gc.freeze()
                results["actions"].append("gc_freeze")
            except Exception:
                pass
            
            gc.collect()
            results["actions"].append("aggressive_gc")
        
        results["after"] = self.get_current_memory_usage()
        
        return results
    
    def create_object_pool(self, object_type, preallocate_count: int = 10):
        """创建对象池"""
        pool = {
            "type": object_type,
            "available": [],
            "in_use": weakref.WeakSet(),
            "preallocate_count": preallocate_count
        }
        
        try:
            for _ in range(preallocate_count):
                obj = object_type()
                pool["available"].append(obj)
        except Exception:
            pass
        
        return pool
    
    def get_from_pool(self, pool):
        """从对象池获取对象"""
        if not pool["available"]:
            try:
                obj = pool["type"]()
                return obj
            except Exception:
                return None
        
        obj = pool["available"].pop()
        pool["in_use"].add(obj)
        return obj
    
    def return_to_pool(self, pool, obj):
        """将对象返回对象池"""
        if hasattr(obj, '__dict__'):
            obj.__dict__.clear()
        elif hasattr(obj, '__slots__'):
            for slot in obj.__slots__:
                try:
                    delattr(obj, slot)
                except Exception:
                    pass
        
        if obj in pool["in_use"]:
            pool["in_use"].remove(obj)
        
        pool["available"].append(obj)
    
    def compress_data(self, data):
        """压缩数据以节省内存"""
        import zlib
        import pickle
        
        try:
            serialized = pickle.dumps(data)
            compressed = zlib.compress(serialized, level=9)
            return compressed
        except Exception:
            return data
    
    def decompress_data(self, compressed):
        """解压缩数据"""
        import zlib
        import pickle
        
        try:
            decompressed = zlib.decompress(compressed)
            data = pickle.loads(decompressed)
            return data
        except Exception:
            return compressed
    
    def get_optimization_suggestions(self) -> List[OptimizationSuggestion]:
        """获取优化建议"""
        suggestions = []
        usage = self.get_current_memory_usage()
        
        if usage.total_allocated > 100 * 1024 * 1024:
            suggestions.append(OptimizationSuggestion(
                category="memory",
                issue="High memory consumption",
                suggestion="Review large data structures, consider using more memory-efficient formats",
                priority=1,
                estimated_impact="high"
            ))
        
        gc_stats = usage.gc_stats
        gen0_stats = gc_stats.get("generation_0", {})
        collections = gen0_stats.get("collections", 0)
        
        if collections > 1000:
            suggestions.append(OptimizationSuggestion(
                category="gc",
                issue="Frequent garbage collections",
                suggestion="Consider reducing short-lived object creation, use object pooling",
                priority=2,
                estimated_impact="medium"
            ))
        
        if len(self._usage_history) >= 10:
            recent_usage = [u.total_allocated for u in self._usage_history[-10:]]
            increasing = all(recent_usage[i] <= recent_usage[i+1] for i in range(len(recent_usage)-1))
            
            if increasing:
                suggestions.append(OptimizationSuggestion(
                    category="leak",
                    issue="Memory usage increasing steadily",
                    suggestion="Possible memory leak, monitor object creation and cleanup",
                    priority=1,
                    estimated_impact="high"
                ))
        
        return suggestions
    
    def get_usage_trend(self, minutes: int = 5) -> Dict[str, Any]:
        """获取内存使用趋势"""
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(minutes=minutes)
        
        recent_usage = [
            u for u in self._usage_history
            if u.timestamp >= cutoff
        ]
        
        if not recent_usage:
            return {"error": "No data in time window"}
        
        totals = [u.total_allocated for u in recent_usage]
        peaks = [u.peak_allocated for u in recent_usage]
        counts = [u.object_count for u in recent_usage]
        
        trend = "stable"
        if len(totals) >= 2:
            if totals[-1] > totals[0] * 1.2:
                trend = "increasing"
            elif totals[-1] < totals[0] * 0.8:
                trend = "decreasing"
        
        return {
            "time_window_minutes": minutes,
            "data_points": len(recent_usage),
            "trend": trend,
            "current_total": totals[-1] if totals else 0,
            "average_total": sum(totals) / len(totals) if totals else 0,
            "max_total": max(totals) if totals else 0,
            "min_total": min(totals) if totals else 0,
            "average_objects": sum(counts) / len(counts) if counts else 0
        }


_global_optimizer: Optional[MemoryOptimizer] = None


def get_memory_optimizer() -> MemoryOptimizer:
    """获取全局内存优化器"""
    global _global_optimizer
    if _global_optimizer is None:
        _global_optimizer = MemoryOptimizer()
    return _global_optimizer
