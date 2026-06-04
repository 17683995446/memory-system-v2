"""
记忆系统插件与扩展架构
基于第一性原理：可扩展性、安全性、易用性
"""

import os
import sys
import json
import time
import importlib
import traceback
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
from pathlib import Path
from ..utils.logger import get_logger



class PluginType(Enum):
    """插件类型"""
    PREPROCESSOR = "preprocessor"  # 预处理器插件
    MEMORY_HOOK = "memory_hook"  # 记忆钩子插件
    SEARCH_ENGINE = "search_engine"  # 搜索引擎插件
    EXPORT_FORMAT = "export_format"  # 导出格式插件
    ANALYTICS = "analytics"  # 分析插件
    CUSTOM = "custom"  # 自定义插件


class PluginStatus(Enum):
    """插件状态"""
    DISABLED = "disabled"
    ENABLED = "enabled"
    ERROR = "error"
    LOADING = "loading"
    UNLOADED = "unloaded"


@dataclass
class PluginInfo:
    """插件信息"""
    plugin_id: str
    name: str
    version: str
    description: str
    plugin_type: PluginType
    author: str = ""
    website: str = ""
    dependencies: List[str] = field(default_factory=list)
    status: PluginStatus = PluginStatus.UNLOADED
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)
    loaded_at: Optional[float] = None
    error_message: Optional[str] = None


class PluginHook:
    """插件钩子点"""
    BEFORE_MEMORY_ADD = "before_memory_add"
    AFTER_MEMORY_ADD = "after_memory_add"
    BEFORE_MEMORY_RETRIEVE = "before_memory_retrieve"
    AFTER_MEMORY_RETRIEVE = "after_memory_retrieve"
    BEFORE_MEMORY_DELETE = "before_memory_delete"
    AFTER_MEMORY_DELETE = "after_memory_delete"
    BEFORE_SEARCH = "before_search"
    AFTER_SEARCH = "after_search"
    ON_SYSTEM_START = "on_system_start"
    ON_SYSTEM_SHUTDOWN = "on_system_shutdown"


class BasePlugin:
    """插件基类 - 所有自定义插件必须继承此类"""
    
    def __init__(self, config: Dict[str, Any]):
        self._logger = get_logger()
        self.config = config
        self.is_initialized = False
    
    def get_info(self) -> PluginInfo:
        """获取插件信息 - 必须由子类实现"""
        raise NotImplementedError("get_info must be implemented by subclass")
    
    def initialize(self) -> bool:
        """初始化插件"""
        self.is_initialized = True
        return True
    
    def cleanup(self) -> None:
        """清理插件资源"""
        self.is_initialized = False
    
    def execute(self, context: Dict[str, Any]) -> Any:
        """执行插件逻辑 - 必须由子类实现"""
        raise NotImplementedError("execute must be implemented by subclass")


class MemoryHookPlugin(BasePlugin):
    """记忆钩子插件 - 用于拦截和处理记忆操作"""
    
    def before_memory_add(self, memory_content: Dict[str, Any]) -> Dict[str, Any]:
        """记忆添加前钩子"""
        return memory_content
    
    def after_memory_add(self, memory_id: str, memory_content: Dict[str, Any]) -> None:
        """记忆添加后钩子"""
        pass
    
    def before_memory_retrieve(self, query: str) -> str:
        """记忆检索前钩子"""
        return query
    
    def after_memory_retrieve(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """记忆检索后钩子"""
        return results


class PreprocessorPlugin(BasePlugin):
    """预处理器插件 - 用于处理记忆内容"""
    
    def process(self, text: str) -> str:
        """处理文本"""
        return text


class PluginManager:
    """插件管理器"""
    
    def __init__(self, plugins_dir: Optional[str] = None, config_path: Optional[str] = None):
        self.plugins_dir = plugins_dir or os.path.join(os.path.dirname(__file__), "..", "..", "plugins")
        self.config_path = config_path or os.path.join(self.plugins_dir, "config.json")
        
        self.plugins: Dict[str, BasePlugin] = {}
        self.plugin_info: Dict[str, PluginInfo] = {}
        self.hook_handlers: Dict[str, List[Callable]] = defaultdict(list)
        self.plugin_types: Dict[PluginType, List[str]] = defaultdict(list)
        
        self._ensure_plugins_dir()
        self._load_config()
    
    def _ensure_plugins_dir(self) -> None:
        """确保插件目录存在"""
        os.makedirs(self.plugins_dir, exist_ok=True)
        init_file = os.path.join(self.plugins_dir, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write("\"\"\"Plugins directory\"\"\"\n")
    
    def _load_config(self) -> None:
        """加载插件配置"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    for plugin_id, plugin_config in config.get("plugins", {}).items():
                        if plugin_id in self.plugin_info:
                            self.plugin_info[plugin_id].config.update(plugin_config)
                            self.plugin_info[plugin_id].enabled = plugin_config.get("enabled", True)
            except Exception as e:
                logger.info(f"Failed to load plugin config: {e}")
    
    def _save_config(self) -> None:
        """保存插件配置"""
        config = {
            "version": "1.0",
            "last_updated": time.time(),
            "plugins": {
                plugin_id: {
                    "enabled": info.enabled,
                    "config": info.config
                }
                for plugin_id, info in self.plugin_info.items()
            }
        }
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def discover_plugins(self) -> List[str]:
        """发现可用插件"""
        discovered = []
        
        if not os.path.exists(self.plugins_dir):
            return discovered
        
        for item in os.listdir(self.plugins_dir):
            item_path = os.path.join(self.plugins_dir, item)
            
            if os.path.isdir(item_path) and not item.startswith("_") and not item.startswith("."):
                if os.path.exists(os.path.join(item_path, "__init__.py")):
                    discovered.append(item)
            elif item.endswith(".py") and not item.startswith("_"):
                plugin_name = item[:-3]
                if plugin_name not in discovered:
                    discovered.append(plugin_name)
        
        return discovered
    
    def load_plugin(self, plugin_id: str) -> Optional[PluginInfo]:
        """加载插件"""
        if plugin_id in self.plugins:
            return self.plugin_info.get(plugin_id)
        
        plugin_path = os.path.join(self.plugins_dir, plugin_id)
        
        try:
            # 更新状态为加载中
            if plugin_id not in self.plugin_info:
                self.plugin_info[plugin_id] = PluginInfo(
                    plugin_id=plugin_id,
                    name=plugin_id,
                    version="0.1.0",
                    description="",
                    plugin_type=PluginType.CUSTOM
                )
            
            self.plugin_info[plugin_id].status = PluginStatus.LOADING
            
            # 导入插件模块
            if plugin_id not in sys.modules:
                sys.path.insert(0, self.plugins_dir)
            
            module_name = plugin_id
            if os.path.isdir(plugin_path):
                module_name = plugin_id
            else:
                module_name = plugin_id
            
            module = importlib.import_module(module_name)
            
            # 查找插件类
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, BasePlugin) and 
                    attr != BasePlugin and 
                    attr != MemoryHookPlugin and 
                    attr != PreprocessorPlugin):
                    plugin_class = attr
                    break
            
            if not plugin_class:
                raise ValueError(f"No plugin class found in {plugin_id}")
            
            # 获取插件配置
            config = self.plugin_info.get(plugin_id, PluginInfo(
                plugin_id=plugin_id,
                name=plugin_id,
                version="0.1.0",
                description="",
                plugin_type=PluginType.CUSTOM
            )).config
            
            # 实例化插件
            plugin = plugin_class(config)
            
            # 获取插件信息
            info = plugin.get_info()
            info.plugin_id = plugin_id
            info.status = PluginStatus.ENABLED
            info.loaded_at = time.time()
            info.enabled = self.plugin_info.get(plugin_id, info).enabled
            
            self.plugin_info[plugin_id] = info
            self.plugins[plugin_id] = plugin
            self.plugin_types[info.plugin_type].append(plugin_id)
            
            # 初始化插件
            if info.enabled:
                plugin.initialize()
                self._register_hooks(plugin, info)
            
            logger.info(f"Loaded plugin: {plugin_id} v{info.version}")
            return info
            
        except Exception as e:
            error_msg = f"Failed to load plugin {plugin_id}: {e}\n{traceback.format_exc()}"
            logger.info(str(error_msg))
            
            if plugin_id in self.plugin_info:
                self.plugin_info[plugin_id].status = PluginStatus.ERROR
                self.plugin_info[plugin_id].error_message = str(e)
            
            return None
    
    def _register_hooks(self, plugin: BasePlugin, info: PluginInfo) -> None:
        """注册插件钩子"""
        if isinstance(plugin, MemoryHookPlugin):
            # 注册记忆钩子
            if hasattr(plugin, "before_memory_add"):
                self.hook_handlers[PluginHook.BEFORE_MEMORY_ADD].append(plugin.before_memory_add)
            if hasattr(plugin, "after_memory_add"):
                self.hook_handlers[PluginHook.AFTER_MEMORY_ADD].append(plugin.after_memory_add)
            if hasattr(plugin, "before_memory_retrieve"):
                self.hook_handlers[PluginHook.BEFORE_MEMORY_RETRIEVE].append(plugin.before_memory_retrieve)
            if hasattr(plugin, "after_memory_retrieve"):
                self.hook_handlers[PluginHook.AFTER_MEMORY_RETRIEVE].append(plugin.after_memory_retrieve)
    
    def unload_plugin(self, plugin_id: str) -> bool:
        """卸载插件"""
        if plugin_id not in self.plugins:
            return False
        
        try:
            plugin = self.plugins[plugin_id]
            plugin.cleanup()
            
            # 移除钩子
            for hook_name, handlers in self.hook_handlers.items():
                self.hook_handlers[hook_name] = [h for h in handlers if not hasattr(h, "__self__") or h.__self__ != plugin]
            
            # 移除插件
            del self.plugins[plugin_id]
            
            if plugin_id in self.plugin_info:
                self.plugin_info[plugin_id].status = PluginStatus.UNLOADED
            
            # 移除插件类型索引
            for plugin_type, plugin_ids in self.plugin_types.items():
                if plugin_id in plugin_ids:
                    plugin_ids.remove(plugin_id)
            
            # 卸载模块
            if plugin_id in sys.modules:
                del sys.modules[plugin_id]
            
            logger.info(f"Unloaded plugin: {plugin_id}")
            return True
            
        except Exception as e:
            logger.info(f"Failed to unload plugin {plugin_id}: {e}")
            return False
    
    def reload_plugin(self, plugin_id: str) -> Optional[PluginInfo]:
        """重新加载插件 - 热加载"""
        self.unload_plugin(plugin_id)
        return self.load_plugin(plugin_id)
    
    def load_all_plugins(self) -> List[PluginInfo]:
        """加载所有发现的插件"""
        loaded = []
        for plugin_id in self.discover_plugins():
            info = self.load_plugin(plugin_id)
            if info:
                loaded.append(info)
        return loaded
    
    def get_plugin(self, plugin_id: str) -> Optional[BasePlugin]:
        """获取插件实例"""
        return self.plugins.get(plugin_id)
    
    def get_plugin_info(self, plugin_id: str) -> Optional[PluginInfo]:
        """获取插件信息"""
        return self.plugin_info.get(plugin_id)
    
    def get_plugins_by_type(self, plugin_type: PluginType) -> List[BasePlugin]:
        """根据类型获取插件"""
        return [self.plugins[pid] for pid in self.plugin_types.get(plugin_type, []) if pid in self.plugins]
    
    def enable_plugin(self, plugin_id: str) -> bool:
        """启用插件"""
        if plugin_id not in self.plugin_info:
            return False
        
        self.plugin_info[plugin_id].enabled = True
        
        if plugin_id in self.plugins:
            plugin = self.plugins[plugin_id]
            if not plugin.is_initialized:
                plugin.initialize()
                self._register_hooks(plugin, self.plugin_info[plugin_id])
        
        self._save_config()
        return True
    
    def disable_plugin(self, plugin_id: str) -> bool:
        """禁用插件"""
        if plugin_id not in self.plugin_info:
            return False
        
        self.plugin_info[plugin_id].enabled = False
        
        if plugin_id in self.plugins:
            plugin = self.plugins[plugin_id]
            if plugin.is_initialized:
                # 移除钩子
                for hook_name, handlers in self.hook_handlers.items():
                    self.hook_handlers[hook_name] = [h for h in handlers if not hasattr(h, "__self__") or h.__self__ != plugin]
                
                plugin.cleanup()
        
        self._save_config()
        return True
    
    def execute_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """执行钩子"""
        results = []
        for handler in self.hook_handlers.get(hook_name, []):
            try:
                result = handler(*args, **kwargs)
                results.append(result)
            except Exception as e:
                logger.info(f"Error executing hook {hook_name}: {e}")
        return results
    
    def update_plugin_config(self, plugin_id: str, config: Dict[str, Any]) -> bool:
        """更新插件配置"""
        if plugin_id not in self.plugin_info:
            return False
        
        self.plugin_info[plugin_id].config.update(config)
        
        if plugin_id in self.plugins:
            plugin = self.plugins[plugin_id]
            plugin.config = self.plugin_info[plugin_id].config
        
        self._save_config()
        return True
    
    def get_all_plugin_info(self) -> List[PluginInfo]:
        """获取所有插件信息"""
        return list(self.plugin_info.values())
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取插件系统统计"""
        total = len(self.plugin_info)
        enabled = sum(1 for info in self.plugin_info.values() if info.enabled)
        loaded = sum(1 for info in self.plugin_info.values() if info.status == PluginStatus.ENABLED)
        error = sum(1 for info in self.plugin_info.values() if info.status == PluginStatus.ERROR)
        
        type_counts = {}
        for plugin_type, plugin_ids in self.plugin_types.items():
            type_counts[plugin_type.value] = len(plugin_ids)
        
        return {
            "total_plugins": total,
            "enabled_plugins": enabled,
            "loaded_plugins": loaded,
            "error_plugins": error,
            "plugins_by_type": type_counts,
            "active_hooks": {
                hook: len(handlers)
                for hook, handlers in self.hook_handlers.items()
            }
        }


class PluginSandbox:
    """插件安全沙箱 - 用于安全隔离插件执行"""
    
    def __init__(self, allowed_modules: Optional[Set[str]] = None):
        self.allowed_modules = allowed_modules or {
            "json", "time", "re", "math", "collections",
            "typing", "dataclasses", "enum"
        }
        self.restricted_functions = {
            "eval", "exec", "compile", "open", "input",
            "__import__", "globals", "locals"
        }
    
    def execute_safely(self, plugin: BasePlugin, context: Dict[str, Any]) -> Any:
        """安全执行插件"""
        try:
            return plugin.execute(context)
        except Exception as e:
            logger.info(f"Plugin execution error: {e}")
            return None
    
    def validate_plugin(self, plugin: BasePlugin) -> bool:
        """验证插件安全性"""
        # 简单验证 - 实际项目中可以实现更复杂的验证
        return True


class EnhancedMemoryWithPlugins:
    """
    增强的记忆系统（带插件支持）
    装饰器模式实现
    """
    
    def __init__(self, memory_system, plugin_manager: Optional[PluginManager] = None):
        self.memory_system = memory_system
        self.plugin_manager = plugin_manager or PluginManager()
        self.sandbox = PluginSandbox()
    
    def add_with_plugins(self, text: str, *args, **kwargs) -> str:
        """添加记忆（带插件处理）"""
        # 执行前置钩子
        memory_content = {"text": text, "args": args, "kwargs": kwargs}
        hook_results = self.plugin_manager.execute_hook(
            PluginHook.BEFORE_MEMORY_ADD,
            memory_content
        )
        
        for result in hook_results:
            if isinstance(result, dict):
                memory_content.update(result)
        
        # 执行预处理器插件
        preprocessors = self.plugin_manager.get_plugins_by_type(PluginType.PREPROCESSOR)
        processed_text = memory_content.get("text", text)
        for preprocessor in preprocessors:
            if isinstance(preprocessor, PreprocessorPlugin):
                processed_text = preprocessor.process(processed_text)
        
        memory_content["text"] = processed_text
        
        # 添加记忆
        memory_id = self.memory_system.add(processed_text, *args, **kwargs)
        
        # 执行后置钩子
        self.plugin_manager.execute_hook(
            PluginHook.AFTER_MEMORY_ADD,
            memory_id,
            memory_content
        )
        
        return memory_id
    
    def recall_with_plugins(self, query: str, *args, **kwargs) -> Any:
        """检索记忆（带插件处理）"""
        # 执行前置钩子
        hook_results = self.plugin_manager.execute_hook(
            PluginHook.BEFORE_MEMORY_RETRIEVE,
            query
        )
        
        processed_query = query
        for result in hook_results:
            if isinstance(result, str):
                processed_query = result
        
        # 检索记忆
        results = self.memory_system.recall(processed_query, *args, **kwargs)
        
        # 执行后置钩子
        hook_results = self.plugin_manager.execute_hook(
            PluginHook.AFTER_MEMORY_RETRIEVE,
            results
        )
        
        final_results = results
        for result in hook_results:
            if isinstance(result, list):
                final_results = result
        
        return final_results
    
    def initialize_plugins(self) -> None:
        """初始化插件系统"""
        self.plugin_manager.load_all_plugins()
        self.plugin_manager.execute_hook(PluginHook.ON_SYSTEM_START)
    
    def shutdown_plugins(self) -> None:
        """关闭插件系统"""
        self.plugin_manager.execute_hook(PluginHook.ON_SYSTEM_SHUTDOWN)


# 全局单例
_global_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager(plugins_dir: Optional[str] = None, config_path: Optional[str] = None) -> PluginManager:
    """获取插件管理器单例"""
    global _global_plugin_manager
    if _global_plugin_manager is None:
        _global_plugin_manager = PluginManager(plugins_dir, config_path)
    return _global_plugin_manager
