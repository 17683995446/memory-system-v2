"""
日志钩子插件 - 记忆钩子插件示例
记录所有记忆操作到日志
"""

import time
from src.plugins import (
    BasePlugin,
    MemoryHookPlugin,
    PluginInfo,
    PluginType
)


class LoggingHookPlugin(MemoryHookPlugin):
    """日志钩子插件"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.log_memory_add = config.get("log_memory_add", True)
        self.log_memory_retrieve = config.get("log_memory_retrieve", True)
        self.log_file = config.get("log_file", "memory_operations.log")
    
    def get_info(self) -> PluginInfo:
        return PluginInfo(
            plugin_id="logging_hook",
            name="Logging Hook",
            version="1.0.0",
            description="Logs memory operations to file",
            plugin_type=PluginType.MEMORY_HOOK,
            author="Memory System",
            config={
                "log_memory_add": True,
                "log_memory_retrieve": True,
                "log_file": "memory_operations.log"
            }
        )
    
    def _log(self, message: str) -> None:
        """记录日志"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {message}\n"
        
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_line)
        except Exception:
            print(log_line)
    
    def before_memory_add(self, memory_content: dict) -> dict:
        """记忆添加前"""
        if self.log_memory_add:
            text = memory_content.get("text", "")[:50]
            self._log(f"Adding memory: {text}...")
        return memory_content
    
    def after_memory_add(self, memory_id: str, memory_content: dict) -> None:
        """记忆添加后"""
        if self.log_memory_add:
            self._log(f"Memory added: {memory_id}")
    
    def before_memory_retrieve(self, query: str) -> str:
        """记忆检索前"""
        if self.log_memory_retrieve:
            self._log(f"Retrieving memories for: {query}")
        return query
    
    def after_memory_retrieve(self, results: list) -> list:
        """记忆检索后"""
        if self.log_memory_retrieve:
            self._log(f"Retrieved {len(results)} memories")
        return results
    
    def execute(self, context: dict) -> any:
        """执行插件"""
        action = context.get("action")
        if action == "log":
            message = context.get("message", "")
            self._log(message)
        return None
