"""
测试覆盖率分析器
用于分析测试覆盖率和代码质量
"""
import os
import ast
import inspect
from typing import Dict, List, Set, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import json


class CoverageLevel(Enum):
    """覆盖率级别"""
    STATEMENT = "statement"
    BRANCH = "branch"
    FUNCTION = "function"
    CLASS = "class"
    MODULE = "module"


@dataclass
class CodeElement:
    """代码元素"""
    element_id: str
    name: str
    type: str  # module, class, function, statement
    line_start: int
    line_end: int
    covered: bool = False
    metadata: Dict = field(default_factory=dict)


@dataclass
class ModuleCoverage:
    """模块覆盖率"""
    module_name: str
    file_path: str
    total_statements: int = 0
    covered_statements: int = 0
    total_functions: int = 0
    covered_functions: int = 0
    total_classes: int = 0
    covered_classes: int = 0
    elements: List[CodeElement] = field(default_factory=list)


@dataclass
class CoverageReport:
    """覆盖率报告"""
    total_modules: int
    total_statements: int
    covered_statements: int
    total_functions: int
    covered_functions: int
    total_classes: int
    covered_classes: int
    module_reports: List[ModuleCoverage]
    uncovered_lines: Dict[str, List[int]] = field(default_factory=dict)


class CoverageAnalyzer:
    """测试覆盖率分析器"""
    
    def __init__(self):
        self.modules: Dict[str, ModuleCoverage] = {}
        self.covered_lines: Dict[str, Set[int]] = {}
        self._element_counter = 0
    
    def register_module(self, module_name: str, file_path: str) -> bool:
        """注册模块进行分析"""
        if not os.path.exists(file_path):
            return False
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source)
            module_coverage = ModuleCoverage(
                module_name=module_name,
                file_path=file_path
            )
            
            # 分析模块
            self._analyze_module(tree, module_coverage, source)
            
            self.modules[module_name] = module_coverage
            return True
            
        except Exception:
            return False
    
    def _analyze_module(self, tree: ast.AST, module_coverage: ModuleCoverage, source: str):
        """分析模块"""
        lines = source.split('\n')
        
        # 统计语句
        for node in ast.walk(tree):
            if isinstance(node, ast.stmt):
                module_coverage.total_statements += 1
        
        # 分析类
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                self._element_counter += 1
                element = CodeElement(
                    element_id=f"EL-{self._element_counter}",
                    name=node.name,
                    type="class",
                    line_start=node.lineno,
                    line_end=node.end_lineno or node.lineno
                )
                module_coverage.elements.append(element)
                module_coverage.total_classes += 1
        
        # 分析函数
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if hasattr(node, 'name') and not node.name.startswith('_'):
                    self._element_counter += 1
                    element = CodeElement(
                        element_id=f"EL-{self._element_counter}",
                        name=node.name,
                        type="function",
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno
                    )
                    module_coverage.elements.append(element)
                    module_coverage.total_functions += 1
    
    def mark_covered(self, module_name: str, line_number: int):
        """标记代码行已被覆盖"""
        if module_name not in self.covered_lines:
            self.covered_lines[module_name] = set()
        
        self.covered_lines[module_name].add(line_number)
    
    def mark_covered_range(self, module_name: str, start_line: int, end_line: int):
        """标记代码范围已被覆盖"""
        if module_name not in self.covered_lines:
            self.covered_lines[module_name] = set()
        
        for line in range(start_line, end_line + 1):
            self.covered_lines[module_name].add(line)
    
    def calculate_coverage(self) -> CoverageReport:
        """计算覆盖率"""
        total_statements = 0
        covered_statements = 0
        total_functions = 0
        covered_functions = 0
        total_classes = 0
        covered_classes = 0
        uncovered_lines = {}
        
        for module_name, module_coverage in self.modules.items():
            covered = self.covered_lines.get(module_name, set())
            
            # 计算元素覆盖
            for element in module_coverage.elements:
                element_covered = any(
                    line in covered
                    for line in range(element.line_start, element.line_end + 1)
                )
                element.covered = element_covered
                
                if element.type == "function":
                    total_functions += 1
                    if element_covered:
                        covered_functions += 1
                
                elif element.type == "class":
                    total_classes += 1
                    if element_covered:
                        covered_classes += 1
            
            # 统计未覆盖的行
            if covered:
                uncovered = []
                for i, line in enumerate(open(module_coverage.file_path), 1):
                    if i not in covered and line.strip() and not line.strip().startswith('#'):
                        uncovered.append(i)
                if uncovered:
                    uncovered_lines[module_name] = uncovered
            
            # 简单估计语句覆盖
            module_coverage.covered_statements = len(covered)
            module_coverage.covered_functions = covered_functions
            module_coverage.covered_classes = covered_classes
            
            total_statements += module_coverage.total_statements
            covered_statements += module_coverage.covered_statements
            total_functions += module_coverage.total_functions
            covered_functions += module_coverage.covered_functions
            total_classes += module_coverage.total_classes
            covered_classes += module_coverage.covered_classes
        
        return CoverageReport(
            total_modules=len(self.modules),
            total_statements=total_statements,
            covered_statements=covered_statements,
            total_functions=total_functions,
            covered_functions=covered_functions,
            total_classes=total_classes,
            covered_classes=covered_classes,
            module_reports=list(self.modules.values()),
            uncovered_lines=uncovered_lines
        )
    
    def generate_report(self, coverage_report: CoverageReport = None) -> str:
        """生成覆盖率报告"""
        if coverage_report is None:
            coverage_report = self.calculate_coverage()
        
        report = []
        report.append("=" * 70)
        report.append("测试覆盖率报告")
        report.append("=" * 70)
        
        # 总体统计
        report.append("\n总体覆盖率:")
        
        stmt_rate = (coverage_report.covered_statements / coverage_report.total_statements * 100) \
            if coverage_report.total_statements > 0 else 0
        func_rate = (coverage_report.covered_functions / coverage_report.total_functions * 100) \
            if coverage_report.total_functions > 0 else 0
        class_rate = (coverage_report.covered_classes / coverage_report.total_classes * 100) \
            if coverage_report.total_classes > 0 else 0
        
        report.append(f"  模块: {coverage_report.total_modules}")
        report.append(f"  语句: {coverage_report.covered_statements}/{coverage_report.total_statements} ({stmt_rate:.1f}%)")
        report.append(f"  函数: {coverage_report.covered_functions}/{coverage_report.total_functions} ({func_rate:.1f}%)")
        report.append(f"  类: {coverage_report.covered_classes}/{coverage_report.total_classes} ({class_rate:.1f}%)")
        
        # 按模块详细报告
        report.append("\n模块详细报告:")
        for module_coverage in coverage_report.module_reports:
            report.append(f"\n  {module_coverage.module_name}:")
            report.append(f"    文件: {module_coverage.file_path}")
            
            if module_coverage.total_functions > 0:
                func_cov = module_coverage.covered_functions / module_coverage.total_functions * 100
                report.append(f"    函数: {module_coverage.covered_functions}/{module_coverage.total_functions} ({func_cov:.1f}%)")
            
            if module_coverage.total_classes > 0:
                class_cov = module_coverage.covered_classes / module_coverage.total_classes * 100
                report.append(f"    类: {module_coverage.covered_classes}/{module_coverage.total_classes} ({class_cov:.1f}%)")
            
            # 显示覆盖的元素
            covered_elements = [e for e in module_coverage.elements if e.covered]
            uncovered_elements = [e for e in module_coverage.elements if not e.covered]
            
            if covered_elements:
                report.append(f"    已覆盖: {', '.join(e.name for e in covered_elements[:5])}")
            if uncovered_elements:
                report.append(f"    未覆盖: {', '.join(e.name for e in uncovered_elements[:5])}")
        
        # 未覆盖的代码行
        if coverage_report.uncovered_lines:
            report.append("\n未覆盖的代码行:")
            for module, lines in coverage_report.uncovered_lines.items():
                report.append(f"\n  {module}:")
                # 只显示前10行
                for line in lines[:10]:
                    report.append(f"    第 {line} 行")
                if len(lines) > 10:
                    report.append(f"    ... 还有 {len(lines) - 10} 行")
        
        report.append("\n" + "=" * 70)
        return "\n".join(report)
    
    def export_report(self, coverage_report: CoverageReport, filepath: str):
        """导出覆盖率报告"""
        data = {
            'total_modules': coverage_report.total_modules,
            'total_statements': coverage_report.total_statements,
            'covered_statements': coverage_report.covered_statements,
            'total_functions': coverage_report.total_functions,
            'covered_functions': coverage_report.covered_functions,
            'total_classes': coverage_report.total_classes,
            'covered_classes': coverage_report.covered_classes,
            'module_reports': [
                {
                    'module_name': m.module_name,
                    'file_path': m.file_path,
                    'total_statements': m.total_statements,
                    'covered_statements': m.covered_statements,
                    'total_functions': m.total_functions,
                    'covered_functions': m.covered_functions,
                    'total_classes': m.total_classes,
                    'covered_classes': m.covered_classes
                }
                for m in coverage_report.module_reports
            ],
            'uncovered_lines': coverage_report.uncovered_lines
        }
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get_coverage_summary(self, coverage_report: CoverageReport) -> Dict[str, Any]:
        """获取覆盖率摘要"""
        return {
            'total_modules': coverage_report.total_modules,
            'statement_coverage': (coverage_report.covered_statements / coverage_report.total_statements * 100)
                if coverage_report.total_statements > 0 else 0,
            'function_coverage': (coverage_report.covered_functions / coverage_report.total_functions * 100)
                if coverage_report.total_functions > 0 else 0,
            'class_coverage': (coverage_report.covered_classes / coverage_report.total_classes * 100)
                if coverage_report.total_classes > 0 else 0,
            'overall_score': (
                (coverage_report.covered_statements / coverage_report.total_statements * 100) +
                (coverage_report.covered_functions / coverage_report.total_functions * 100) +
                (coverage_report.covered_classes / coverage_report.total_classes * 100)
            ) / 3 if coverage_report.total_statements > 0 or coverage_report.total_functions > 0 or coverage_report.total_classes > 0 else 0
        }


# 全局覆盖率分析器
_coverage_analyzer = None


def get_coverage_analyzer() -> CoverageAnalyzer:
    """获取覆盖率分析器"""
    global _coverage_analyzer
    if _coverage_analyzer is None:
        _coverage_analyzer = CoverageAnalyzer()
    return _coverage_analyzer
