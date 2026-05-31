"""
日志模块 - 记录读写、召回、治理行为
基于第一性原理：可追溯、可监控
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional


def setup_logger(name: str = "agent_memory", log_dir: str = "./logs") -> logging.Logger:
    """设置日志"""
    os.makedirs(log_dir, exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # 避免重复添加handler
    if logger.handlers:
        return logger
    
    # 格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件handler - 按天分割
    today = datetime.now().strftime('%Y-%m-%d')
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, f"{name}_{today}.log"),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=30,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


# 全局日志单例
_logger: Optional[logging.Logger] = None


def get_logger() -> logging.Logger:
    """获取全局日志"""
    global _logger
    if _logger is None:
        _logger = setup_logger()
    return _logger
