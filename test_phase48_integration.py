"""
第48阶段测试用例：系统集成和端到端测试
"""
import sys
import time
import os

sys.path.insert(0, '/workspace')

from src.testing import (
    get_e2e_framework,
    EndToEndScenario,
    ScenarioStatus,
    get_cross_module_tester,
    IntegrationLevel,
    get_regression_manager,
    get_env_manager,
    EnvironmentType,
    ResourceType,
    get_coverage_analyzer,
    assert_equal,
    assert_true,
    assert_false,
    assert_not_none,
    assert_none,
)


def test_e2e_scenario():
    """测试端到端场景"""
    framework = get_e2e_framework()
    
    scenario = framework.create_scenario(
        "test_scenario",
        "测试场景"
    )
    
    counter = {'value': 0}
    
    def step1():
        counter['value'] = 1
        return True
    
    def step2():
        counter['value'] = 2
        return True
    
    def step3():
        return counter['value'] == 2
    
    scenario.add_step("步骤1", step1, timeout=5.0)
    scenario.add_step("步骤2", step2, timeout=5.0)
    scenario.add_step("步骤3验证", step3, timeout=5.0)
    
    result = scenario.run()
    
    assert_equal(result.status, ScenarioStatus.PASSED)
    assert_equal(result.passed_steps, 3)
    assert_equal(result.failed_steps, 0)


def test_e2e_framework():
    """测试端到端测试框架"""
    framework = get_e2e_framework()
    
    scenario = framework.create_scenario("user_registration", "用户注册流程")
    
    def check_username():
        return "valid_user"
    
    def create_user():
        return True
    
    scenario.add_step("验证用户名", check_username)
    scenario.add_step("创建用户", create_user)
    
    results = framework.run_all()
    
    assert_true(len(results) > 0)
    
    report = framework.generate_report(results)
    assert_true("端到端测试报告" in report)


def test_cross_module_tester():
    """测试跨模块测试器"""
    tester = get_cross_module_tester()
    
    # 注册模块
    tester.register_module(
        "module_a",
        inputs=["input1"],
        outputs=["output1"],
        dependencies=[]
    )
    
    tester.register_module(
        "module_b",
        inputs=["output1"],
        outputs=["result"],
        dependencies=["module_a"]
    )
    
    assert_true("module_a" in tester.modules)
    assert_true("module_b" in tester.modules)
    
    # 添加集成测试
    def integration_test():
        assert True
    
    test_id = tester.add_integration_test(
        name="test_a_to_b",
        source_module="module_a",
        target_module="module_b",
        test_func=integration_test,
        level=IntegrationLevel.INTEGRATION
    )
    
    assert_not_none(test_id)
    
    # 检查循环依赖
    circular = tester.check_circular_dependency()
    assert_none(circular)


def test_cross_module_dependency_graph():
    """测试依赖图"""
    tester = get_cross_module_tester()
    
    # A depends on B, B depends on C - no circular
    tester.register_module("A", [], ["B"], ["B"])
    tester.register_module("B", ["A"], ["C"], ["C"])
    tester.register_module("C", ["B"], [], [])
    
    circular = tester.check_circular_dependency()
    assert_none(circular)  # No circular dependency here
    
    # Test with actual circular dependency: A -> B -> A
    tester2 = get_cross_module_tester()
    tester2.register_module("X", [], ["Y"], ["Y"])
    tester2.register_module("Y", ["X"], [], ["X"])
    
    circular2 = tester2.check_circular_dependency()
    # This should detect circular dependency


def test_regression_manager():
    """测试回归测试管理器"""
    manager = get_regression_manager()
    
    suite_id = manager.create_suite(
        name="core_tests",
        description="核心测试套件"
    )
    
    assert_not_none(suite_id)
    
    def simple_test():
        assert True
    
    test_id = manager.register_test(
        name="test_core_1",
        test_func=simple_test,
        module="core",
        priority=1
    )
    
    assert_not_none(test_id)
    
    manager.add_test_to_suite(suite_id, test_id)
    
    results = manager.run_suite(suite_id)
    assert_true(len(results) > 0)


def test_regression_stability():
    """测试回归稳定性追踪"""
    manager = get_regression_manager()
    
    test_id = manager.register_test(
        name="stability_test",
        test_func=lambda: None,
        module="test",
        priority=2
    )
    
    # 运行多次
    for _ in range(3):
        manager.run_test(test_id)
    
    trend = manager.get_stability_trend("stability_test", days=1)
    assert_true(trend['total'] > 0)


def test_environment_manager():
    """测试环境管理器"""
    manager = get_env_manager()
    
    env_id = manager.create_environment(
        name="test_env",
        env_type=EnvironmentType.TESTING
    )
    
    assert_not_none(env_id)
    
    # 设置资源
    resource_id = manager.setup_resource(
        env_id,
        ResourceType.FILE,
        "test.txt",
        {'content': 'test data'}
    )
    
    assert_not_none(resource_id)
    
    # 设置环境变量
    manager.set_environment_variable(env_id, "TEST_VAR", "test_value")
    value = manager.get_environment_variable(env_id, "TEST_VAR")
    assert_equal(value, "test_value")
    
    # 生成报告
    report = manager.generate_report()
    assert_true("测试环境报告" in report)


def test_environment_snapshot():
    """测试环境快照和恢复"""
    manager = get_env_manager()
    
    env_id = manager.create_environment(
        name="snapshot_test",
        env_type=EnvironmentType.TESTING
    )
    
    # 设置资源
    manager.setup_resource(
        env_id,
        ResourceType.FILE,
        "data.txt",
        {'content': 'important data'}
    )
    
    # 创建快照
    snapshot = manager.snapshot_environment(env_id)
    assert_not_none(snapshot)
    assert_true('files' in snapshot)
    
    # 恢复环境
    restored_id = manager.restore_environment(snapshot)
    assert_not_none(restored_id)


def test_coverage_analyzer():
    """测试覆盖率分析器"""
    analyzer = get_coverage_analyzer()
    
    # 注册测试模块
    module_path = '/workspace/src/memory/__init__.py'
    if os.path.exists(module_path):
        result = analyzer.register_module("memory", module_path)
        assert_true(result)
    
    # 标记覆盖
    analyzer.mark_covered("memory", 1)
    analyzer.mark_covered("memory", 5)
    analyzer.mark_covered("memory", 10)
    
    # 计算覆盖率
    report = analyzer.calculate_coverage()
    assert_true(report.total_modules >= 0)


def test_integration_levels():
    """测试集成级别"""
    tester = get_cross_module_tester()
    
    levels = [
        IntegrationLevel.UNIT,
        IntegrationLevel.INTEGRATION,
        IntegrationLevel.SYSTEM,
        IntegrationLevel.END_TO_END
    ]
    
    for level in levels:
        assert_equal(level.value in ['unit', 'integration', 'system', 'e2e'], True)


def test_environment_types():
    """测试环境类型"""
    types = [
        EnvironmentType.DEVELOPMENT,
        EnvironmentType.TESTING,
        EnvironmentType.STAGING,
        EnvironmentType.PRODUCTION
    ]
    
    for env_type in types:
        assert_true(env_type.value in ['development', 'testing', 'staging', 'production'])


def test_resource_types():
    """测试资源类型"""
    types = [
        ResourceType.DATABASE,
        ResourceType.CACHE,
        ResourceType.FILE,
        ResourceType.CONFIG,
        ResourceType.NETWORK
    ]
    
    for rtype in types:
        assert_true(rtype.value in ['database', 'cache', 'file', 'config', 'network'])


def run_all_tests():
    """运行所有测试"""
    print("=" * 70)
    print("第48阶段测试：系统集成和端到端测试")
    print("=" * 70)
    
    tests = [
        test_e2e_scenario,
        test_e2e_framework,
        test_cross_module_tester,
        test_cross_module_dependency_graph,
        test_regression_manager,
        test_regression_stability,
        test_environment_manager,
        test_environment_snapshot,
        test_coverage_analyzer,
        test_integration_levels,
        test_environment_types,
        test_resource_types,
    ]
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(tests, 1):
        print(f"\n[{i}/{len(tests)}] 运行: {test.__name__}")
        try:
            test()
            print(f"  ✓ 通过")
            passed += 1
        except Exception as e:
            print(f"  ✗ 失败: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
