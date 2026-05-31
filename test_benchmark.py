"""
性能基准测试
基于第一性原理：可量化、可重复、可比较
"""
import sys
import os
import time
import statistics
from typing import Dict, List
from dataclasses import dataclass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.memory import get_memory_system
from src.preprocessing import get_preprocessor


@dataclass
class BenchmarkResult:
    """基准测试结果"""
    name: str
    iterations: int
    avg_time_ms: float
    median_time_ms: float
    min_time_ms: float
    max_time_ms: float
    throughput_ops_sec: float
    p95_time_ms: float
    p99_time_ms: float


class BenchmarkSuite:
    """基准测试套件"""
    
    def __init__(self, memory_system=None):
        self.memory_system = memory_system or get_memory_system()
        self.results: List[BenchmarkResult] = []
        self.session_id = "benchmark_session"
    
    def run_benchmark(
        self,
        name: str,
        func,
        iterations: int = 1000,
        warmup: int = 100
    ) -> BenchmarkResult:
        """运行单个基准测试"""
        # 预热
        for _ in range(warmup):
            func()
        
        # 正式测试
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            func()
            end = time.perf_counter()
            times.append((end - start) * 1000)  # 毫秒
        
        # 计算统计
        avg = statistics.mean(times)
        median = statistics.median(times)
        min_time = min(times)
        max_time = max(times)
        times_sorted = sorted(times)
        p95 = times_sorted[int(iterations * 0.95)]
        p99 = times_sorted[int(iterations * 0.99)]
        throughput = 1000 / avg if avg > 0 else 0
        
        result = BenchmarkResult(
            name=name,
            iterations=iterations,
            avg_time_ms=avg,
            median_time_ms=median,
            min_time_ms=min_time,
            max_time_ms=max_time,
            throughput_ops_sec=throughput,
            p95_time_ms=p95,
            p99_time_ms=p99
        )
        
        self.results.append(result)
        return result
    
    def benchmark_memory_add(self):
        """基准测试：添加记忆"""
        def _add():
            self.memory_system.add("测试记忆内容", self.session_id, "l2")
        return self.run_benchmark("Memory Add (L2)", _add, iterations=1000)
    
    def benchmark_memory_recall(self):
        """基准测试：召回记忆"""
        # 先添加一些数据
        for i in range(100):
            self.memory_system.add(f"测试内容{i}", self.session_id, "l2")
        
        def _recall():
            self.memory_system.recall("测试", self.session_id)
        return self.run_benchmark("Memory Recall", _recall, iterations=1000)
    
    def benchmark_preprocessing(self):
        """基准测试：预处理"""
        preprocessor = get_preprocessor()
        
        def _preprocess():
            preprocessor.process("这是一条测试消息，包含一些内容")
        return self.run_benchmark("Text Preprocessing", _preprocess, iterations=2000)
    
    def benchmark_fact_add(self):
        """基准测试：添加事实"""
        def _add_fact():
            self.memory_system.add_fact("测试实体", "测试属性", "测试值")
        return self.run_benchmark("Fact Add (L3)", _add_fact, iterations=500)
    
    def benchmark_batch_ops(self):
        """基准测试：批量操作"""
        def _batch_add():
            for i in range(10):
                self.memory_system.add(f"批量{i}", self.session_id, "l2")
        return self.run_benchmark("Batch Add (10x)", _batch_add, iterations=100)
    
    def run_all(self):
        """运行所有基准测试"""
        print("=" * 80)
        print("AGENT MEMORY SYSTEM - PERFORMANCE BENCHMARK")
        print("=" * 80)
        print()
        
        self.benchmark_memory_add()
        self.benchmark_memory_recall()
        self.benchmark_preprocessing()
        self.benchmark_fact_add()
        self.benchmark_batch_ops()
        
        self.print_summary()
    
    def print_summary(self):
        """打印基准测试总结"""
        print()
        print("=" * 80)
        print("BENCHMARK SUMMARY")
        print("=" * 80)
        print()
        
        header = (
            f"{'Test Name':<30} "
            f"{'Avg (ms)':<10} "
            f"{'Med (ms)':<10} "
            f"{'P95 (ms)':<10} "
            f"{'P99 (ms)':<10} "
            f"{'Throughput (ops/s)':<20}"
        )
        print(header)
        print("-" * 80)
        
        for result in self.results:
            line = (
                f"{result.name:<30} "
                f"{result.avg_time_ms:<10.2f} "
                f"{result.median_time_ms:<10.2f} "
                f"{result.p95_time_ms:<10.2f} "
                f"{result.p99_time_ms:<10.2f} "
                f"{result.throughput_ops_sec:<20.1f}"
            )
            print(line)
        
        print()
        print("=" * 80)


def main():
    """运行基准测试"""
    suite = BenchmarkSuite()
    suite.run_all()


if __name__ == "__main__":
    main()
