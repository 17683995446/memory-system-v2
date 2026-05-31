"""
测试框架模块
"""
from .test_framework import (
    TestingFramework,
    TestSuite,
    TestStatus,
    TestCategory,
    TestResult,
    PerformanceMetric,
    PerformanceTester,
    IntegrationTester,
    get_testing_framework,
    assert_equal,
    assert_true,
    assert_false,
    assert_not_none,
    assert_none,
    assert_in,
    assert_not_in,
    assert_raises,
    assert_greater,
    assert_less,
    assert_almost_equal,
)

from .bug_tracker import (
    BugTracker,
    Bug,
    BugSeverity,
    BugStatus,
    get_bug_tracker,
)

from .test_automation import (
    TestAutomation,
    TestSchedule,
    TestScheduleType,
    CIJob,
    get_test_automation,
)

from .e2e_testing import (
    EndToEndTestFramework,
    EndToEndScenario,
    ScenarioStatus,
    TestStep,
    ScenarioResult,
    get_e2e_framework,
)

from .cross_module_testing import (
    CrossModuleTester,
    ModuleInterface,
    IntegrationTest,
    IntegrationLevel,
    get_cross_module_tester,
)

from .regression_testing import (
    RegressionTestManager,
    RegressionSuite,
    RegressionTest,
    RegressionResult,
    RegressionStatus,
    get_regression_manager,
)

from .test_environment import (
    TestEnvironmentManager,
    EnvironmentConfig,
    EnvironmentType,
    ResourceType,
    TestResource,
    get_env_manager,
)

from .coverage_analyzer import (
    CoverageAnalyzer,
    ModuleCoverage,
    CodeElement,
    CoverageLevel,
    CoverageReport,
    get_coverage_analyzer,
)

__all__ = [
    'TestingFramework',
    'TestSuite',
    'TestStatus',
    'TestCategory',
    'TestResult',
    'PerformanceMetric',
    'PerformanceTester',
    'IntegrationTester',
    'get_testing_framework',
    'assert_equal',
    'assert_true',
    'assert_false',
    'assert_not_none',
    'assert_none',
    'assert_in',
    'assert_not_in',
    'assert_raises',
    'assert_greater',
    'assert_less',
    'assert_almost_equal',
    'BugTracker',
    'Bug',
    'BugSeverity',
    'BugStatus',
    'get_bug_tracker',
    'TestAutomation',
    'TestSchedule',
    'TestScheduleType',
    'CIJob',
    'get_test_automation',
    'EndToEndTestFramework',
    'EndToEndScenario',
    'ScenarioStatus',
    'TestStep',
    'ScenarioResult',
    'get_e2e_framework',
    'CrossModuleTester',
    'ModuleInterface',
    'IntegrationTest',
    'IntegrationLevel',
    'get_cross_module_tester',
    'RegressionTestManager',
    'RegressionSuite',
    'RegressionTest',
    'RegressionResult',
    'RegressionStatus',
    'get_regression_manager',
    'TestEnvironmentManager',
    'EnvironmentConfig',
    'EnvironmentType',
    'ResourceType',
    'TestResource',
    'get_env_manager',
    'CoverageAnalyzer',
    'ModuleCoverage',
    'CodeElement',
    'CoverageLevel',
    'CoverageReport',
    'get_coverage_analyzer',
]
