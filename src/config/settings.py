"""
配置模块 - 动态调整阈值参数
基于第一性原理：确定性、可配置
支持环境变量配置和热更新
"""
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class L1Config:
    """L1记忆配置"""
    max_items_per_task: int = 100
    max_tasks: int = 1000
    
    @classmethod
    def from_env(cls):
        """从环境变量加载"""
        return cls(
            max_items_per_task=int(os.getenv('L1_MAX_ITEMS', 100)),
            max_tasks=int(os.getenv('L1_MAX_TASKS', 1000))
        )


@dataclass
class L2Config:
    """L2记忆配置"""
    dimension: int = 384
    top_k: int = 5
    similarity_threshold: float = 0.7
    cleanup_days: int = 30
    index_file: str = "./data/l2_index.faiss"
    metadata_file: str = "./data/l2_metadata.json"
    
    @classmethod
    def from_env(cls):
        """从环境变量加载"""
        return cls(
            dimension=int(os.getenv('L2_DIMENSION', 384)),
            top_k=int(os.getenv('L2_TOP_K', 5)),
            similarity_threshold=float(os.getenv('L2_SIMILARITY_THRESHOLD', 0.7)),
            cleanup_days=int(os.getenv('L2_CLEANUP_DAYS', 30)),
            index_file=os.getenv('L2_INDEX_FILE', './data/l2_index.faiss'),
            metadata_file=os.getenv('L2_METADATA_FILE', './data/l2_metadata.json')
        )


@dataclass
class L3Config:
    """L3记忆配置"""
    db_file: str = "./data/l3_memory.db"
    
    @classmethod
    def from_env(cls):
        """从环境变量加载"""
        return cls(
            db_file=os.getenv('L3_DB_FILE', './data/l3_memory.db')
        )


@dataclass
class EmbeddingConfig:
    """Embedding配置"""
    model_name: str = "all-MiniLM-L6-v2"
    
    @classmethod
    def from_env(cls):
        """从环境变量加载"""
        return cls(
            model_name=os.getenv('EMBEDDING_MODEL_NAME', 'all-MiniLM-L6-v2')
        )


@dataclass
class LogConfig:
    """日志配置"""
    log_dir: str = "./logs"
    log_level: str = "INFO"
    
    @classmethod
    def from_env(cls):
        """从环境变量加载"""
        return cls(
            log_dir=os.getenv('LOG_DIR', './logs'),
            log_level=os.getenv('LOG_LEVEL', 'INFO')
        )


@dataclass
class RecallConfig:
    """召回配置"""
    max_l1_items: int = 3
    max_l2_items: int = 5
    max_l3_items: int = 2
    total_limit: int = 10
    
    @classmethod
    def from_env(cls):
        """从环境变量加载"""
        return cls(
            max_l1_items=int(os.getenv('RECALL_MAX_L1', 3)),
            max_l2_items=int(os.getenv('RECALL_MAX_L2', 5)),
            max_l3_items=int(os.getenv('RECALL_MAX_L3', 2)),
            total_limit=int(os.getenv('RECALL_TOTAL_LIMIT', 10))
        )


@dataclass
class APIConfig:
    """API配置"""
    host: str = "0.0.0.0"
    port: int = 5000
    debug: bool = False
    
    @classmethod
    def from_env(cls):
        """从环境变量加载"""
        return cls(
            host=os.getenv('API_HOST', '0.0.0.0'),
            port=int(os.getenv('API_PORT', 5000)),
            debug=os.getenv('API_DEBUG', 'false').lower() == 'true'
        )


@dataclass
class Settings:
    """全局配置"""
    l1: L1Config = field(default_factory=L1Config)
    l2: L2Config = field(default_factory=L2Config)
    l3: L3Config = field(default_factory=L3Config)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    log: LogConfig = field(default_factory=LogConfig)
    recall: RecallConfig = field(default_factory=RecallConfig)
    api: APIConfig = field(default_factory=APIConfig)
    
    @classmethod
    def from_env(cls):
        """从环境变量加载所有配置"""
        return cls(
            l1=L1Config.from_env(),
            l2=L2Config.from_env(),
            l3=L3Config.from_env(),
            embedding=EmbeddingConfig.from_env(),
            log=LogConfig.from_env(),
            recall=RecallConfig.from_env(),
            api=APIConfig.from_env()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "l1": asdict(self.l1),
            "l2": asdict(self.l2),
            "l3": asdict(self.l3),
            "embedding": asdict(self.embedding),
            "log": asdict(self.log),
            "recall": asdict(self.recall),
            "api": asdict(self.api)
        }
    
    def reload_from_env(self):
        """从环境变量重新加载配置（热更新）"""
        self.l1 = L1Config.from_env()
        self.l2 = L2Config.from_env()
        self.l3 = L3Config.from_env()
        self.embedding = EmbeddingConfig.from_env()
        self.log = LogConfig.from_env()
        self.recall = RecallConfig.from_env()
        self.api = APIConfig.from_env()


# 全局配置单例
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """获取全局配置（支持环境变量）"""
    global _settings
    if _settings is None:
        _settings = Settings.from_env()
    return _settings


def reload_settings():
    """重新加载配置（热更新）"""
    global _settings
    if _settings is not None:
        _settings.reload_from_env()
    else:
        _settings = Settings.from_env()


def reset_settings():
    """重置为默认配置"""
    global _settings
    _settings = Settings()
