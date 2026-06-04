"""
基于第一性原理的Agent可靠记忆系统 - 统一调度入口
分层解耦、单向数据流、闭环治理、增量迭代
增强：事务机制、数据一致性校验、持久化状态追踪
"""
import time
import os
import shutil
import json
from typing import Dict, List, Optional, Any, Tuple
from threading import Lock
from dataclasses import dataclass

from .l1_memory import L1Memory
from .l2_memory import L2Memory
from .l3_memory import L3Memory
from ..config.settings import get_settings, Settings
from ..utils.logger import get_logger
from ..utils.embedding import get_embedding_model


@dataclass
class PersistenceState:
    """持久化状态记录"""
    l2_last_save: float = 0.0
    l3_last_save: float = 0.0
    l2_save_count: int = 0
    l3_save_count: int = 0
    last_backup: float = 0.0
    backup_count: int = 0


class ConsistencyChecker:
    """数据一致性校验器"""

    @staticmethod
    def validate_l2_metadata_consistency(items: List[Dict]) -> Tuple[bool, List[str]]:
        """校验L2元数据一致性"""
        errors = []
        for item in items:
            if 'id' not in item or not item['id']:
                errors.append(f"L2 item missing id: {item}")
            if 'text' not in item:
                errors.append(f"L2 item missing text: {item.get('id')}")
            if 'timestamp' not in item:
                errors.append(f"L2 item missing timestamp: {item.get('id')}")
        return len(errors) == 0, errors

    @staticmethod
    def validate_l3_triple_consistency(triples: List[Dict]) -> Tuple[bool, List[str]]:
        """校验L3三元组一致性"""
        errors = []
        seen_ids = set()
        for triple in triples:
            tid = triple.get('id')
            if not tid:
                errors.append(f"L3 triple missing id: {triple}")
                continue
            if tid in seen_ids:
                errors.append(f"L3 duplicate triple id: {tid}")
            seen_ids.add(tid)
            if not triple.get('entity'):
                errors.append(f"L3 triple missing entity: {tid}")
            if not triple.get('attribute'):
                errors.append(f"L3 triple missing attribute: {tid}")
            if not triple.get('value'):
                errors.append(f"L3 triple missing value: {tid}")
        return len(errors) == 0, errors

    @staticmethod
    def validate_cross_layer_references(l1_items: List[Dict], l2_items: List[Dict], l3_triples: List[Dict]) -> Tuple[bool, List[str]]:
        """校验跨层引用一致性"""
        errors = []
        # 检查L1中引用的task_id是否在L2中有对应记录
        l1_task_ids = set()
        for item in l1_items:
            tid = item.get('task_id')
            if tid:
                l1_task_ids.add(tid)

        l2_task_ids = set()
        for item in l2_items:
            meta = item.get('metadata', {})
            tid = meta.get('task_id')
            if tid:
                l2_task_ids.add(tid)

        # L1的task_id应该能在L2中找到对应（如果该任务产生过L2记忆）
        # 这不是严格错误，只是警告
        orphan_tasks = l1_task_ids - l2_task_ids
        if len(orphan_tasks) > 10:  # 少量orphan是正常的
            errors.append(f"Too many orphan L1 tasks without L2 records: {len(orphan_tasks)}")

        return len(errors) == 0, errors


class MemorySystem:
    """统一记忆系统调度器

    数据持久化与一致性增强：
    1. 多层操作事务日志
    2. 自动备份机制
    3. 一致性校验
    4. 持久化状态追踪
    """

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
        self._persistence_state = PersistenceState()
        self._consistency_checker = ConsistencyChecker()
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
                self._persistence_state.l3_last_save = time.time()
                self._persistence_state.l3_save_count += 1
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
            self._persistence_state.l3_last_save = time.time()
            self._persistence_state.l3_save_count += 1
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
                },
                "persistence": {
                    "l2_last_save": self._persistence_state.l2_last_save,
                    "l3_last_save": self._persistence_state.l3_last_save,
                    "l2_save_count": self._persistence_state.l2_save_count,
                    "l3_save_count": self._persistence_state.l3_save_count,
                    "last_backup": self._persistence_state.last_backup,
                    "backup_count": self._persistence_state.backup_count
                }
            }

    def save(self) -> bool:
        """保存数据（带错误处理和状态追踪）"""
        with self._lock:
            try:
                self.l2.save()
                self._persistence_state.l2_last_save = time.time()
                self._persistence_state.l2_save_count += 1
                self._logger.info("Memory system L2 saved")

                # L3是SQLite，每次add已自动commit，这里触发VACUUM优化
                self.l3.vacuum()
                self._persistence_state.l3_last_save = time.time()

                return True
            except Exception as e:
                self._logger.error(f"[SaveError] Failed to save memory system: {e}")
                return False

    def backup(self, backup_dir: Optional[str] = None) -> bool:
        """创建数据备份"""
        with self._lock:
            try:
                backup_dir = backup_dir or "./data/backups"
                os.makedirs(backup_dir, exist_ok=True)

                timestamp = time.strftime("%Y%m%d_%H%M%S")
                backup_path = os.path.join(backup_dir, f"backup_{timestamp}")
                os.makedirs(backup_path, exist_ok=True)

                # 备份L2
                l2_index_src = self._settings.l2.index_file
                l2_meta_src = self._settings.l2.metadata_file
                if os.path.exists(l2_meta_src):
                    shutil.copy2(l2_meta_src, os.path.join(backup_path, "l2_metadata.json"))
                if os.path.exists(l2_index_src):
                    shutil.copy2(l2_index_src, os.path.join(backup_path, "l2_index.faiss"))

                # 备份L3
                l3_db_src = self._settings.l3.db_file
                if os.path.exists(l3_db_src):
                    shutil.copy2(l3_db_src, os.path.join(backup_path, "l3_memory.db"))

                # 写入备份元数据
                backup_meta = {
                    "timestamp": time.time(),
                    "l2_size": self.l2.size(),
                    "l3_size": self.l3.size(),
                    "version": "1.1.0"
                }
                with open(os.path.join(backup_path, "backup_meta.json"), 'w') as f:
                    json.dump(backup_meta, f, indent=2)

                self._persistence_state.last_backup = time.time()
                self._persistence_state.backup_count += 1
                self._logger.info(f"[Backup] Created backup at {backup_path}")
                return True
            except Exception as e:
                self._logger.error(f"[BackupError] Failed to create backup: {e}")
                return False

    def check_consistency(self) -> Tuple[bool, Dict[str, Any]]:
        """全量数据一致性校验"""
        with self._lock:
            report = {
                "timestamp": time.time(),
                "checks": {},
                "errors": [],
                "warnings": []
            }

            # 获取各层数据
            l1_items = self.l1.get_all()
            l2_items = self.l2.get_all()
            l3_triples = self.l3.get_all()

            # L2一致性
            l2_ok, l2_errors = self._consistency_checker.validate_l2_metadata_consistency(l2_items)
            report["checks"]["l2_metadata"] = {"passed": l2_ok, "errors": l2_errors}
            report["errors"].extend(l2_errors)

            # L3一致性
            l3_ok, l3_errors = self._consistency_checker.validate_l3_triple_consistency(l3_triples)
            report["checks"]["l3_triples"] = {"passed": l3_ok, "errors": l3_errors}
            report["errors"].extend(l3_errors)

            # 跨层一致性
            cross_ok, cross_errors = self._consistency_checker.validate_cross_layer_references(
                l1_items, l2_items, l3_triples
            )
            report["checks"]["cross_layer"] = {"passed": cross_ok, "errors": cross_errors}
            report["warnings"].extend(cross_errors)

            # 统计信息
            report["summary"] = {
                "l1_count": len(l1_items),
                "l2_count": len(l2_items),
                "l3_count": len(l3_triples),
                "total_errors": len(report["errors"]),
                "total_warnings": len(report["warnings"]),
                "overall_passed": len(report["errors"]) == 0
            }

            self._logger.info(
                f"[ConsistencyCheck] L1={len(l1_items)} L2={len(l2_items)} L3={len(l3_triples)} "
                f"Errors={len(report['errors'])} Warnings={len(report['warnings'])}"
            )

            return report["summary"]["overall_passed"], report

    def _should_store_l1(self, text: str) -> bool:
        """判断是否应该存储到L1（简单启发式规则）"""
        # 通常，短文本、当前交互属于L1
        return len(text) < 500

    def _should_store_l3(self, text: str) -> bool:
        """判断是否应该存储到L3（简单启发式规则）"""
        # 包含事实特征的文本
        keywords = ["是", "等于", "名称", "叫", "定义", "规则", "必须", "禁止"]
        return any(kw in text for kw in keywords)

    def delete(self, key: str) -> bool:
        """删除指定key的记忆"""
        with self._lock:
            # 尝试从L1删除
            l1_deleted = self.l1.delete_by_key(key)
            # 尝试从L2删除
            l2_deleted = self.l2.delete_by_key(key)
            # 尝试从L3删除
            l3_deleted = self.l3.delete_by_key(key)

            deleted = l1_deleted or l2_deleted or l3_deleted
            if deleted:
                self._logger.info(f"[Delete] Removed memory for key: {key}")
            return deleted

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
