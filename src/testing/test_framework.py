"""
测试和质量保证框架
基于第一性原理：确定性、可复现、全面覆盖、自动化
"""
import time
import traceback
import threading
import json
import os
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
from ..utils.logger import get_logger



class TestStatus(Enum):
    """测试状态"""
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"


class TestCategory(Enum):
    """测试分类"""
    UNIT = "unit"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"
    SECURITY = "security"
    END_TO_END = "end_to_end"


@dataclass
class TestResult:
    """测试结果"""
    test_name: str
    category: TestCategory
    status: TestStatus
    duration_ms: float
    error_message: str = ""
    traceback_info: str = ""
    metadata: Dict = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


@dataclass
class PerformanceMetric:
    """性能指标"""
    name: str
    min_ms: float = float('inf')
    max_ms: float = 0.0
    avg_ms: float = 0.0
    p50_ms: float = 0.0
    p95_ms: float = 0.0
    p99_ms: float = 0.0
    total_count: int = 0
    total_ms: float = 0.0
    measurements: List[float] = field(default_factory=list)


class TestSuite:
    """测试套件"""
    
    def __init__(self, name: str, category: TestCategory = TestCategory.UNIT):
        self._logger = get_logger()
        self.name = name
        self.category = category
        self.tests: List[Dict] = []  # {'func': Callable, 'tags': List[str], 'timeout': float}
        self.results: List[TestResult] = []
        self.setup_func: Optional[Callable] = None
        self.teardown_func: Optional[Callable] = None
    
    def setup(self, func: Callable) -> Callable:
        """设置前置函数"""
        self.setup_func = func
        return func
    
    def teardown(self, func: Callable) -> Callable:
        """设置后置函数"""
        self.teardown_func = func
        return func
    
    def add_test(self, test_func: Callable, tags: List[str] = None, timeout: float = None) -> None:
        """添加测试"""
        self.tests.append({
            'func': test_func,
            'tags': tags or [],
            'timeout': timeout or 30.0  # 默认30秒超时
        })
    
    def run(self, fail_fast: bool = False) -> Dict[str, Any]:
        """运行测试套件"""
        start_time = time.time()
        self.results = []
        
        for test_info in self.tests:
            if fail_fast and self.results:
                last_result = self.results[-1]
                if last_result.status in [TestStatus.FAILED, TestStatus.ERROR]:
                    break
            
            result = self._run_single_test(test_info)
            self.results.append(result)
        
        duration = (time.time() - start_time) * 1000
        
        return self._generate_report(duration)
    
    def _run_single_test(self, test_info: Dict) -> TestResult:
        """运行单个测试"""
        test_func = test_info['func']
        test_name = test_func.__name__
        tags = test_info['tags']
        timeout = test_info['timeout']
        start_time = time.time()
        
        # 运行setup
        if self.setup_func:
            try:
                self.setup_func()
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                return TestResult(
                    test_name=test_name,
                    category=self.category,
                    status=TestStatus.ERROR,
                    duration_ms=duration,
                    error_message=f"Setup failed: {str(e)}",
                    traceback_info=traceback.format_exc(),
                    tags=tags
                )
        
        result = None
        try:
            # 带超时运行
            if timeout:
                result = self._run_with_timeout(test_func, timeout)
            else:
                test_func()
                result = TestStatus.PASSED
            
            duration = (time.time() - start_time) * 1000
            return TestResult(
                test_name=test_name,
                category=self.category,
                status=result,
                duration_ms=duration,
                tags=tags
            )
        except AssertionError as e:
            duration = (time.time() - start_time) * 1000
            return TestResult(
                test_name=test_name,
                category=self.category,
                status=TestStatus.FAILED,
                duration_ms=duration,
                error_message=str(e),
                traceback_info=traceback.format_exc(),
                tags=tags
            )
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return TestResult(
                test_name=test_name,
                category=self.category,
                status=TestStatus.ERROR,
                duration_ms=duration,
                error_message=str(e),
                traceback_info=traceback.format_exc(),
                tags=tags
            )
        finally:
            # 运行teardown
            if self.teardown_func:
                try:
                    self.teardown_func()
                except Exception:
                    pass
    
    def _run_with_timeout(self, func: Callable, timeout: float) -> TestStatus:
        """带超时运行函数"""
        result = {'status': TestStatus.PASSED, 'exception': None}
        
        def target():
            try:
                func()
            except Exception as e:
                result['exception'] = e
        
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout)
        
        if thread.is_alive():
            return TestStatus.TIMEOUT
        
        if result['exception']:
            raise result['exception']
        
        return TestStatus.PASSED
    
    def _generate_report(self, total_duration: float) -> Dict[str, Any]:
        """生成报告"""
        passed = sum(1 for r in self.results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAILED)
        errors = sum(1 for r in self.results if r.status == TestStatus.ERROR)
        skipped = sum(1 for r in self.results if r.status == TestStatus.SKIPPED)
        timeout = sum(1 for r in self.results if r.status == TestStatus.TIMEOUT)
        
        return {
            'suite_name': self.name,
            'category': self.category.value,
            'total_tests': len(self.tests),
            'passed': passed,
            'failed': failed,
            'errors': errors,
            'skipped': skipped,
            'timeout': timeout,
            'total_duration_ms': total_duration,
            'results': [
                {
                    'name': r.test_name,
                    'category': r.category.value,
                    'status': r.status.value,
                    'duration_ms': r.duration_ms,
                    'error': r.error_message if r.status != TestStatus.PASSED else None,
                    'tags': r.tags
                }
                for r in self.results
            ]
        }


class PerformanceTester:
    """性能测试器"""
    
    def __init__(self):
        self.metrics: Dict[str, PerformanceMetric] = {}
    
    def measure(self, name: str, func: Callable, iterations: int = 100, warmup: int = 10) -> PerformanceMetric:
        """测量函数性能"""
        # 预热
        for _ in range(warmup):
            func()
        
        # 正式测量
        measurements = []
        for _ in range(iterations):
            start = time.time()
            func()
            duration = (time.time() - start) * 1000
            measurements.append(duration)
        
        # 计算统计
        metric = PerformanceMetric(
            name=name,
            measurements=measurements,
            total_count=iterations
        )
        
        if measurements:
            metric.min_ms = min(measurements)
            metric.max_ms = max(measurements)
            metric.total_ms = sum(measurements)
            metric.avg_ms = metric.total_ms / iterations
            
            # 计算百分位数
            sorted_ms = sorted(measurements)
            metric.p50_ms = sorted_ms[int(iterations * 0.5)]
            metric.p95_ms = sorted_ms[int(iterations * 0.95)]
            metric.p99_ms = sorted_ms[int(iterations * 0.99)]
        
        self.metrics[name] = metric
        return metric
    
    def get_metric(self, name: str) -> Optional[PerformanceMetric]:
        """获取性能指标"""
        return self.metrics.get(name)
    
    def generate_report(self) -> str:
        """生成性能报告"""
        report = []
        report.append("=" * 70)
        report.append("性能测试报告")
        report.append("=" * 70)
        
        for name, metric in self.metrics.items():
            report.append(f"\n{name}:")
            report.append(f"  运行次数: {metric.total_count}")
            report.append(f"  总耗时: {metric.total_ms:.2f}ms")
            report.append(f"  平均: {metric.avg_ms:.2f}ms")
            report.append(f"  最小: {metric.min_ms:.2f}ms")
            report.append(f"  最大: {metric.max_ms:.2f}ms")
            report.append(f"  P50: {metric.p50_ms:.2f}ms")
            report.append(f"  P95: {metric.p95_ms:.2f}ms")
            report.append(f"  P99: {metric.p99_ms:.2f}ms")
        
        report.append("\n" + "=" * 70)
        return "\n".join(report)


class IntegrationTester:
    """集成测试器"""
    
    def __init__(self):
        self.components: Dict[str, Any] = {}
        self.dependencies: Dict[str, List[str]] = defaultdict(list)
    
    def register_component(self, name: str, component: Any, depends_on: List[str] = None) -> None:
        """注册组件"""
        self.components[name] = component
        if depends_on:
            self.dependencies[name] = depends_on
    
    def test_component_integration(self, component_name: str) -> bool:
        """测试组件集成"""
        if component_name not in self.components:
            return False
        
        # 检查依赖
        for dep in self.dependencies.get(component_name, []):
            if dep not in self.components:
                return False
        
        return True


class TestingFramework:
    """综合测试框架"""
    
    def __init__(self):
        self.suites: Dict[str, TestSuite] = {}
        self.performance_tester = PerformanceTester()
        self.integration_tester = IntegrationTester()
        self._lock = threading.Lock()
    
    def create_suite(self, name: str, category: TestCategory = TestCategory.UNIT) -> TestSuite:
        """创建测试套件"""
        with self._lock:
            suite = TestSuite(name, category)
            self.suites[name] = suite
            return suite
    
    def get_suite(self, name: str) -> Optional[TestSuite]:
        """获取测试套件"""
        return self.suites.get(name)
    
    def run_all(self, fail_fast: bool = False) -> Dict[str, Any]:
        """运行所有测试套件"""
        all_results = {}
        
        for name, suite in self.suites.items():
            logger.info(f"\n运行测试套件: {name} ({suite.category.value})")
            result = suite.run(fail_fast)
            all_results[name] = result
        
        return all_results
    
    def run_by_category(self, category: TestCategory, fail_fast: bool = False) -> Dict[str, Any]:
        """按分类运行测试"""
        results = {}
        
        for name, suite in self.suites.items():
            if suite.category == category:
                logger.info(f"\n运行测试套件: {name}")
                result = suite.run(fail_fast)
                results[name] = result
        
        return results
    
    def run_by_tag(self, tag: str, fail_fast: bool = False) -> Dict[str, Any]:
        """按标签运行测试"""
        # 临时创建只包含匹配标签测试的套件
        results = {}
        
        for name, suite in self.suites.items():
            filtered_tests = [t for t in suite.tests if tag in t['tags']]
            if filtered_tests:
                temp_suite = TestSuite(f"{name}_{tag}", suite.category)
                temp_suite.tests = filtered_tests
                result = temp_suite.run(fail_fast)
                results[name] = result
        
        return results
    
    def generate_full_report(self, results: Dict[str, Any]) -> str:
        """生成完整报告"""
        report = []
        report.append("=" * 70)
        report.append("测试报告")
        report.append("=" * 70)
        
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_errors = 0
        total_skipped = 0
        total_timeout = 0
        
        for suite_name, result in results.items():
            report.append(f"\n测试套件: {suite_name} ({result['category']})")
            report.append(f"  总测试数: {result['total_tests']}")
            report.append(f"  通过: {result['passed']}")
            report.append(f"  失败: {result['failed']}")
            report.append(f"  错误: {result['errors']}")
            report.append(f"  跳过: {result['skipped']}")
            report.append(f"  超时: {result['timeout']}")
            report.append(f"  耗时: {result['total_duration_ms']:.2f}ms")
            
            total_tests += result['total_tests']
            total_passed += result['passed']
            total_failed += result['failed']
            total_errors += result['errors']
            total_skipped += result['skipped']
            total_timeout += result['timeout']
            
            # 显示失败/错误详情
            for test_result in result['results']:
                if test_result['status'] != 'passed':
                    report.append(f"    ✗ {test_result['name']}: {test_result['error']}")
        
        report.append("\n" + "=" * 70)
        report.append(f"总计: {total_tests} 测试")
        report.append(f"通过: {total_passed}")
        report.append(f"失败: {total_failed}")
        report.append(f"错误: {total_errors}")
        report.append(f"跳过: {total_skipped}")
        report.append(f"超时: {total_timeout}")
        
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        report.append(f"成功率: {success_rate:.2f}%")
        report.append("=" * 70)
        
        return "\n".join(report)
    
    def save_report(self, results: Dict[str, Any], filepath: str) -> None:
        """保存报告到文件"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
    
    def load_report(self, filepath: str) -> Dict[str, Any]:
        """从文件加载报告"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)


# 全局测试框架
_testing_framework = None


def get_testing_framework() -> TestingFramework:
    """获取测试框架"""
    global _testing_framework
    if _testing_framework is None:
        _testing_framework = TestingFramework()
    return _testing_framework


# 断言辅助函数
def assert_equal(actual: Any, expected: Any, message: str = ""):
    """断言相等"""
    if actual != expected:
        raise AssertionError(f"{message}: expected {expected}, got {actual}")


def assert_true(condition: bool, message: str = ""):
    """断言为真"""
    if not condition:
        raise AssertionError(f"{message}: expected True, got False")


def assert_false(condition: bool, message: str = ""):
    """断言为假"""
    if condition:
        raise AssertionError(f"{message}: expected False, got True")


def assert_not_none(value: Any, message: str = ""):
    """断言不为空"""
    if value is None:
        raise AssertionError(f"{message}: expected not None")


def assert_none(value: Any, message: str = ""):
    """断言为空"""
    if value is not None:
        raise AssertionError(f"{message}: expected None, got {value}")


def assert_in(item: Any, container: Any, message: str = ""):
    """断言包含"""
    if item not in container:
        raise AssertionError(f"{message}: {item} not in {container}")


def assert_not_in(item: Any, container: Any, message: str = ""):
    """断言不包含"""
    if item in container:
        raise AssertionError(f"{message}: {item} in {container}")


def assert_raises(exception_type: type, func: Callable, *args, **kwargs):
    """断言抛出异常"""
    try:
        func(*args, **kwargs)
        raise AssertionError(f"Expected {exception_type.__name__} but no exception was raised")
    except exception_type:
        pass
    except Exception as e:
        raise AssertionError(f"Expected {exception_type.__name__} but got {type(e).__name__}")


def assert_greater(a: float, b: float, message: str = ""):
    """断言大于"""
    if a <= b:
        raise AssertionError(f"{message}: {a} not greater than {b}")


def assert_less(a: float, b: float, message: str = ""):
    """断言小于"""
    if a >= b:
        raise AssertionError(f"{message}: {a} not less than {b}")


def assert_almost_equal(a: float, b: float, places: int = 7, message: str = ""):
    """断言近似相等"""
    if round(abs(a - b), places) != 0:
        raise AssertionError(f"{message}: {a} not almost equal to {b}")
