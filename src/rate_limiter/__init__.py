"""
限流器
用于API和资源访问控制
"""

import time
import threading
from typing import Dict, Optional
from datetime import datetime, timedelta


class RateLimiter:
    """限流器"""
    
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = {}
        self._lock = threading.Lock()
    
    def allow_request(self, client_id: str) -> bool:
        """检查是否允许请求"""
        with self._lock:
            now = datetime.now()
            window_start = now - timedelta(seconds=self.window_seconds)
            
            if client_id not in self.requests:
                self.requests[client_id] = []
            
            self.requests[client_id] = [
                ts for ts in self.requests[client_id]
                if ts > window_start
            ]
            
            if len(self.requests[client_id]) < self.max_requests:
                self.requests[client_id].append(now)
                return True
            
            return False
    
    def get_remaining(self, client_id: str) -> int:
        """获取剩余请求数"""
        with self._lock:
            if client_id not in self.requests:
                return self.max_requests
            
            now = datetime.now()
            window_start = now - timedelta(seconds=self.window_seconds)
            
            recent_requests = [
                ts for ts in self.requests[client_id]
                if ts > window_start
            ]
            
            return max(0, self.max_requests - len(recent_requests))
    
    def reset(self, client_id: str):
        """重置客户端限制"""
        with self._lock:
            if client_id in self.requests:
                self.requests[client_id] = []


class RateLimitManager:
    """限流管理器"""
    
    def __init__(self):
        self.limiters: Dict[str, RateLimiter] = {}
        self._lock = threading.Lock()
    
    def create_limiter(
        self,
        name: str,
        max_requests: int,
        window_seconds: int
    ) -> RateLimiter:
        """创建限流器"""
        with self._lock:
            limiter = RateLimiter(max_requests, window_seconds)
            self.limiters[name] = limiter
            return limiter
    
    def get_limiter(self, name: str) -> Optional[RateLimiter]:
        """获取限流器"""
        return self.limiters.get(name)
    
    def check_limit(self, limiter_name: str, client_id: str) -> bool:
        """检查限制"""
        limiter = self.limiters.get(limiter_name)
        if not limiter:
            return True
        return limiter.allow_request(client_id)


_global_rate_limiter: Optional[RateLimitManager] = None


def get_rate_limiter() -> RateLimitManager:
    """获取全局限流管理器"""
    global _global_rate_limiter
    if _global_rate_limiter is None:
        _global_rate_limiter = RateLimitManager()
    return _global_rate_limiter
