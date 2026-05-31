"""
第39阶段测试：记忆系统插件与扩展架构
遵循"图难于其易，为大于其细"原则
"""

import os
import sys
import shutil
import tempfile

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.plugins import (
    PluginManager,
    PluginType,
    PluginStatus,
    BasePlugin,
    PreprocessorPlugin,
    MemoryHookPlugin,
    PluginInfo,
    EnhancedMemoryWithPlugins,
    get_plugin_manager
)


# 创建模拟记忆系统
class MockMemorySystem:
    """模拟记忆系统"""
    
    def __init__(self):
        self.memories = {}
    
    def add(self, text: str, task_id: str = "default", level: str = None) -> str:
        """添加记忆"""
        import uuid
        memory_id = str(uuid.uuid4())
        self.memories[memory_id] = {"text": text, "task_id": task_id, "level": level}
        return memory_id
    
    def recall(self, query: str, task_id: str = "default", limit: int = None) -> list:
        """检索记忆"""
        results = []
        for memory_id, memory in self.memories.items():
            if query.lower() in memory["text"].lower():
                results.append({"id": memory_id, **memory})
        return results if limit is None else results[:limit]


def test_plugin_discovery():
    """测试插件发现"""
    print("\n=== 测试插件发现")
    
    # 创建临时插件目录
    temp_dir = tempfile.mkdtemp()
    plugins_dir = os.path.join(temp_dir, "plugins")
    os.makedirs(plugins_dir)
    
    # 创建一个测试插件
    test_plugin_code = '''
from src.plugins import BasePlugin, PluginInfo, PluginType

class TestPlugin(BasePlugin):
    def get_info(self) -> PluginInfo:
        return PluginInfo(
            plugin_id="test_plugin",
            name="Test Plugin",
            version="0.1.0",
            description="A test plugin",
            plugin_type=PluginType.CUSTOM
        )
    
    def execute(self, context: dict) -> any:
        return {"status": "success", "data": context}
'''
    
    with open(os.path.join(plugins_dir, "test_plugin.py"), "w") as f:
        f.write(test_plugin_code)
    
    # 创建init文件
    with open(os.path.join(plugins_dir, "__init__.py"), "w") as f:
        f.write('"""Test plugins"""')
    
    # 测试发现
    manager = PluginManager(plugins_dir=plugins_dir)
    discovered = manager.discover_plugins()
    
    assert "test_plugin" in discovered, "Should discover test_plugin"
    print(f"✓ 发现插件: {discovered}")
    
    # 清理
    shutil.rmtree(temp_dir)
    print("✓ 插件发现测试通过")


def test_plugin_loading():
    """测试插件加载"""
    print("\n=== 测试插件加载")
    
    temp_dir = tempfile.mkdtemp()
    plugins_dir = os.path.join(temp_dir, "plugins")
    os.makedirs(plugins_dir)
    
    # 创建测试插件
    test_plugin_code = '''
from src.plugins import PreprocessorPlugin, PluginInfo, PluginType

class TestPreprocessor(PreprocessorPlugin):
    def get_info(self) -> PluginInfo:
        return PluginInfo(
            plugin_id="test_preprocessor",
            name="Test Preprocessor",
            version="1.0.0",
            description="Test preprocessor",
            plugin_type=PluginType.PREPROCESSOR
        )
    
    def process(self, text: str) -> str:
        return f"PROCESSED: {text}"
    
    def execute(self, context: dict) -> any:
        return self.process(context.get("text", ""))
'''
    
    with open(os.path.join(plugins_dir, "test_preprocessor.py"), "w") as f:
        f.write(test_plugin_code)
    
    with open(os.path.join(plugins_dir, "__init__.py"), "w") as f:
        f.write('"""Test plugins"""')
    
    # 加载插件
    manager = PluginManager(plugins_dir=plugins_dir)
    info = manager.load_plugin("test_preprocessor")
    
    assert info is not None, "Plugin should load successfully"
    assert info.name == "Test Preprocessor"
    assert info.plugin_type == PluginType.PREPROCESSOR
    assert info.status == PluginStatus.ENABLED
    
    print(f"✓ 插件加载成功: {info.name} v{info.version}")
    
    # 获取插件
    plugin = manager.get_plugin("test_preprocessor")
    assert plugin is not None
    
    # 测试插件执行
    result = plugin.process("test text")
    assert result == "PROCESSED: test text"
    print(f"✓ 插件执行结果: {result}")
    
    # 清理
    shutil.rmtree(temp_dir)
    print("✓ 插件加载测试通过")


def test_plugin_hooks():
    """测试插件钩子"""
    print("\n=== 测试插件钩子")
    
    temp_dir = tempfile.mkdtemp()
    plugins_dir = os.path.join(temp_dir, "plugins")
    os.makedirs(plugins_dir)
    
    # 创建钩子插件
    hook_plugin_code = '''
from src.plugins import MemoryHookPlugin, PluginInfo, PluginType

class TestHookPlugin(MemoryHookPlugin):
    def __init__(self, config: dict):
        super().__init__(config)
        self.add_calls = 0
        self.retrieve_calls = 0
    
    def get_info(self) -> PluginInfo:
        return PluginInfo(
            plugin_id="test_hook",
            name="Test Hook",
            version="1.0.0",
            description="Test hook plugin",
            plugin_type=PluginType.MEMORY_HOOK
        )
    
    def before_memory_add(self, memory_content: dict) -> dict:
        self.add_calls += 1
        memory_content["hooked"] = True
        return memory_content
    
    def after_memory_add(self, memory_id: str, memory_content: dict) -> None:
        pass
    
    def execute(self, context: dict) -> any:
        return {"add_calls": self.add_calls, "retrieve_calls": self.retrieve_calls}
'''
    
    with open(os.path.join(plugins_dir, "test_hook.py"), "w") as f:
        f.write(hook_plugin_code)
    
    with open(os.path.join(plugins_dir, "__init__.py"), "w") as f:
        f.write('"""Test plugins"""')
    
    # 加载插件
    manager = PluginManager(plugins_dir=plugins_dir)
    manager.load_plugin("test_hook")
    
    # 执行钩子
    result = manager.execute_hook("before_memory_add", {"text": "test"})
    assert len(result) > 0
    assert result[0]["hooked"] == True
    
    hook_plugin = manager.get_plugin("test_hook")
    assert hook_plugin.add_calls == 1
    
    print("✓ 钩子执行测试通过")
    
    # 清理
    shutil.rmtree(temp_dir)
    print("✓ 插件钩子测试通过")


def test_plugin_enable_disable():
    """测试插件启用/禁用"""
    print("\n=== 测试插件启用/禁用")
    
    temp_dir = tempfile.mkdtemp()
    plugins_dir = os.path.join(temp_dir, "plugins")
    os.makedirs(plugins_dir)
    
    # 创建测试插件
    test_plugin_code = '''
from src.plugins import BasePlugin, PluginInfo, PluginType

class TogglePlugin(BasePlugin):
    def get_info(self) -> PluginInfo:
        return PluginInfo(
            plugin_id="toggle_plugin",
            name="Toggle Plugin",
            version="1.0.0",
            description="Toggle test",
            plugin_type=PluginType.CUSTOM
        )
    
    def execute(self, context: dict) -> any:
        return {"active": True}
'''
    
    with open(os.path.join(plugins_dir, "toggle_plugin.py"), "w") as f:
        f.write(test_plugin_code)
    
    with open(os.path.join(plugins_dir, "__init__.py"), "w") as f:
        f.write('"""Test plugins"""')
    
    # 加载插件
    manager = PluginManager(plugins_dir=plugins_dir)
    manager.load_plugin("toggle_plugin")
    
    info = manager.get_plugin_info("toggle_plugin")
    assert info.enabled == True
    print("✓ 插件默认启用")
    
    # 禁用插件
    assert manager.disable_plugin("toggle_plugin") == True
    info = manager.get_plugin_info("toggle_plugin")
    assert info.enabled == False
    print("✓ 插件禁用成功")
    
    # 启用插件
    assert manager.enable_plugin("toggle_plugin") == True
    info = manager.get_plugin_info("toggle_plugin")
    assert info.enabled == True
    print("✓ 插件启用成功")
    
    # 清理
    shutil.rmtree(temp_dir)
    print("✓ 插件启用/禁用测试通过")


def test_enhanced_memory():
    """测试增强的记忆系统（带插件）"""
    print("\n=== 测试增强的记忆系统")
    
    temp_dir = tempfile.mkdtemp()
    plugins_dir = os.path.join(temp_dir, "plugins")
    os.makedirs(plugins_dir)
    
    # 创建文本清理插件
    cleaner_code = '''
from src.plugins import PreprocessorPlugin, PluginInfo, PluginType
import re

class TextCleaner(PreprocessorPlugin):
    def get_info(self) -> PluginInfo:
        return PluginInfo(
            plugin_id="text_cleaner",
            name="Text Cleaner",
            version="1.0.0",
            description="Cleans text",
            plugin_type=PluginType.PREPROCESSOR
        )
    
    def process(self, text: str) -> str:
        return re.sub(r'\\s+', ' ', text).strip()
    
    def execute(self, context: dict) -> any:
        return self.process(context.get("text", ""))
'''
    
    with open(os.path.join(plugins_dir, "text_cleaner.py"), "w") as f:
        f.write(cleaner_code)
    
    with open(os.path.join(plugins_dir, "__init__.py"), "w") as f:
        f.write('"""Test plugins"""')
    
    # 创建记忆系统和插件管理器
    memory_system = MockMemorySystem()
    manager = PluginManager(plugins_dir=plugins_dir)
    enhanced = EnhancedMemoryWithPlugins(memory_system, manager)
    
    # 加载插件
    manager.load_plugin("text_cleaner")
    
    # 测试带插件的记忆添加
    test_text = "   Hello   World!   "
    memory_id = enhanced.add_with_plugins(test_text)
    
    # 验证文本被处理了
    assert memory_id in memory_system.memories
    assert memory_system.memories[memory_id]["text"] == "Hello World!"
    print(f"✓ 文本清理成功: '{test_text}' -> 'Hello World!'")
    
    # 测试检索
    results = enhanced.recall_with_plugins("hello")
    assert len(results) > 0
    print("✓ 记忆检索成功")
    
    # 清理
    shutil.rmtree(temp_dir)
    print("✓ 增强记忆系统测试通过")


def test_plugin_statistics():
    """测试插件统计"""
    print("\n=== 测试插件统计")
    
    temp_dir = tempfile.mkdtemp()
    plugins_dir = os.path.join(temp_dir, "plugins")
    os.makedirs(plugins_dir)
    
    # 创建几个测试插件
    for i in range(3):
        plugin_code = f'''
from src.plugins import BasePlugin, PluginInfo, PluginType

class TestPlugin{i}(BasePlugin):
    def get_info(self) -> PluginInfo:
        return PluginInfo(
            plugin_id="test_plugin{i}",
            name="Test Plugin {i}",
            version="1.0.0",
            description="Test",
            plugin_type=PluginType.CUSTOM
        )
    
    def execute(self, context: dict) -> any:
        return None
'''
        with open(os.path.join(plugins_dir, f"test_plugin{i}.py"), "w") as f:
            f.write(plugin_code)
    
    with open(os.path.join(plugins_dir, "__init__.py"), "w") as f:
        f.write('"""Test plugins"""')
    
    # 加载插件
    manager = PluginManager(plugins_dir=plugins_dir)
    manager.load_all_plugins()
    
    # 获取统计
    stats = manager.get_statistics()
    assert stats["total_plugins"] >= 3
    assert stats["loaded_plugins"] >= 3
    
    print(f"✓ 统计信息: {stats}")
    print("✓ 插件统计测试通过")
    
    # 清理
    shutil.rmtree(temp_dir)


def test_global_plugin_manager():
    """测试全局插件管理器"""
    print("\n=== 测试全局插件管理器")
    
    # 获取单例
    manager1 = get_plugin_manager()
    manager2 = get_plugin_manager()
    
    assert manager1 is manager2, "Should return the same instance"
    print("✓ 全局单例获取正常")
    
    print("✓ 全局插件管理器测试通过")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("第39阶段测试：记忆系统插件与扩展架构")
    print("遵循原则：图难于其易，为大于其细")
    print("=" * 60)
    
    try:
        test_plugin_discovery()
        test_plugin_loading()
        test_plugin_hooks()
        test_plugin_enable_disable()
        test_enhanced_memory()
        test_plugin_statistics()
        test_global_plugin_manager()
        
        print("\n" + "=" * 60)
        print("✓ 所有第39阶段测试通过！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
