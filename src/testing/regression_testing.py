"""
回归测试套件管理器
用于管理回归测试，确保系统稳定性
"""
import time
import json
import os
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from ..utils.logger import get_logger



class RegressionStatus(Enum):
    """回归状态"""
    STABLE = "stable"
    UNSTABLE = "unstable"
    FAILING = "failing"
    SKIPPED = "skipped"


@dataclass
class RegressionTest:
    """回归测试"""
    test_id: str
    name: str
    test_func: Callable
    module: str
    priority: int = 1  # 1-5, 1 is highest
    tags: List[str] = field(default_factory=list)
    flaky: bool = False
    baseline_duration_ms: float = 0.0


@dataclass
class RegressionResult:
    """回归测试结果"""
    test_name: str
    module: str
    passed: bool
    duration_ms: float
    timestamp: datetime
    flaky: bool = False
    error_message: str = ""
    metadata: Dict = field(default_factory=dict)


@dataclass
class RegressionSuite:
    """回归测试套件"""
    suite_id: str
    name: str
    description: str
    tests: List[RegressionTest]
    baseline_pass_rate: float = 100.0
    current_pass_rate: float = 100.0
    last_run: Optional[datetime] = None


class RegressionTestManager:
    """回归测试管理器"""
    
    def __init__(self):
        self._logger = get_logger()
        self.suites: Dict[str, RegressionSuite] = {}
        self.tests: Dict[str, RegressionTest] = {}
        self.results: List[RegressionResult] = []
        self._test_counter = 0
        self._suite_counter = 0
    
    def create_suite(
        self,
        name: str,
        description: str = "",
        baseline_pass_rate: float = 100.0
    ) -> str:
        """创建回归测试套件"""
        self._suite_counter += 1
        suite_id = f"REGSUIT-{self._suite_counter:04d}"
        
        suite = RegressionSuite(
            suite_id=suite_id,
            name=name,
            description=description,
            tests=[],
            baseline_pass_rate=baseline_pass_rate
        )
        
        self.suites[suite_id] = suite
        return suite_id
    
    def register_test(
        self,
        name: str,
        test_func: Callable,
        module: str,
        priority: int = 3,
        tags: List[str] = None,
        flaky: bool = False
    ) -> str:
        """注册回归测试"""
        self._test_counter += 1
        test_id = f"REGTEST-{self._test_counter:04d}"
        
        test = RegressionTest(
            test_id=test_id,
            name=name,
            test_func=test_func,
            module=module,
            priority=priority,
            tags=tags or [],
            flaky=flaky
        )
        
        self.tests[test_id] = test
        return test_id
    
    def add_test_to_suite(self, suite_id: str, test_id: str) -> bool:
        """添加测试到套件"""
        if suite_id not in self.suites or test_id not in self.tests:
            return False
        
        suite = self.suites[suite_id]
        test = self.tests[test_id]
        
        if test not in suite.tests:
            suite.tests.append(test)
        
        return True
    
    def run_test(self, test_id: str) -> Optional[RegressionResult]:
        """运行单个回归测试"""
        if test_id not in self.tests:
            return None
        
        test = self.tests[test_id]
        start_time = time.time()
        
        try:
            test.test_func()
            
            duration = (time.time() - start_time) * 1000
            
            # 更新baseline duration
            if test.baseline_duration_ms == 0:
                test.baseline_duration_ms = duration
            
            result = RegressionResult(
                test_name=test.name,
                module=test.module,
                passed=True,
                duration_ms=duration,
                timestamp=datetime.now(),
                flaky=test.flaky
            )
            
            self.results.append(result)
            return result
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            result = RegressionResult(
                test_name=test.name,
                module=test.module,
                passed=False,
                duration_ms=duration,
                timestamp=datetime.now(),
                flaky=test.flaky,
                error_message=str(e)
            )
            
            self.results.append(result)
            return result
    
    def run_suite(self, suite_id: str) -> Dict[str, RegressionResult]:
        """运行回归测试套件"""
        if suite_id not in self.suites:
            return {}
        
        suite = self.suites[suite_id]
        results = {}
        
        # 按优先级排序
        sorted_tests = sorted(suite.tests, key=lambda t: t.priority)
        
        for test in sorted_tests:
            result = self.run_test(test.test_id)
            if result:
                results[test.test_id] = result
        
        # 更新套件状态
        suite.last_run = datetime.now()
        total = len(results)
        passed = sum(1 for r in results.values() if r.passed)
        suite.current_pass_rate = (passed / total * 100) if total > 0 else 0
        
        return results
    
    def run_all(self) -> Dict[str, Dict[str, RegressionResult]]:
        """运行所有回归测试套件"""
        all_results = {}
        
        for suite_id in self.suites:
            logger.info(f"\n运行回归测试套件: {self.suites[suite_id].name}")
            results = self.run_suite(suite_id)
            all_results[suite_id] = results
        
        return all_results
    
    def get_stability_trend(self, test_name: str, days: int = 7) -> Dict[str, Any]:
        """获取稳定性趋势"""
        cutoff = datetime.now()
        recent_results = [
            r for r in self.results
            if r.test_name == test_name and
            (cutoff - r.timestamp).days <= days
        ]
        
        if not recent_results:
            return {'trend': 'no_data', 'pass_rate': 0, 'total': 0}
        
        passed = sum(1 for r in recent_results if r.passed)
        pass_rate = (passed / len(recent_results)) * 100
        
        # 计算趋势
        if len(recent_results) >= 3:
            first_half = recent_results[:len(recent_results)//2]
            second_half = recent_results[len(recent_results)//2:]
            
            first_rate = sum(1 for r in first_half if r.passed) / len(first_half) * 100
            second_rate = sum(1 for r in second_half if r.passed) / len(second_half) * 100
            
            if second_rate > first_rate:
                trend = 'improving'
            elif second_rate < first_rate:
                trend = 'degrading'
            else:
                trend = 'stable'
        else:
            trend = 'insufficient_data'
        
        return {
            'trend': trend,
            'pass_rate': pass_rate,
            'total': len(recent_results),
            'passed': passed,
            'failed': len(recent_results) - passed
        }
    
    def identify_flaky_tests(self) -> List[str]:
        """识别不稳定的测试"""
        flaky_tests = []
        
        for test_id, test in self.tests.items():
            if not test.flaky:
                continue
            
            # 获取最近的测试结果
            recent = [
                r for r in self.results
                if r.test_name == test.name
            ][-10:]  # 最近10次
            
            if len(recent) >= 5:
                passed = sum(1 for r in recent if r.passed)
                pass_rate = passed / len(recent)
                
                # 如果通过率在40%-60%之间，认为是不稳定的
                if 0.4 <= pass_rate <= 0.6:
                    flaky_tests.append(test.name)
        
        return flaky_tests
    
    def generate_baseline_report(self) -> str:
        """生成基线报告"""
        report = []
        report.append("=" * 70)
        report.append("回归测试基线报告")
        report.append("=" * 70)
        
        for suite_id, suite in self.suites.items():
            report.append(f"\n测试套件: {suite.name}")
            report.append(f"  描述: {suite.description}")
            report.append(f"  测试数量: {len(suite.tests)}")
            report.append(f"  基线通过率: {suite.baseline_pass_rate:.1f}%")
            report.append(f"  当前通过率: {suite.current_pass_rate:.1f}%")
            
            if suite.last_run:
                report.append(f"  上次运行: {suite.last_run}")
        
        # 性能基线
        report.append("\n性能基线:")
        for test_id, test in self.tests.items():
            if test.baseline_duration_ms > 0:
                report.append(f"  {test.name}: {test.baseline_duration_ms:.2f}ms")
        
        report.append("\n" + "=" * 70)
        return "\n".join(report)
    
    def generate_report(self, results: Dict[str, RegressionResult]) -> str:
        """生成回归测试报告"""
        report = []
        report.append("=" * 70)
        report.append("回归测试报告")
        report.append("=" * 70)
        
        # 按模块分组
        by_module = {}
        for test_id, result in results.items():
            if result.module not in by_module:
                by_module[result.module] = []
            by_module[result.module].append(result)
        
        for module, module_results in by_module.items():
            report.append(f"\n模块: {module}")
            
            passed = sum(1 for r in module_results if r.passed)
            failed = sum(1 for r in module_results if not r.passed)
            
            report.append(f"  通过: {passed}, 失败: {failed}")
            
            for result in module_results:
                status = "✓" if result.passed else "✗"
                report.append(f"    {status} {result.test_name} ({result.duration_ms:.2f}ms)")
                if result.error_message:
                    report.append(f"      错误: {result.error_message}")
        
        # 不稳定测试
        flaky = self.identify_flaky_tests()
        if flaky:
            report.append("\n不稳定测试:")
            for test_name in flaky:
                report.append(f"  ⚠ {test_name}")
        
        total_passed = sum(1 for r in results.values() if r.passed)
        total_failed = sum(1 for r in results.values() if not r.passed)
        
        report.append("\n" + "=" * 70)
        report.append(f"总计: {len(results)} 测试")
        report.append(f"  通过: {total_passed}")
        report.append(f"  失败: {total_failed}")
        
        success_rate = (total_passed / len(results) * 100) if len(results) > 0 else 0
        report.append(f"成功率: {success_rate:.2f}%")
        report.append("=" * 70)
        
        return "\n".join(report)
    
    def save_baseline(self, filepath: str) -> bool:
        """保存基线"""
        data = {
            'suites': [],
            'tests': [],
            'timestamp': datetime.now().isoformat()
        }
        
        for suite_id, suite in self.suites.items():
            data['suites'].append({
                'suite_id': suite_id,
                'name': suite.name,
                'baseline_pass_rate': suite.baseline_pass_rate
            })
        
        for test_id, test in self.tests.items():
            data['tests'].append({
                'test_id': test_id,
                'name': test.name,
                'module': test.module,
                'baseline_duration_ms': test.baseline_duration_ms
            })
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return True
    
    def load_baseline(self, filepath: str) -> bool:
        """加载基线"""
        if not os.path.exists(filepath):
            return False
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 恢复基线数据
        for test_data in data.get('tests', []):
            test_id = test_data['test_id']
            if test_id in self.tests:
                self.tests[test_id].baseline_duration_ms = test_data['baseline_duration_ms']
        
        return True


# 全局回归测试管理器
_regression_manager = None


def get_regression_manager() -> RegressionTestManager:
    """获取回归测试管理器"""
    global _regression_manager
    if _regression_manager is None:
        _regression_manager = RegressionTestManager()
    return _regression_manager
