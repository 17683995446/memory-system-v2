"""
负载均衡器
用于请求分发
"""

import time
import threading
import random
from typing import Dict, List, Optional, Callable
from enum import Enum


class LoadBalancingStrategy(Enum):
    """负载均衡策略"""
    ROUND_ROBIN = "round_robin"
    RANDOM = "random"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED = "weighted"
    IP_HASH = "ip_hash"


class Backend:
    """后端服务器"""
    def __init__(self, host: str, port: int, weight: int = 1):
        self.host = host
        self.port = port
        self.weight = weight
        self.connections = 0
        self.active = True
    
    def address(self) -> str:
        return f"{self.host}:{self.port}"


class LoadBalancer:
    """负载均衡器"""
    
    def __init__(self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN):
        self.strategy = strategy
        self.backends: List[Backend] = []
        self.current_index = 0
        self._lock = threading.Lock()
    
    def add_backend(self, host: str, port: int, weight: int = 1) -> Backend:
        """添加后端"""
        with self._lock:
            backend = Backend(host, port, weight)
            self.backends.append(backend)
            return backend
    
    def remove_backend(self, backend: Backend) -> bool:
        """移除后端"""
        with self._lock:
            if backend in self.backends:
                self.backends.remove(backend)
                return True
            return False
    
    def get_backend(self, client_ip: Optional[str] = None) -> Optional[Backend]:
        """获取后端"""
        with self._lock:
            if not self.backends:
                return None
            
            active_backends = [b for b in self.backends if b.active]
            if not active_backends:
                return None
            
            if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
                backend = active_backends[self.current_index % len(active_backends)]
                self.current_index += 1
                return backend
            
            elif self.strategy == LoadBalancingStrategy.RANDOM:
                return random.choice(active_backends)
            
            elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
                return min(active_backends, key=lambda b: b.connections)
            
            elif self.strategy == LoadBalancingStrategy.WEIGHTED:
                total_weight = sum(b.weight for b in active_backends)
                rand_val = random.randint(1, total_weight)
                cum_weight = 0
                for backend in active_backends:
                    cum_weight += backend.weight
                    if rand_val <= cum_weight:
                        return backend
                return active_backends[-1]
            
            elif self.strategy == LoadBalancingStrategy.IP_HASH:
                if client_ip:
                    hash_val = hash(client_ip) % len(active_backends)
                    return active_backends[hash_val]
                return random.choice(active_backends)
            
            return active_backends[0]
    
    def backend_used(self, backend: Backend):
        """后端被使用"""
        with self._lock:
            backend.connections += 1
    
    def backend_released(self, backend: Backend):
        """后端释放"""
        with self._lock:
            if backend.connections > 0:
                backend.connections -= 1
    
    def get_stats(self) -> Dict:
        """获取统计"""
        with self._lock:
            return {
                "total_backends": len(self.backends),
                "active_backends": len([b for b in self.backends if b.active]),
                "strategy": self.strategy.value,
                "backends": [
                    {
                        "address": b.address(),
                        "weight": b.weight,
                        "connections": b.connections,
                        "active": b.active
                    }
                    for b in self.backends
                ]
            }


_global_load_balancer: Optional[LoadBalancer] = None


def get_load_balancer(strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN) -> LoadBalancer:
    """获取负载均衡器"""
    global _global_load_balancer
    if _global_load_balancer is None:
        _global_load_balancer = LoadBalancer(strategy)
    return _global_load_balancer
