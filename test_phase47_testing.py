"""
第47阶段测试用例：测试和质量保证
"""
import time
import sys
from datetime import datetime, timedelta

sys.path.insert(0, '/workspace')

from src.testing import (
    TestingFramework,
    TestSuite,
    TestStatus,
    TestCategory,
    TestResult,
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
    BugTracker,
    BugSeverity,
    BugStatus,
    get_bug_tracker,
    TestAutomation,
    TestScheduleType,
    get_test_automation,
)


def test_basic_assertions():
    """测试基本断言功能"""
    assert_equal(1 + 1, 2)
    assert_true(1 < 2)
    assert_false(1 > 2)
    assert_not_none("test")
    assert_none(None)
    assert_in(1, [1, 2, 3])
    assert_not_in(4, [1, 2, 3])
    
    def raise_exception():
        raise ValueError("Test error")
    
    assert_raises(ValueError, raise_exception)
    
    assert_greater(5, 3)
    assert_less(3, 5)
    assert_almost_equal(0.1 + 0.2, 0.3, places=1)


def test_test_suite():
    """测试测试套件功能"""
    suite = TestSuite("test_suite_1", TestCategory.UNIT)
    
    # 添加测试
    def test_pass():
        assert_equal(1 + 1, 2)
    
    def test_fail():
        assert_equal(1 + 1, 3)
    
    suite.add_test(test_pass, tags=["basic", "math"])
    suite.add_test(test_fail, tags=["basic"])
    
    # 运行测试
    results = suite.run()
    
    assert_equal(results['suite_name'], "test_suite_1")
    assert_equal(results['total_tests'], 2)
    assert_equal(results['passed'], 1)
    assert_equal(results['failed'], 1)


def test_test_framework():
    """测试综合测试框架"""
    framework = TestingFramework()
    
    # 创建多个测试套件
    suite1 = framework.create_suite("unit_tests", TestCategory.UNIT)
    suite2 = framework.create_suite("integration_tests", TestCategory.INTEGRATION)
    
    # 添加测试
    def test_math():
        assert_equal(2 * 3, 6)
    
    def test_string():
        assert_equal("hello".upper(), "HELLO")
    
    suite1.add_test(test_math, tags=["math"])
    suite1.add_test(test_string, tags=["string"])
    
    # 运行所有测试
    all_results = framework.run_all()
    
    assert_in("unit_tests", all_results)
    assert_in("integration_tests", all_results)
    
    # 生成报告
    report = framework.generate_full_report(all_results)
    assert_true(len(report) > 0)


def test_setup_teardown():
    """测试setup和teardown功能"""
    suite = TestSuite("setup_teardown_test")
    
    setup_called = False
    teardown_called = False
    test_called = False
    
    def setup():
        nonlocal setup_called
        setup_called = True
    
    def teardown():
        nonlocal teardown_called
        teardown_called = True
    
    def test():
        nonlocal test_called
        test_called = True
        assert_true(True)
    
    suite.setup(setup)
    suite.teardown(teardown)
    suite.add_test(test)
    
    suite.run()
    
    assert_true(setup_called)
    assert_true(teardown_called)
    assert_true(test_called)


def test_performance_tester():
    """测试性能测试器"""
    tester = PerformanceTester()
    
    # 定义一个简单的测试函数
    def quick_function():
        sum(range(1000))
    
    # 测量性能
    metric = tester.measure(
        "quick_function_test",
        quick_function,
        iterations=50,
        warmup=5
    )
    
    assert_equal(metric.name, "quick_function_test")
    assert_equal(metric.total_count, 50)
    assert_greater(metric.max_ms, metric.min_ms)
    assert_greater(metric.avg_ms, 0)
    
    # 生成报告
    report = tester.generate_report()
    assert_true("quick_function_test" in report)


def test_integration_tester():
    """测试集成测试器"""
    tester = IntegrationTester()
    
    # 注册组件
    class ComponentA:
        pass
    
    class ComponentB:
        pass
    
    tester.register_component("component_a", ComponentA())
    tester.register_component("component_b", ComponentB(), depends_on=["component_a"])
    
    # 测试集成
    result_b = tester.test_component_integration("component_b")
    result_a = tester.test_component_integration("component_a")
    
    assert_true(result_a)
    assert_true(result_b)


def test_bug_tracker():
    """测试BUG追踪器"""
    tracker = BugTracker()
    
    # 创建BUG
    bug_id = tracker.create_bug(
        title="Test Bug",
        description="This is a test bug",
        severity=BugSeverity.HIGH,
        module="test_module"
    )
    
    # 获取BUG
    bug = tracker.get_bug(bug_id)
    assert_not_none(bug)
    assert_equal(bug.title, "Test Bug")
    assert_equal(bug.severity, BugSeverity.HIGH)
    
    # 更新BUG
    success = tracker.update_bug(bug_id, status=BugStatus.IN_PROGRESS)
    assert_true(success)
    
    bug = tracker.get_bug(bug_id)
    assert_equal(bug.status, BugStatus.IN_PROGRESS)
    
    # 获取统计
    stats = tracker.get_statistics()
    assert_equal(stats['total'], 1)
    
    # 生成报告
    report = tracker.generate_report()
    assert_true("Test Bug" in report)


def test_test_automation():
    """测试测试自动化功能"""
    framework = get_testing_framework()
    automation = get_test_automation(framework)
    
    # 创建测试套件用于自动化测试
    suite = framework.create_suite("automation_test_suite")
    
    def sample_test():
        assert_equal(1 + 1, 2)
    
    suite.add_test(sample_test)
    
    # 创建CI任务
    job_id = automation.create_ci_job(
        "Test CI Job",
        target_suites=["automation_test_suite"]
    )
    
    assert_not_none(job_id)
    
    # 运行CI任务
    success = automation.run_ci_job(job_id)
    assert_true(success)
    
    # 等待任务完成
    time.sleep(1)
    
    # 获取任务
    job = automation.get_job(job_id)
    assert_not_none(job)
    
    # 列出任务
    jobs = automation.list_jobs()
    assert_equal(len(jobs), 1)


def test_test_scheduling():
    """测试测试调度功能"""
    framework = get_testing_framework()
    automation = get_test_automation(framework)
    
    # 创建调度
    schedule_id = automation.create_schedule(
        "Daily Test",
        TestScheduleType.DAILY,
        target_suites=["automation_test_suite"],
        enabled=True
    )
    
    assert_not_none(schedule_id)
    
    # 获取调度
    schedule = automation.get_schedule(schedule_id)
    assert_not_none(schedule)
    assert_equal(schedule.name, "Daily Test")
    
    # 列出调度
    schedules = automation.list_schedules()
    assert_equal(len(schedules), 1)
    
    # 更新调度
    success = automation.update_schedule(schedule_id, enabled=False)
    assert_true(success)
    
    # 删除调度
    success = automation.delete_schedule(schedule_id)
    assert_true(success)


def test_report_generation():
    """测试报告生成功能"""
    framework = TestingFramework()
    suite = framework.create_suite("report_test_suite")
    
    def test_pass():
        assert_true(True)
    
    suite.add_test(test_pass)
    
    # 运行测试
    results = framework.run_all()
    
    # 生成报告
    report = framework.generate_full_report(results)
    assert_true("report_test_suite" in report)
    assert_true("通过" in report)


def test_fail_fast():
    """测试fail_fast功能"""
    suite = TestSuite("fail_fast_test")
    
    def test_1():
        assert_true(True)
    
    def test_2():
        assert_true(False)  # 这个会失败
    
    def test_3():
        assert_true(True)  # 这个不应该被执行
    
    suite.add_test(test_1)
    suite.add_test(test_2)
    suite.add_test(test_3)
    
    results = suite.run(fail_fast=True)
    
    # 虽然有3个测试，但fail_fast应该在失败后停止
    assert_equal(results['total_tests'], 3)


def run_all_tests():
    """运行所有测试"""
    print("=" * 70)
    print("第47阶段测试：测试和质量保证")
    print("=" * 70)
    
    tests = [
        test_basic_assertions,
        test_test_suite,
        test_test_framework,
        test_setup_teardown,
        test_performance_tester,
        test_integration_tester,
        test_bug_tracker,
        test_test_automation,
        test_test_scheduling,
        test_report_generation,
        test_fail_fast,
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
