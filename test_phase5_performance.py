"""
第5阶段：性能测试（简化版）
"""
import sys
import os
import time
import tracemalloc
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.memory import get_memory_system
from src.preprocessing import get_preprocessor


def test_write_performance():
    """测试写入性能"""
    print("\n" + "="*70)
    print("性能测试1: 写入性能")
    print("="*70)
    
    memory = get_memory_system()
    task_id = "perf_test_write"
    
    # 记录开始状态
    tracemalloc.start()
    start_time = time.time()
    
    # 执行写入
    write_count = 100
    for i in range(write_count):
        memory.add(f"性能测试数据{i}", task_id, "l2")
    
    # 记录结束状态
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    duration = (end_time - start_time) * 1000
    
    print(f"\n[结果]")
    print(f"  写入次数: {write_count}")
    print(f"  总耗时: {duration:.2f}ms")
    print(f"  平均耗时: {duration/write_count:.2f}ms/次")
    print(f"  吞吐量: {write_count/(duration/1000):.2f}次/秒")
    print(f"  内存使用: {current/1024/1024:.2f}MB (峰值: {peak/1024/1024:.2f}MB)")


def test_recall_performance():
    """测试召回性能"""
    print("\n" + "="*70)
    print("性能测试2: 召回性能")
    print("="*70)
    
    memory = get_memory_system()
    
    # 先添加一些数据
    task_id = "perf_test_recall"
    for i in range(50):
        memory.add(f"召回测试数据{i}", task_id, "l2")
    
    # 测试召回
    tracemalloc.start()
    start_time = time.time()
    
    recall_count = 50
    for i in range(recall_count):
        memory.recall("测试数据", task_id)
    
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    duration = (end_time - start_time) * 1000
    
    print(f"\n[结果]")
    print(f"  召回次数: {recall_count}")
    print(f"  总耗时: {duration:.2f}ms")
    print(f"  平均耗时: {duration/recall_count:.2f}ms/次")
    print(f"  吞吐量: {recall_count/(duration/1000):.2f}次/秒")
    print(f"  内存使用: {current/1024/1024:.2f}MB (峰值: {peak/1024/1024:.2f}MB)")


def test_preprocessing_performance():
    """测试预处理性能"""
    print("\n" + "="*70)
    print("性能测试3: 预处理性能")
    print("="*70)
    
    preprocessor = get_preprocessor()
    
    test_texts = [
        "用户询问天气情况",
        "我的手机号是13812345678，邮箱test@example.com",
        "这是一个包含多种信息的测试文本，用于验证预处理性能",
    ]
    
    tracemalloc.start()
    start_time = time.time()
    
    process_count = 1000
    for i in range(process_count):
        for text in test_texts:
            preprocessor.process(text, check_hallucination=False)
    
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    duration = (end_time - start_time) * 1000
    total_processes = process_count * len(test_texts)
    
    print(f"\n[结果]")
    print(f"  处理次数: {total_processes}")
    print(f"  总耗时: {duration:.2f}ms")
    print(f"  平均耗时: {duration/total_processes:.3f}ms/次")
    print(f"  吞吐量: {total_processes/(duration/1000):.2f}次/秒")
    print(f"  内存使用: {current/1024/1024:.2f}MB (峰值: {peak/1024/1024:.2f}MB)")


def test_concurrent_performance():
    """测试并发性能"""
    print("\n" + "="*70)
    print("性能测试4: 并发性能")
    print("="*70)
    
    memory = get_memory_system()
    
    def concurrent_operations(task_id):
        for i in range(20):
            memory.add(f"并发数据{i}", task_id, "l2")
            if i % 5 == 0:
                memory.recall("数据", task_id)
    
    tracemalloc.start()
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(concurrent_operations, f"concurrent_{i}") for i in range(10)]
        for future in futures:
            future.result()
    
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    duration = (end_time - start_time) * 1000
    total_operations = 10 * 20 * 2  # 10个线程 * 20次 * 2种操作
    
    print(f"\n[结果]")
    print(f"  并发线程: 10")
    print(f"  总操作数: {total_operations}")
    print(f"  总耗时: {duration:.2f}ms")
    print(f"  平均耗时: {duration/total_operations:.2f}ms/次")
    print(f"  吞吐量: {total_operations/(duration/1000):.2f}次/秒")
    print(f"  内存使用: {current/1024/1024:.2f}MB (峰值: {peak/1024/1024:.2f}MB)")


def test_memory_usage():
    """测试内存占用"""
    print("\n" + "="*70)
    print("性能测试5: 内存占用测试")
    print("="*70)
    
    memory = get_memory_system()
    
    tracemalloc.start()
    current_before, _ = tracemalloc.get_traced_memory()
    
    # 添加大量数据
    print("\n[操作] 添加1000条L2记忆")
    task_id = "memory_test"
    for i in range(1000):
        memory.add(f"内存测试数据{i}，这是一个比较长的字符串用于测试", task_id, "l2")
    
    current_after, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    print(f"\n[结果]")
    print(f"  添加前内存: {current_before/1024/1024:.2f}MB")
    print(f"  添加后内存: {current_after/1024/1024:.2f}MB")
    print(f"  增量: {(current_after-current_before)/1024/1024:.2f}MB")
    print(f"  峰值内存: {peak/1024/1024:.2f}MB")
    print(f"  平均每条: {(current_after-current_before)/1000/1024:.2f}KB")


def run_performance_tests():
    """运行所有性能测试"""
    print("\n" + "="*70)
    print("第5阶段：性能测试")
    print("="*70)
    
    try:
        test_write_performance()
        test_recall_performance()
        test_preprocessing_performance()
        test_concurrent_performance()
        test_memory_usage()
        
        print("\n" + "="*70)
        print("✓ 所有性能测试完成！")
        print("="*70)
        
    except Exception as e:
        print(f"\n✗ 性能测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_performance_tests()
