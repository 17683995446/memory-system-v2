"""
插件系统
用于扩展功能
"""

import time
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Plugin:
    """插件"""
    plugin_id: str
    name: str
    version: str
    author: str
    description: str
    hooks: Dict[str, Callable] = field(default_factory=dict)
    enabled: bool = True
    loaded_at: Optional[datetime] = None


class PluginManager:
    """插件管理器"""
    
    def __init__(self):
        self.plugins: Dict[str, Plugin] = {}
        self._plugin_counter: int = 0
        self._lock = threading.Lock()
    
    def register_plugin(
        self,
        name: str,
        version: str,
        author: str,
        description: str,
        hooks: Dict[str, Callable]
    ) -> str:
        """注册插件"""
        with self._lock:
            self._plugin_counter += 1
            plugin_id = f"PLUGIN-{self._plugin_counter:06d}"
            
            plugin = Plugin(
                plugin_id=plugin_id,
                name=name,
                version=version,
                author=author,
                description=description,
                hooks=hooks,
                loaded_at=datetime.now()
            )
            
            self.plugins[plugin_id] = plugin
            return plugin_id
    
    def unregister_plugin(self, plugin_id: str) -> bool:
        """注销插件"""
        with self._lock:
            if plugin_id in self.plugins:
                del self.plugins[plugin_id]
                return True
            return False
    
    def enable_plugin(self, plugin_id: str) -> bool:
        """启用插件"""
        if plugin_id not in self.plugins:
            return False
        self.plugins[plugin_id].enabled = True
        return True
    
    def disable_plugin(self, plugin_id: str) -> bool:
        """禁用插件"""
        if plugin_id not in self.plugins:
            return False
        self.plugins[plugin_id].enabled = False
        return True
    
    def execute_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """执行钩子"""
        results = []
        
        for plugin in self.plugins.values():
            if not plugin.enabled:
                continue
            
            if hook_name in plugin.hooks:
                try:
                    result = plugin.hooks[hook_name](*args, **kwargs)
                    results.append(result)
                except Exception:
                    pass
        
        return results
    
    def get_plugin(self, plugin_id: str) -> Optional[Plugin]:
        """获取插件"""
        return self.plugins.get(plugin_id)
    
    def get_all_plugins(self) -> List[Plugin]:
        """获取所有插件"""
        return list(self.plugins.values())


_global_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """获取全局插件管理器"""
    global _global_plugin_manager
    if _global_plugin_manager is None:
        _global_plugin_manager = PluginManager()
    return _global_plugin_manager
