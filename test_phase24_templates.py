"""
第24阶段测试：记忆模板功能
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.memory import get_memory_system
from src.templates import (
    MemoryTemplateManager,
    MemoryTemplate,
    TemplateEngine,
    EnhancedMemoryWithTemplates
)


def test_template_engine():
    """测试模板引擎"""
    print("\n" + "=" * 60)
    print("测试 1: 模板引擎")
    print("=" * 60)

    # 测试变量提取
    template = "项目名称：{project_name}，负责人：{manager}，截止日期：{deadline}"
    variables = TemplateEngine.extract_variables(template)
    print(f"\n模板: {template}")
    print(f"提取的变量: {variables}")
    assert set(variables) == {"project_name", "manager", "deadline"}

    # 测试模板渲染
    rendered = TemplateEngine.render(template, {
        "project_name": "新系统开发",
        "manager": "张三",
        "deadline": "2026-06-01"
    })
    print(f"\n渲染结果: {rendered}")
    assert "新系统开发" in rendered
    assert "张三" in rendered
    assert "2026-06-01" in rendered

    # 测试验证
    validation = TemplateEngine.validate(template, {"project_name": "test"})
    print(f"\n验证结果（缺少变量）: {validation}")
    assert validation["valid"] == False
    assert "manager" in validation["missing"]

    validation_ok = TemplateEngine.validate(template, {
        "project_name": "test",
        "manager": "test",
        "deadline": "test"
    })
    assert validation_ok["valid"] == True

    print("✓ 模板引擎测试通过！")
    return True


def test_basic_template():
    """测试基本模板管理"""
    print("\n" + "=" * 60)
    print("测试 2: 基本模板管理")
    print("=" * 60)

    # 清理测试数据
    test_path = "./data/test_templates_temp.json"
    if os.path.exists(test_path):
        os.remove(test_path)

    manager = MemoryTemplateManager(test_path)

    # 创建模板
    template_id = manager.create_template(
        name="会议记录",
        content_template="会议主题：{title}，日期：{date}",
        description="标准会议记录",
        category="工作",
        tags=["会议", "记录"]
    )
    print(f"\n创建模板: {template_id}")

    # 获取模板
    template = manager.get_template(template_id)
    assert template is not None
    assert template.name == "会议记录"

    # 更新模板
    success = manager.update_template(
        template_id,
        name="会议记录（详细版）",
        description="详细版会议记录"
    )
    assert success

    template = manager.get_template(template_id)
    assert template.name == "会议记录（详细版）"

    # 删除模板
    success = manager.delete_template(template_id)
    assert success
    assert manager.get_template(template_id) is None

    print("✓ 基本模板管理测试通过！")

    # 清理
    try:
        os.remove(test_path)
    except:
        pass

    return True


def test_template_categories():
    """测试模板分类"""
    print("\n" + "=" * 60)
    print("测试 3: 模板分类")
    print("=" * 60)

    test_path = "./data/test_templates_cat.json"
    if os.path.exists(test_path):
        os.remove(test_path)

    manager = MemoryTemplateManager(test_path)

    # 创建多个分类的模板
    manager.create_template(
        name="会议记录",
        content_template="会议：{title}",
        category="工作",
        tags=["会议"]
    )
    manager.create_template(
        name="项目计划",
        content_template="项目：{name}",
        category="工作",
        tags=["项目"]
    )
    manager.create_template(
        name="学习笔记",
        content_template="学习：{topic}",
        category="学习",
        tags=["学习"]
    )

    # 按类别获取
    work_templates = manager.get_templates_by_category("工作")
    print(f"\n工作类模板数: {len(work_templates)}")
    assert len(work_templates) == 2

    # 按标签获取
    meeting_templates = manager.get_templates_by_tag("会议")
    assert len(meeting_templates) == 1

    # 搜索
    results = manager.search_templates("会议")
    print(f"搜索'会议'结果: {len(results)}")
    assert len(results) >= 1

    print("✓ 模板分类测试通过！")

    # 清理
    try:
        os.remove(test_path)
    except:
        pass

    return True


def test_template_usage():
    """测试模板使用统计"""
    print("\n" + "=" * 60)
    print("测试 4: 模板使用统计")
    print("=" * 60)

    test_path = "./data/test_templates_usage.json"
    if os.path.exists(test_path):
        os.remove(test_path)

    manager = MemoryTemplateManager(test_path)

    # 创建模板
    template_id = manager.create_template(
        name="测试模板",
        content_template="测试内容：{var1} {var2}"
    )

    # 使用模板
    manager.render_template(template_id, {"var1": "a", "var2": "b"})
    manager.render_template(template_id, {"var1": "c", "var2": "d"})

    template = manager.get_template(template_id)
    print(f"\n模板使用次数: {template.usage_count}")
    assert template.usage_count == 2

    # 获取统计
    stats = manager.get_statistics()
    print(f"\n统计信息:")
    print(f"  总模板数: {stats['total_templates']}")
    print(f"  总使用次数: {stats['total_usage']}")
    print(f"  类别分布: {stats['categories']}")

    assert stats['total_templates'] == 1
    assert stats['total_usage'] == 2

    print("✓ 模板使用统计测试通过！")

    # 清理
    try:
        os.remove(test_path)
    except:
        pass

    return True


def test_enhanced_memory():
    """测试增强记忆系统"""
    print("\n" + "=" * 60)
    print("测试 5: 增强记忆系统")
    print("=" * 60)

    memory = get_memory_system()
    enhanced = EnhancedMemoryWithTemplates(memory)

    # 清空现有数据
    memory.l1.clear()
    memory.l2.clear()
    memory.l3.clear()

    # 获取所有模板
    templates = enhanced.get_all_templates()
    print(f"\n默认模板数: {len(templates)}")
    for t in templates[:3]:
        print(f"  - {t.name} ({t.category})")

    # 创建自定义模板
    custom_id = enhanced.create_template(
        name="自定义模板",
        content_template="自定义内容：{content1} {content2}",
        category="自定义",
        tags=["测试"]
    )
    print(f"\n创建自定义模板: {custom_id}")

    # 搜索模板
    results = enhanced.search_templates("会议")
    print(f"\n搜索'会议'结果: {len(results)}")

    # 使用模板创建记忆
    meeting_template = None
    for t in templates:
        if t.name == "会议记录":
            meeting_template = t
            break

    if meeting_template:
        memory_id = enhanced.use_template(
            meeting_template.template_id,
            {
                "title": "项目启动会议",
                "date": "2026-06-01",
                "participants": "张三、李四、王五",
                "point1": "确定项目目标",
                "point2": "分配任务",
                "point3": "制定计划",
                "action_items": "完成项目计划文档"
            },
            "proj_001",
            "l2"
        )
        print(f"\n使用模板创建记忆: {memory_id}")
        assert memory_id is not None

    # 获取统计
    stats = enhanced.get_template_statistics()
    print(f"\n模板统计:")
    print(f"  总模板数: {stats['total_templates']}")
    print(f"  总使用次数: {stats['total_usage']}")

    print("✓ 增强记忆系统测试通过！")
    return True


def test_error_handling():
    """测试错误处理"""
    print("\n" + "=" * 60)
    print("测试 6: 错误处理")
    print("=" * 60)

    test_path = "./data/test_templates_error.json"
    if os.path.exists(test_path):
        os.remove(test_path)

    manager = MemoryTemplateManager(test_path)

    # 创建模板
    template_id = manager.create_template(
        name="错误测试",
        content_template="变量：{var1} {var2}"
    )

    # 尝试使用缺少变量的模板
    try:
        manager.render_template(template_id, {"var1": "only_one"})
        print("\n错误：应该抛出异常！")
        assert False
    except ValueError as e:
        print(f"\n正确捕获异常: {e}")
        assert "Missing variables" in str(e)

    # 尝试获取不存在的模板
    template = manager.get_template("non_existent_id")
    assert template is None

    # 尝试更新不存在的模板
    success = manager.update_template("non_existent_id", name="test")
    assert success == False

    # 尝试删除不存在的模板
    success = manager.delete_template("non_existent_id")
    assert success == False

    print("✓ 错误处理测试通过！")

    # 清理
    try:
        os.remove(test_path)
    except:
        pass

    return True


def test_default_templates():
    """测试默认模板"""
    print("\n" + "=" * 60)
    print("测试 7: 默认模板")
    print("=" * 60)

    memory = get_memory_system()
    enhanced = EnhancedMemoryWithTemplates(memory)

    templates = enhanced.get_all_templates()
    print(f"\n默认模板数: {len(templates)}")

    # 验证默认模板
    assert len(templates) >= 4

    default_names = ["会议记录", "项目启动", "学习笔记", "代码审查"]
    template_names = [t.name for t in templates]

    for name in default_names:
        assert name in template_names, f"默认模板{name}应该存在"

    print("\n默认模板:")
    for t in templates:
        print(f"  - {t.name} ({t.category}): {len(t.variables)}个变量")

    print("✓ 默认模板测试通过！")
    return True


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("第24阶段测试：记忆模板功能")
    print("=" * 60)

    all_passed = True

    try:
        passed = test_template_engine()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试1失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_basic_template()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试2失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_template_categories()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试3失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_template_usage()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试4失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_enhanced_memory()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试5失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_error_handling()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试6失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        passed = test_default_templates()
        if not passed:
            all_passed = False
    except Exception as e:
        print(f"\n✗ 测试7失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("✓ 所有测试通过！")
    else:
        print("✗ 部分测试失败")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
