"""
配置中心
用于集中化配置管理
"""

import time
import threading
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
from enum import Enum


class ConfigSource(Enum):
    """配置来源"""
    MEMORY = "memory"
    FILE = "file"
    ENV = "environment"
    REMOTE = "remote"


@dataclass
class ConfigEntry:
    """配置项"""
    key: str
    value: Any
    source: ConfigSource
    updated_at: datetime
    version: int = 1


class ConfigCenter:
    """配置中心"""
    
    def __init__(self):
        self.configs: Dict[str, ConfigEntry] = {}
        self._lock = threading.Lock()
        self._version_counter: int = 0
    
    def set(
        self,
        key: str,
        value: Any,
        source: ConfigSource = ConfigSource.MEMORY
    ) -> bool:
        """设置配置"""
        with self._lock:
            self._version_counter += 1
            
            entry = ConfigEntry(
                key=key,
                value=value,
                source=source,
                updated_at=datetime.now(),
                version=self._version_counter
            )
            
            self.configs[key] = entry
            return True
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置"""
        with self._lock:
            if key in self.configs:
                return self.configs[key].value
            return default
    
    def delete(self, key: str) -> bool:
        """删除配置"""
        with self._lock:
            if key in self.configs:
                del self.configs[key]
                return True
            return False
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        with self._lock:
            return {
                key: entry.value
                for key, entry in self.configs.items()
            }
    
    def get_config_info(self, key: str) -> Optional[ConfigEntry]:
        """获取配置信息"""
        return self.configs.get(key)
    
    def batch_set(
        self,
        configs: Dict[str, Any],
        source: ConfigSource = ConfigSource.MEMORY
    ) -> int:
        """批量设置配置"""
        count = 0
        for key, value in configs.items():
            if self.set(key, value, source):
                count += 1
        return count
    
    def export_to_json(self) -> str:
        """导出为JSON"""
        with self._lock:
            return json.dumps(
                {key: entry.value for key, entry in self.configs.items()},
                indent=2,
                default=str
            )
    
    def import_from_json(self, json_str: str, source: ConfigSource = ConfigSource.FILE) -> int:
        """从JSON导入"""
        try:
            configs = json.loads(json_str)
            return self.batch_set(configs, source)
        except Exception:
            return 0
    
    def watch(self, key: str, callback: Callable[[str, Any], None]):
        """监视配置变化（简化版）"""
        pass


_global_config_center: Optional[ConfigCenter] = None


def get_config_center() -> ConfigCenter:
    """获取全局配置中心"""
    global _global_config_center
    if _global_config_center is None:
        _global_config_center = ConfigCenter()
    return _global_config_center


from enum import Enum
from typing import Callable
