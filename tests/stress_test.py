#!/usr/bin/env python3
"""
复杂场景压力测试
目标：更长时间、更大规模、更错综复杂、更高难度、涉及更混乱的场景
验证：系统在极端条件下的稳定性、正确性、数据一致性
"""

import sys
import os
import time
import threading
import random
import string
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

sys.path.insert(0, '/workspace')

from src.memory import get_memory_system
from src.utils.logger import get_logger

logger = get_logger()


class ChaosMonkey:
    """混沌猴子 - 模拟各种混乱场景"""

    @staticmethod
    def random_string(min_len=1, max_len=1000):
        """生成随机字符串"""
        length = random.randint(min_len, max_len)
        chars = string.ascii_letters + string.digits + string.punctuation + " \t\n"
        return ''.join(random.choice(chars) for _ in range(length))

    @staticmethod
    def random_unicode(min_len=1, max_len=500):
        """生成随机Unicode字符串"""
        length = random.randint(min_len, max_len)
        # 包含中文、日文、韩文、emoji等
        ranges = [
            (0x4E00, 0x9FFF),  # CJK
            (0x3040, 0x309F),  # Hiragana
            (0xAC00, 0xD7AF),  # Korean
            (0x1F600, 0x1F64F),  # Emoji
        ]
        result = []
        for _ in range(length):
            r = random.choice(ranges)
            result.append(chr(random.randint(r[0], r[1])))
        return ''.join(result)

    @staticmethod
    def corrupt_data():
        """生成损坏的数据"""
        choices = [
            None,
            {},
            [],
            {"nested": {"deeply": {"nested": "value" * 1000}}},
            b"binary_data_\x00\x01\x02",
            float('inf'),
            float('-inf'),
            "",
            "a" * 1000000,  # 1MB string
        ]
        return random.choice(choices)


class StressTester:
    """压力测试器"""

    def __init__(self):
        self.memory = get_memory_system()
        self.chaos = ChaosMonkey()
        self.errors = []
        self.stats = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "start_time": time.time()
        }
        self._stats_lock = threading.Lock()

    def _record_op(self, success: bool):
        """记录操作结果"""
        with self._stats_lock:
            self.stats["total_operations"] += 1
            if success:
                self.stats["successful_operations"] += 1
            else:
                self.stats["failed_operations"] += 1

    def scenario_massive_add(self, count: int = 10000):
        """场景1: 大规模添加"""
        logger.info(f"[Stress] 场景1: 大规模添加 {count} 条记忆")
        task_id = f"massive_{int(time.time() * 1000)}"

        for i in range(count):
            try:
                text = self.chaos.random_string(10, 500)
                self.memory.add(text, task_id)
                self._record_op(True)
            except Exception as e:
                self._record_op(False)
                self.errors.append(f"massive_add[{i}]: {e}")

        logger.info(f"[Stress] 场景1完成: 成功={self.stats['successful_operations']} 失败={self.stats['failed_operations']}")

    def scenario_rapid_add_delete(self, count: int = 5000):
        """场景2: 快速添加删除交替"""
        logger.info(f"[Stress] 场景2: 快速添加删除交替 {count} 次")
        task_id = f"rapid_{int(time.time() * 1000)}"
        added_keys = []

        for i in range(count):
            try:
                if random.random() > 0.3 or len(added_keys) == 0:
                    # 添加
                    text = self.chaos.random_string(5, 200)
                    self.memory.add(text, task_id)
                    added_keys.append(text)
                    self._record_op(True)
                else:
                    # 删除
                    key = random.choice(added_keys)
                    self.memory.delete(key)
                    added_keys.remove(key)
                    self._record_op(True)
            except Exception as e:
                self._record_op(False)
                self.errors.append(f"rapid_add_delete[{i}]: {e}")

        logger.info(f"[Stress] 场景2完成")

    def scenario_concurrent_chaos(self, threads: int = 50, ops_per_thread: int = 200):
        """场景3: 多线程并发混乱操作"""
        logger.info(f"[Stress] 场景3: {threads}线程并发混乱操作，每线程{ops_per_thread}次")

        def worker(thread_id: int):
            task_id = f"chaos_thread_{thread_id}"
            local_errors = []
            for i in range(ops_per_thread):
                try:
                    op = random.randint(0, 5)
                    if op == 0:
                        # 添加正常数据
                        self.memory.add(self.chaos.random_string(10, 300), task_id)
                    elif op == 1:
                        # 添加Unicode数据
                        self.memory.add(self.chaos.random_unicode(5, 100), task_id)
                    elif op == 2:
                        # 召回
                        self.memory.recall(self.chaos.random_string(5, 50), task_id)
                    elif op == 3:
                        # 添加事实
                        self.memory.add_fact(
                            self.chaos.random_string(3, 20),
                            self.chaos.random_string(3, 20),
                            self.chaos.random_string(5, 100)
                        )
                    elif op == 4:
                        # 获取统计
                        self.memory.get_statistics()
                    elif op == 5:
                        # 一致性检查
                        self.memory.check_consistency()
                    self._record_op(True)
                except Exception as e:
                    self._record_op(False)
                    local_errors.append(f"thread_{thread_id}[{i}]: {e}")
            return local_errors

        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = [executor.submit(worker, i) for i in range(threads)]
            for future in as_completed(futures):
                errs = future.result()
                self.errors.extend(errs)

        logger.info(f"[Stress] 场景3完成")

    def scenario_memory_pressure(self, count: int = 5000):
        """场景4: 内存压力测试 - 大量大对象"""
        logger.info(f"[Stress] 场景4: 内存压力测试 {count} 条大对象")
        task_id = f"pressure_{int(time.time() * 1000)}"

        for i in range(count):
            try:
                # 生成大文本（1KB - 100KB）
                size = random.randint(1024, 100 * 1024)
                text = "X" * size
                self.memory.add(text, task_id)
                self._record_op(True)

                # 每100条清理一次L1，防止内存溢出
                if i % 100 == 0:
                    self.memory.end_task(task_id)
                    task_id = f"pressure_{int(time.time() * 1000)}_{i}"
            except Exception as e:
                self._record_op(False)
                self.errors.append(f"memory_pressure[{i}]: {e}")

        logger.info(f"[Stress] 场景4完成")

    def scenario_long_running(self, duration_seconds: int = 60):
        """场景5: 长时间运行测试"""
        logger.info(f"[Stress] 场景5: 长时间运行测试 {duration_seconds}秒")
        start = time.time()
        task_id = f"longrun_{int(start * 1000)}"
        iteration = 0

        while time.time() - start < duration_seconds:
            iteration += 1
            try:
                # 混合操作
                op = random.randint(0, 4)
                if op == 0:
                    self.memory.add(self.chaos.random_string(10, 200), task_id)
                elif op == 1:
                    self.memory.recall(self.chaos.random_string(5, 50), task_id)
                elif op == 2:
                    self.memory.get_statistics()
                elif op == 3:
                    self.memory.check_consistency()
                elif op == 4:
                    self.memory.save()
                self._record_op(True)
            except Exception as e:
                self._record_op(False)
                self.errors.append(f"long_running[{iteration}]: {e}")

            # 每1000次操作换task
            if iteration % 1000 == 0:
                self.memory.end_task(task_id)
                task_id = f"longrun_{int(time.time() * 1000)}"
                logger.info(f"[Stress] 长时间运行: 已完成{iteration}次操作")

        logger.info(f"[Stress] 场景5完成: 共{iteration}次操作")

    def scenario_boundary_extremes(self):
        """场景6: 极端边界条件"""
        logger.info("[Stress] 场景6: 极端边界条件")
        task_id = "boundary_extreme"

        test_cases = [
            ("", "空字符串"),
            ("a", "单字符"),
            ("a" * 10000000, "10MB字符串"),
            ("\x00" * 100, "空字节"),
            ("\n" * 1000, "换行符"),
            ("<script>alert('xss')</script>", "XSS尝试"),
            ("'; DROP TABLE triples; --", "SQL注入尝试"),
            ("../../etc/passwd", "路径遍历尝试"),
        ]

        for text, desc in test_cases:
            try:
                self.memory.add(text, task_id)
                self._record_op(True)
                logger.info(f"[Stress] 边界测试通过: {desc}")
            except Exception as e:
                self._record_op(False)
                logger.info(f"[Stress] 边界测试异常(可能预期): {desc}: {e}")

        logger.info("[Stress] 场景6完成")

    def scenario_backup_recovery(self):
        """场景7: 备份恢复测试"""
        logger.info("[Stress] 场景7: 备份恢复测试")

        try:
            # 添加一些数据
            task_id = "backup_test"
            for i in range(100):
                self.memory.add(f"backup_data_{i}", task_id)

            # 创建备份
            backup_ok = self.memory.backup("./data/stress_backups")
            self._record_op(backup_ok)

            # 一致性检查
            ok, report = self.memory.check_consistency()
            self._record_op(ok)
            logger.info(f"[Stress] 备份前一致性: {ok}, errors={len(report['errors'])}")

            # 保存
            save_ok = self.memory.save()
            self._record_op(save_ok)

            logger.info("[Stress] 场景7完成")
        except Exception as e:
            self._record_op(False)
            self.errors.append(f"backup_recovery: {e}")

    def run_all_stress_tests(self):
        """运行所有压力测试"""
        logger.info("=" * 80)
        logger.info("开始复杂场景压力测试")
        logger.info("=" * 80)

        test_start = time.time()

        # 场景1: 大规模添加
        self.scenario_massive_add(5000)

        # 场景2: 快速添加删除
        self.scenario_rapid_add_delete(2000)

        # 场景3: 多线程并发混乱
        self.scenario_concurrent_chaos(threads=30, ops_per_thread=100)

        # 场景4: 内存压力
        self.scenario_memory_pressure(1000)

        # 场景5: 长时间运行（缩短为10秒以快速验证）
        self.scenario_long_running(10)

        # 场景6: 极端边界
        self.scenario_boundary_extremes()

        # 场景7: 备份恢复
        self.scenario_backup_recovery()

        test_duration = time.time() - test_start

        # 最终一致性检查
        final_ok, final_report = self.memory.check_consistency()

        # 打印报告
        logger.info("\n" + "=" * 80)
        logger.info("压力测试总结报告")
        logger.info("=" * 80)
        logger.info(f"测试耗时: {test_duration:.2f}秒")
        logger.info(f"总操作数: {self.stats['total_operations']}")
        logger.info(f"成功: {self.stats['successful_operations']}")
        logger.info(f"失败: {self.stats['failed_operations']}")
        logger.info(f"成功率: {self.stats['successful_operations'] / max(1, self.stats['total_operations']) * 100:.2f}%")
        logger.info(f"错误数: {len(self.errors)}")
        logger.info(f"最终一致性检查: {'通过' if final_ok else '失败'}")
        logger.info(f"L1数量: {self.memory.l1.size()}")
        logger.info(f"L2数量: {self.memory.l2.size()}")
        logger.info(f"L3数量: {self.memory.l3.size()}")

        if self.errors:
            logger.info("\n错误样本(前10条):")
            for err in self.errors[:10]:
                logger.info(f"  - {err}")

        logger.info("=" * 80)

        return len(self.errors) == 0 and final_ok


if __name__ == "__main__":
    tester = StressTester()
    success = tester.run_all_stress_tests()
    sys.exit(0 if success else 1)
