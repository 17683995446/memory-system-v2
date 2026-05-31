"""
热重载系统
用于运行时更新代码
"""

import time
import threading
import importlib
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class HotReloadModule:
    """热重载模块"""
    module_name: str
    module: Any
    last_modified: datetime
    reload_count: int = 0


class HotReloadManager:
    """热重载管理器"""
    
    def __init__(self):
        self.modules: Dict[str, HotReloadModule] = {}
        self._lock = threading.Lock()
        self._watching: bool = False
        self._watch_thread: Optional[threading.Thread] = None
    
    def register_module(self, module_name: str, module: Any) -> bool:
        """注册模块"""
        with self._lock:
            hot_module = HotReloadModule(
                module_name=module_name,
                module=module,
                last_modified=datetime.now()
            )
            self.modules[module_name] = hot_module
            return True
    
    def reload_module(self, module_name: str) -> bool:
        """重载模块"""
        with self._lock:
            if module_name not in self.modules:
                return False
            
            try:
                hot_module = self.modules[module_name]
                importlib.reload(hot_module.module)
                hot_module.reload_count += 1
                hot_module.last_modified = datetime.now()
                return True
            except Exception:
                return False
    
    def reload_all(self) -> Dict[str, bool]:
        """重载所有模块"""
        results = {}
        for module_name in self.modules:
            results[module_name] = self.reload_module(module_name)
        return results
    
    def get_module(self, module_name: str) -> Optional[HotReloadModule]:
        """获取模块"""
        return self.modules.get(module_name)
    
    def start_watching(self, interval: int = 60):
        """开始监控"""
        if self._watching:
            return
        
        self._watching = True
        self._watch_thread = threading.Thread(
            target=self._watch_loop,
            args=(interval,),
            daemon=True
        )
        self._watch_thread.start()
    
    def stop_watching(self):
        """停止监控"""
        self._watching = False
        if self._watch_thread:
            self._watch_thread.join(timeout=5.0)
    
    def _watch_loop(self, interval: int):
        """监控循环"""
        while self._watching:
            self.reload_all()
            time.sleep(interval)


_global_hot_reload: Optional[HotReloadManager] = None


def get_hot_reload_manager() -> HotReloadManager:
    """获取全局热重载管理器"""
    global _global_hot_reload
    if _global_hot_reload is None:
        _global_hot_reload = HotReloadManager()
    return _global_hot_reload
