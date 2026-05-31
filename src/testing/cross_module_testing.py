"""
跨模块集成测试框架
用于测试不同模块之间的交互和集成
"""
import time
from typing import Dict, List, Callable, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum


class IntegrationLevel(Enum):
    """集成级别"""
    UNIT = "unit"           # 模块内部
    INTEGRATION = "integration"  # 模块之间
    SYSTEM = "system"       # 系统级别
    END_TO_END = "e2e"      # 端到端


@dataclass
class ModuleInterface:
    """模块接口"""
    module_name: str
    inputs: List[str]
    outputs: List[str]
    dependencies: List[str]
    metadata: Dict = field(default_factory=dict)


@dataclass
class IntegrationTest:
    """集成测试"""
    test_id: str
    name: str
    source_module: str
    target_module: str
    test_func: Callable
    level: IntegrationLevel
    description: str = ""
    expected_behavior: str = ""
    timeout: float = 30.0


@dataclass
class IntegrationResult:
    """集成测试结果"""
    test_name: str
    source_module: str
    target_module: str
    level: IntegrationLevel
    passed: bool
    duration_ms: float
    error_message: str = ""
    metadata: Dict = field(default_factory=dict)


@dataclass
class DependencyGraph:
    """依赖图"""
    nodes: List[str]
    edges: Dict[str, List[str]]


class CrossModuleTester:
    """跨模块测试器"""
    
    def __init__(self):
        self.modules: Dict[str, ModuleInterface] = {}
        self.integration_tests: List[IntegrationTest] = {}
        self.results: Dict[str, IntegrationResult] = {}
        self._test_counter = 0
    
    def register_module(
        self,
        module_name: str,
        inputs: List[str],
        outputs: List[str],
        dependencies: List[str] = None
    ) -> None:
        """注册模块"""
        module = ModuleInterface(
            module_name=module_name,
            inputs=inputs,
            outputs=outputs,
            dependencies=dependencies or []
        )
        self.modules[module_name] = module
    
    def add_integration_test(
        self,
        name: str,
        source_module: str,
        target_module: str,
        test_func: Callable,
        level: IntegrationLevel = IntegrationLevel.INTEGRATION,
        description: str = "",
        expected_behavior: str = "",
        timeout: float = 30.0
    ) -> str:
        """添加集成测试"""
        self._test_counter += 1
        test_id = f"INT-{self._test_counter:04d}"
        
        test = IntegrationTest(
            test_id=test_id,
            name=name,
            source_module=source_module,
            target_module=target_module,
            test_func=test_func,
            level=level,
            description=description,
            expected_behavior=expected_behavior,
            timeout=timeout
        )
        
        self.integration_tests[test_id] = test
        return test_id
    
    def run_integration_test(self, test_id: str) -> Optional[IntegrationResult]:
        """运行单个集成测试"""
        if test_id not in self.integration_tests:
            return None
        
        test = self.integration_tests[test_id]
        start_time = time.time()
        
        try:
            # 检查模块是否注册
            if test.source_module not in self.modules:
                return IntegrationResult(
                    test_name=test.name,
                    source_module=test.source_module,
                    target_module=test.target_module,
                    level=test.level,
                    passed=False,
                    duration_ms=(time.time() - start_time) * 1000,
                    error_message=f"Source module {test.source_module} not registered"
                )
            
            if test.target_module not in self.modules:
                return IntegrationResult(
                    test_name=test.name,
                    source_module=test.source_module,
                    target_module=test.target_module,
                    level=test.level,
                    passed=False,
                    duration_ms=(time.time() - start_time) * 1000,
                    error_message=f"Target module {test.target_module} not registered"
                )
            
            # 运行测试
            test.test_func()
            
            duration = (time.time() - start_time) * 1000
            result = IntegrationResult(
                test_name=test.name,
                source_module=test.source_module,
                target_module=test.target_module,
                level=test.level,
                passed=True,
                duration_ms=duration
            )
            
            self.results[test_id] = result
            return result
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            result = IntegrationResult(
                test_name=test.name,
                source_module=test.source_module,
                target_module=test.target_module,
                level=test.level,
                passed=False,
                duration_ms=duration,
                error_message=str(e)
            )
            
            self.results[test_id] = result
            return result
    
    def run_all_by_level(self, level: IntegrationLevel) -> Dict[str, IntegrationResult]:
        """按级别运行所有测试"""
        results = {}
        
        for test_id, test in self.integration_tests.items():
            if test.level == level:
                result = self.run_integration_test(test_id)
                if result:
                    results[test_id] = result
        
        return results
    
    def run_all(self) -> Dict[str, IntegrationResult]:
        """运行所有集成测试"""
        results = {}
        
        for test_id in self.integration_tests.keys():
            result = self.run_integration_test(test_id)
            if result:
                results[test_id] = result
        
        return results
    
    def get_module_dependencies(self, module_name: str) -> List[str]:
        """获取模块的依赖"""
        if module_name not in self.modules:
            return []
        return self.modules[module_name].dependencies
    
    def check_circular_dependency(self) -> Optional[List[str]]:
        """检查循环依赖"""
        visited = set()
        rec_stack = set()
        
        def dfs(module: str, path: List[str]) -> Optional[List[str]]:
            visited.add(module)
            rec_stack.add(module)
            path.append(module)
            
            if module in self.modules:
                for dep in self.modules[module].dependencies:
                    if dep not in visited:
                        cycle = dfs(dep, path.copy())
                        if cycle:
                            return cycle
                    elif dep in rec_stack:
                        cycle = path[path.index(dep):] + [dep]
                        return cycle
            
            rec_stack.remove(module)
            return None
        
        for module in self.modules:
            if module not in visited:
                cycle = dfs(module, [])
                if cycle:
                    return cycle
        
        return None
    
    def build_dependency_graph(self) -> DependencyGraph:
        """构建依赖图"""
        nodes = list(self.modules.keys())
        edges = {}
        
        for module_name, module in self.modules.items():
            edges[module_name] = module.dependencies.copy()
        
        return DependencyGraph(nodes=nodes, edges=edges)
    
    def get_test_coverage(self) -> Dict[str, float]:
        """获取测试覆盖率"""
        coverage = {}
        
        # 计算每个模块的测试覆盖
        for module_name in self.modules:
            total_tests = len(self.integration_tests)
            if total_tests == 0:
                coverage[module_name] = 0.0
                continue
            
            # 计算涉及该模块的测试数
            module_tests = sum(
                1 for test in self.integration_tests.values()
                if test.source_module == module_name or test.target_module == module_name
            )
            
            coverage[module_name] = (module_tests / total_tests) * 100
        
        return coverage
    
    def generate_report(self, results: Dict[str, IntegrationResult]) -> str:
        """生成报告"""
        report = []
        report.append("=" * 70)
        report.append("跨模块集成测试报告")
        report.append("=" * 70)
        
        # 按级别分组
        by_level = {}
        for test_id, result in results.items():
            level = result.level.value
            if level not in by_level:
                by_level[level] = []
            by_level[level].append(result)
        
        for level, level_results in by_level.items():
            report.append(f"\n{level.upper()}级别:")
            
            passed = sum(1 for r in level_results if r.passed)
            failed = sum(1 for r in level_results if not r.passed)
            
            report.append(f"  通过: {passed}, 失败: {failed}")
            
            for result in level_results:
                status = "✓" if result.passed else "✗"
                report.append(f"    {status} {result.test_name}")
                report.append(f"      {result.source_module} -> {result.target_module}")
                if result.error_message:
                    report.append(f"      错误: {result.error_message}")
        
        # 模块覆盖率
        report.append("\n模块测试覆盖率:")
        coverage = self.get_test_coverage()
        for module, cov in coverage.items():
            report.append(f"  {module}: {cov:.1f}%")
        
        # 循环依赖检查
        circular = self.check_circular_dependency()
        if circular:
            report.append(f"\n警告: 检测到循环依赖: {' -> '.join(circular)}")
        else:
            report.append("\n✓ 未检测到循环依赖")
        
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


# 全局跨模块测试器
_cross_module_tester = None


def get_cross_module_tester() -> CrossModuleTester:
    """获取跨模块测试器"""
    global _cross_module_tester
    if _cross_module_tester is None:
        _cross_module_tester = CrossModuleTester()
    return _cross_module_tester
