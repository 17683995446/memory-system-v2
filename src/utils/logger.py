"""
增强日志系统
用于代码执行追踪和问题诊断
"""

import logging
import sys
import os
import threading
import traceback
from datetime import datetime
from typing import Optional, Dict, Any
from functools import wraps


class ExecutionLogger:
    """执行日志记录器"""
    
    def __init__(self, name: str = "memory_system"):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        
        # 创建文件处理器
        log_dir = "/workspace/logs"
        os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(
            f"{log_dir}/{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        file_handler.setLevel(logging.DEBUG)
        
        # 设置格式
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] [%(threadName)s] %(message)s'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        
        self._call_counter: Dict[str, int] = {}
        self._lock = threading.Lock()
    
    def log_entry(self, func_name: str, args: tuple, kwargs: dict):
        """记录函数入口"""
        with self._lock:
            self._call_counter[func_name] = self._call_counter.get(func_name, 0) + 1
            call_id = self._call_counter[func_name]
        
        self.logger.debug(f"[ENTRY] {func_name} (#{call_id}) args={args}, kwargs={kwargs}")
    
    def log_exit(self, func_name: str, result: Any, duration_ms: float):
        """记录函数出口"""
        self.logger.debug(
            f"[EXIT] {func_name} result={result}, duration={duration_ms:.2f}ms"
        )
    
    def log_error(self, func_name: str, error: Exception):
        """记录错误"""
        self.logger.error(
            f"[ERROR] {func_name}: {str(error)}\n{traceback.format_exc()}"
        )
    
    def log_state(self, component: str, state: Dict[str, Any]):
        """记录状态"""
        self.logger.info(f"[STATE] {component}: {state}")
    
    def log_decision(self, component: str, decision: str, reason: str):
        """记录决策"""
        self.logger.info(f"[DECISION] {component}: {decision} (reason: {reason})")
    
    def log_data_flow(self, from_component: str, to_component: str, data: Any):
        """记录数据流"""
        self.logger.debug(f"[DATA_FLOW] {from_component} -> {to_component}: {type(data).__name__}")
    
    def log_boundary(self, boundary_type: str, value: Any, is_valid: bool):
        """记录边界检查"""
        status = "PASS" if is_valid else "FAIL"
        self.logger.debug(f"[BOUNDARY] {boundary_type}: {value} [{status}]")
    
    def info(self, message: str):
        """记录信息日志（兼容标准logger接口）"""
        self.logger.info(message)
    
    def debug(self, message: str):
        """记录调试日志（兼容标准logger接口）"""
        self.logger.debug(message)
    
    def warning(self, message: str):
        """记录警告日志（兼容标准logger接口）"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """记录错误日志（兼容标准logger接口）"""
        self.logger.error(message)


# 全局日志实例
_global_logger: Optional[ExecutionLogger] = None


def get_logger() -> ExecutionLogger:
    """获取全局日志实例"""
    global _global_logger
    if _global_logger is None:
        _global_logger = ExecutionLogger()
    return _global_logger


def trace_execution(logger: Optional[ExecutionLogger] = None):
    """执行追踪装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            log = logger or get_logger()
            start_time = datetime.now()
            
            log.log_entry(func.__name__, args, kwargs)
            
            try:
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds() * 1000
                log.log_exit(func.__name__, result, duration)
                return result
            except Exception as e:
                log.log_error(func.__name__, e)
                raise
        
        return wrapper
    return decorator
