"""
基于第一性原理的Agent可靠记忆系统 - 统一调度入口
分层解耦、单向数据流、闭环治理、增量迭代
"""
import time
from typing import Dict, List, Optional, Any
from threading import Lock

from .l1_memory import L1Memory
from .l2_memory import L2Memory
from .l3_memory import L3Memory
from ..config.settings import get_settings, Settings
from ..utils.logger import get_logger
from ..utils.embedding import get_embedding_model


class MemorySystem:
    """统一记忆系统调度器"""
    
    def __init__(self, settings: Optional[Settings] = None):
        self._settings = settings or get_settings()
        self._logger = get_logger()
        self._embedding = get_embedding_model()
        
        # 初始化各层记忆
        self.l1 = L1Memory(
            max_items_per_task=self._settings.l1.max_items_per_task,
            max_tasks=self._settings.l1.max_tasks
        )
        self.l2 = L2Memory(
            dimension=self._settings.l2.dimension,
            index_file=self._settings.l2.index_file,
            metadata_file=self._settings.l2.metadata_file
        )
        self.l3 = L3Memory(
            db_file=self._settings.l3.db_file
        )
        
        self._lock = Lock()
        self._logger.info("MemorySystem initialized")
    
    def add(self, text: str, task_id: str, memory_level: Optional[str] = None) -> str:
        """
        添加记忆
        基于第一性原理：智能分发规则（硬编码，不依赖模型）
        
        Returns:
            唯一记忆ID
        """
        with self._lock:
            if memory_level == "l1" or (not memory_level and self._should_store_l1(text)):
                # L1: 单任务临时交互
                mem_id = f"l1_{int(time.time() * 1000000)}"
                self.l1.add(text, task_id)
                self._logger.info(f"[L1] Added memory for task {task_id}: {mem_id}")
                return mem_id
            
            elif memory_level == "l3" or (not memory_level and self._should_store_l3(text)):
                # L3: 结构化事实（简化版，实际需要解析三元组）
                # 这里简单处理：检测是否包含事实特征
                fact_id = f"fact_{int(time.time() * 1000000)}"
                self.l3.add(fact_id, "content", text)
                self._logger.info(f"[L3] Added fact memory: {fact_id}")
                return fact_id
            
            else:
                # 默认L2: 情景经验
                try:
                    embedding = self._embedding.encode(text)
                except Exception:
                    embedding = None
                item_id = self.l2.add(text, embedding, {"task_id": task_id})
                self._logger.info(f"[L2] Added experience memory: {item_id}")
                return item_id
    
    def recall(
        self,
        query: str,
        task_id: str,
        limit: Optional[int] = None
    ) -> Dict[str, List[Dict]]:
        """
        智能召回
        基于第一性原理：多维度确定性召回策略
        """
        with self._lock:
            limit = limit or self._settings.recall.total_limit
            results = {
                "l1": [],
                "l2": [],
                "l3": []
            }
            
            # L1: 当前任务上下文
            l1_results = self.l1.get(task_id, limit=self._settings.recall.max_l1_items)
            results["l1"] = l1_results
            self._logger.info(f"[Recall] L1: {len(l1_results)} items")
            
            # L2: 语义检索
            try:
                query_embedding = self._embedding.encode(query)
            except Exception:
                query_embedding = None
            l2_results = self.l2.search(
                query_embedding,
                top_k=self._settings.recall.max_l2_items,
                threshold=self._settings.l2.similarity_threshold
            )
            results["l2"] = l2_results
            self._logger.info(f"[Recall] L2: {len(l2_results)} items")
            
            # L3: 关键词精确匹配
            l3_results = self.l3.query_by_keyword(query)
            l3_results = l3_results[:self._settings.recall.max_l3_items]
            results["l3"] = l3_results
            self._logger.info(f"[Recall] L3: {len(l3_results)} items")
            
            return results
    
    def end_task(self, task_id: str) -> None:
        """任务结束，自动清理L1"""
        with self._lock:
            self.l1.clear(task_id)
            self._logger.info(f"[L1] Cleared memory for task {task_id}")
    
    def add_fact(self, entity: str, attribute: str, value: str, source: str = "system") -> str:
        """直接添加事实到L3"""
        with self._lock:
            triple_id = self.l3.add(entity, attribute, value, source)
            self._logger.info(f"[L3] Added fact: {triple_id}")
            return triple_id
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        with self._lock:
            return {
                "l1": {
                    "size": self.l1.size(),
                    "task_count": self.l1.task_count()
                },
                "l2": {
                    "size": self.l2.size()
                },
                "l3": {
                    "size": self.l3.size()
                }
            }
    
    def save(self) -> None:
        """保存数据"""
        with self._lock:
            self.l2.save()
            self._logger.info("Memory system saved")
    
    def _should_store_l1(self, text: str) -> bool:
        """判断是否应该存储到L1（简单启发式规则）"""
        # 通常，短文本、当前交互属于L1
        return len(text) < 500
    
    def _should_store_l3(self, text: str) -> bool:
        """判断是否应该存储到L3（简单启发式规则）"""
        # 包含事实特征的文本
        keywords = ["是", "等于", "名称", "叫", "定义", "规则", "必须", "禁止"]
        return any(kw in text for kw in keywords)
    
    def cleanup(self) -> None:
        """清理过期数据"""
        with self._lock:
            deleted = self.l2.cleanup_old(self._settings.l2.cleanup_days)
            self._logger.info(f"Cleaned up {deleted} old L2 items")


# 全局单例
_memory_system: Optional[MemorySystem] = None


def get_memory_system() -> MemorySystem:
    """获取记忆系统单例"""
    global _memory_system
    if _memory_system is None:
        _memory_system = MemorySystem()
    return _memory_system
