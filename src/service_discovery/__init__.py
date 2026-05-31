"""
服务发现
用于微服务注册与发现
"""

import time
import threading
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ServiceInstance:
    """服务实例"""
    instance_id: str
    service_name: str
    host: str
    port: int
    metadata: Dict[str, str] = field(default_factory=dict)
    healthy: bool = True
    registered_at: datetime = field(default_factory=datetime.now)
    last_heartbeat: datetime = field(default_factory=datetime.now)


class ServiceRegistry:
    """服务注册表"""
    
    def __init__(self):
        self.services: Dict[str, List[ServiceInstance]] = {}
        self._lock = threading.Lock()
    
    def register(
        self,
        service_name: str,
        host: str,
        port: int,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """注册服务"""
        with self._lock:
            import uuid
            instance_id = f"INST-{uuid.uuid4().hex[:12]}"
            
            instance = ServiceInstance(
                instance_id=instance_id,
                service_name=service_name,
                host=host,
                port=port,
                metadata=metadata or {}
            )
            
            if service_name not in self.services:
                self.services[service_name] = []
            self.services[service_name].append(instance)
            
            return instance_id
    
    def deregister(self, instance_id: str) -> bool:
        """注销服务"""
        with self._lock:
            for service_name, instances in self.services.items():
                for i, instance in enumerate(instances):
                    if instance.instance_id == instance_id:
                        instances.pop(i)
                        return True
            return False
    
    def heartbeat(self, instance_id: str) -> bool:
        """发送心跳"""
        with self._lock:
            for instances in self.services.values():
                for instance in instances:
                    if instance.instance_id == instance_id:
                        instance.last_heartbeat = datetime.now()
                        return True
            return False
    
    def discover(self, service_name: str) -> List[ServiceInstance]:
        """发现服务"""
        with self._lock:
            if service_name not in self.services:
                return []
            
            healthy_instances = [
                inst for inst in self.services[service_name]
                if inst.healthy
            ]
            
            return healthy_instances
    
    def get_all_services(self) -> Dict[str, int]:
        """获取所有服务"""
        with self._lock:
            return {
                name: len(instances)
                for name, instances in self.services.items()
            }


_global_registry: Optional[ServiceRegistry] = None


def get_service_registry() -> ServiceRegistry:
    """获取全局服务注册表"""
    global _global_registry
    if _global_registry is None:
        _global_registry = ServiceRegistry()
    return _global_registry
