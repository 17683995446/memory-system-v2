"""
端到端测试框架
用于测试完整的用户场景和系统集成
"""
import time
import threading
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import traceback
from ..utils.logger import get_logger



class ScenarioStatus(Enum):
    """场景状态"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TestStep:
    """测试步骤"""
    step_id: str
    name: str
    action: Callable
    expected_result: Any = None
    timeout: float = 30.0
    retry_count: int = 0
    metadata: Dict = field(default_factory=dict)


@dataclass
class ScenarioResult:
    """场景结果"""
    scenario_name: str
    status: ScenarioStatus
    total_steps: int
    passed_steps: int
    failed_steps: int
    duration_ms: float
    error_message: str = ""
    step_results: List[Dict] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


@dataclass
class ModuleConnection:
    """模块连接"""
    source_module: str
    target_module: str
    connection_type: str
    test_func: Callable
    metadata: Dict = field(default_factory=dict)


class EndToEndScenario:
    """端到端测试场景"""
    
    def __init__(self, name: str, description: str = ""):
        self._logger = get_logger()
        self.name = name
        self.description = description
        self.steps: List[TestStep] = []
        self.setup_func: Optional[Callable] = None
        self.teardown_func: Optional[Callable] = None
        self._step_counter = 0
    
    def add_step(
        self,
        name: str,
        action: Callable,
        expected_result: Any = None,
        timeout: float = 30.0,
        retry_count: int = 0
    ) -> 'EndToEndScenario':
        """添加测试步骤"""
        self._step_counter += 1
        step_id = f"{self.name}_step_{self._step_counter:03d}"
        
        step = TestStep(
            step_id=step_id,
            name=name,
            action=action,
            expected_result=expected_result,
            timeout=timeout,
            retry_count=retry_count
        )
        
        self.steps.append(step)
        return self
    
    def setup(self, func: Callable) -> Callable:
        """设置前置函数"""
        self.setup_func = func
        return func
    
    def teardown(self, func: Callable) -> Callable:
        """设置后置函数"""
        self.teardown_func = func
        return func
    
    def run(self) -> ScenarioResult:
        """运行场景"""
        start_time = time.time()
        passed_steps = 0
        failed_steps = 0
        step_results = []
        error_message = ""
        
        # 运行setup
        if self.setup_func:
            try:
                self.setup_func()
            except Exception as e:
                return ScenarioResult(
                    scenario_name=self.name,
                    status=ScenarioStatus.FAILED,
                    total_steps=len(self.steps),
                    passed_steps=0,
                    failed_steps=len(self.steps),
                    duration_ms=(time.time() - start_time) * 1000,
                    error_message=f"Setup failed: {str(e)}",
                    step_results=[]
                )
        
        # 运行步骤
        for step in self.steps:
            step_result = self._run_step(step)
            step_results.append(step_result)
            
            if step_result['status'] == 'passed':
                passed_steps += 1
            else:
                failed_steps += 1
                error_message = step_result.get('error', '')
                break  # 遇到失败就停止
        
        # 运行teardown
        if self.teardown_func:
            try:
                self.teardown_func()
            except Exception:
                pass
        
        duration = (time.time() - start_time) * 1000
        status = ScenarioStatus.PASSED if failed_steps == 0 else ScenarioStatus.FAILED
        
        return ScenarioResult(
            scenario_name=self.name,
            status=status,
            total_steps=len(self.steps),
            passed_steps=passed_steps,
            failed_steps=failed_steps,
            duration_ms=duration,
            error_message=error_message,
            step_results=step_results
        )
    
    def _run_step(self, step: TestStep) -> Dict[str, Any]:
        """运行单个步骤"""
        attempts = step.retry_count + 1
        
        for attempt in range(attempts):
            try:
                # 带超时运行
                result = self._run_with_timeout(step.action, step.timeout)
                
                # 检查结果
                if step.expected_result is not None:
                    if result == step.expected_result or (callable(step.expected_result) and step.expected_result(result)):
                        return {
                            'step_id': step.step_id,
                            'step_name': step.name,
                            'status': 'passed',
                            'duration_ms': 0,
                            'result': result,
                            'attempt': attempt + 1
                        }
                    else:
                        return {
                            'step_id': step.step_id,
                            'step_name': step.name,
                            'status': 'failed',
                            'error': f"Expected {step.expected_result}, got {result}",
                            'attempt': attempt + 1
                        }
                else:
                    return {
                        'step_id': step.step_id,
                        'step_name': step.name,
                        'status': 'passed',
                        'duration_ms': 0,
                        'result': result,
                        'attempt': attempt + 1
                    }
                    
            except Exception as e:
                if attempt < attempts - 1:
                    continue
                return {
                    'step_id': step.step_id,
                    'step_name': step.name,
                    'status': 'failed',
                    'error': str(e),
                    'traceback': traceback.format_exc(),
                    'attempt': attempt + 1
                }
        
        return {
            'step_id': step.step_id,
            'step_name': step.name,
            'status': 'failed',
            'error': 'Max retries exceeded'
        }
    
    def _run_with_timeout(self, func: Callable, timeout: float) -> Any:
        """带超时运行函数"""
        result = {'value': None, 'exception': None}
        
        def target():
            try:
                result['value'] = func()
            except Exception as e:
                result['exception'] = e
        
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout)
        
        if thread.is_alive():
            raise TimeoutError(f"Step execution timed out after {timeout}s")
        
        if result['exception']:
            raise result['exception']
        
        return result['value']


class EndToEndTestFramework:
    """端到端测试框架"""
    
    def __init__(self):
        self.scenarios: Dict[str, EndToEndScenario] = {}
        self.results: Dict[str, ScenarioResult] = {}
        self._lock = threading.Lock()
    
    def create_scenario(self, name: str, description: str = "") -> EndToEndScenario:
        """创建测试场景"""
        with self._lock:
            scenario = EndToEndScenario(name, description)
            self.scenarios[name] = scenario
            return scenario
    
    def get_scenario(self, name: str) -> Optional[EndToEndScenario]:
        """获取测试场景"""
        return self.scenarios.get(name)
    
    def run_scenario(self, name: str) -> Optional[ScenarioResult]:
        """运行单个场景"""
        scenario = self.scenarios.get(name)
        if not scenario:
            return None
        
        result = scenario.run()
        self.results[name] = result
        return result
    
    def run_all(self) -> Dict[str, ScenarioResult]:
        """运行所有场景"""
        results = {}
        
        for name, scenario in self.scenarios.items():
            logger.info(f"\n运行端到端场景: {name}")
            result = scenario.run()
            results[name] = result
            self.results[name] = result
        
        return results
    
    def get_results(self) -> Dict[str, ScenarioResult]:
        """获取所有结果"""
        return self.results
    
    def generate_report(self, results: Dict[str, ScenarioResult]) -> str:
        """生成报告"""
        report = []
        report.append("=" * 70)
        report.append("端到端测试报告")
        report.append("=" * 70)
        
        total_scenarios = len(results)
        total_steps = sum(r.total_steps for r in results.values())
        total_passed = sum(r.passed_steps for r in results.values())
        total_failed = sum(r.failed_steps for r in results.values())
        
        passed_scenarios = sum(1 for r in results.values() if r.status == ScenarioStatus.PASSED)
        failed_scenarios = sum(1 for r in results.values() if r.status == ScenarioStatus.FAILED)
        
        for name, result in results.items():
            report.append(f"\n场景: {name}")
            report.append(f"  状态: {result.status.value}")
            report.append(f"  步骤: {result.passed_steps}/{result.total_steps} 通过")
            report.append(f"  耗时: {result.duration_ms:.2f}ms")
            
            if result.error_message:
                report.append(f"  错误: {result.error_message}")
            
            for step_result in result.step_results:
                status_symbol = "✓" if step_result['status'] == 'passed' else "✗"
                report.append(f"    {status_symbol} {step_result['step_name']}")
        
        report.append("\n" + "=" * 70)
        report.append(f"总计: {total_scenarios} 场景")
        report.append(f"  通过: {passed_scenarios}")
        report.append(f"  失败: {failed_scenarios}")
        report.append(f"总步骤: {total_steps}")
        report.append(f"  通过: {total_passed}")
        report.append(f"  失败: {total_failed}")
        
        success_rate = (total_passed / total_steps * 100) if total_steps > 0 else 0
        report.append(f"成功率: {success_rate:.2f}%")
        report.append("=" * 70)
        
        return "\n".join(report)


# 全局端到端测试框架
_e2e_framework = None


def get_e2e_framework() -> EndToEndTestFramework:
    """获取端到端测试框架"""
    global _e2e_framework
    if _e2e_framework is None:
        _e2e_framework = EndToEndTestFramework()
    return _e2e_framework
