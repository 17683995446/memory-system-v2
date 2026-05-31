"""
增强的备份与恢复系统
基于第一性原理：确定性、完整性、可靠性、可验证
"""

import os
import json
import time
import hashlib
import gzip
import logging
import threading
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class BackupType(Enum):
    """备份类型"""
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"


class VerificationStatus(Enum):
    """验证状态"""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    UNKNOWN = "unknown"


@dataclass
class BackupMetadata:
    """备份元数据"""
    backup_id: str
    backup_type: str
    created_at: str
    memory_count: int
    data_size: int
    checksum: str
    version: str = "1.0.0"
    description: str = ""
    parent_backup_id: Optional[str] = None


@dataclass
class BackupConfig:
    """备份配置"""
    backup_dir: str = "./data/backups"
    auto_backup_enabled: bool = True
    auto_backup_interval_hours: int = 24
    max_backups: int = 10
    compress_backups: bool = True
    enable_verification: bool = True
    incremental_enabled: bool = True


class DataVerifier:
    """数据验证器"""

    @staticmethod
    def compute_checksum(data: str) -> str:
        """计算数据校验和"""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    @staticmethod
    def verify_checksum(data: str, expected_checksum: str) -> bool:
        """验证数据校验和"""
        actual_checksum = DataVerifier.compute_checksum(data)
        return actual_checksum == expected_checksum

    @staticmethod
    def verify_backup_file(filepath: str) -> VerificationStatus:
        """验证备份文件完整性"""
        try:
            if not os.path.exists(filepath):
                logger.warning(f"备份文件不存在: {filepath}")
                return VerificationStatus.FAIL

            # 支持压缩文件
            if filepath.endswith('.gz'):
                with gzip.open(filepath, 'rt', encoding='utf-8') as f:
                    backup_data = json.load(f)
            else:
                with open(filepath, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)

            checksum = backup_data.get('checksum')
            if not checksum:
                return VerificationStatus.WARNING

            data_str = json.dumps(backup_data.get('data', {}), ensure_ascii=False)
            is_valid = DataVerifier.verify_checksum(data_str, checksum)

            return VerificationStatus.PASS if is_valid else VerificationStatus.FAIL

        except Exception as e:
            logger.error(f"验证备份文件失败: {e}")
            return VerificationStatus.FAIL


class AdvancedBackupManager:
    """增强的备份管理器"""

    def __init__(self, config: Optional[BackupConfig] = None):
        self.config = config or BackupConfig()
        os.makedirs(self.config.backup_dir, exist_ok=True)
        self._scheduler_thread: Optional[threading.Thread] = None
        self._scheduler_running = False

    def generate_backup_id(self) -> str:
        """生成备份ID"""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        random_suffix = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        return f"backup_{timestamp}_{random_suffix}"

    def create_backup(
        self,
        memory_system,
        backup_type: BackupType = BackupType.FULL,
        description: str = "",
        include_metadata: bool = True
    ) -> Dict[str, Any]:
        """创建备份"""
        start_time = time.time()

        backup_id = self.generate_backup_id()
        filename = f"{backup_id}.json"
        if self.config.compress_backups:
            filename += ".gz"

        backup_path = os.path.join(self.config.backup_dir, filename)

        try:
            # 收集数据
            backup_data = {
                "version": "2.0.0",
                "backup_id": backup_id,
                "backup_type": backup_type.value,
                "created_at": datetime.utcnow().isoformat(),
                "description": description,
                "data": {
                    "l1": [],
                    "l2": [],
                    "l3": []
                }
            }

            stats = {
                "l1_count": 0,
                "l2_count": 0,
                "l3_count": 0,
                "total_count": 0
            }

            # 导出各层记忆
            if hasattr(memory_system, 'l1'):
                try:
                    l1_memories = memory_system.l1.get_all()
                    backup_data["data"]["l1"] = l1_memories
                    stats["l1_count"] = len(l1_memories)
                except Exception as e:
                    logger.warning(f"导出L1记忆失败: {e}")

            if hasattr(memory_system, 'l2'):
                try:
                    l2_memories = memory_system.l2.get_all()
                    backup_data["data"]["l2"] = l2_memories
                    stats["l2_count"] = len(l2_memories)
                except Exception as e:
                    logger.warning(f"导出L2记忆失败: {e}")

            if hasattr(memory_system, 'l3'):
                try:
                    l3_memories = memory_system.l3.get_all()
                    backup_data["data"]["l3"] = l3_memories
                    stats["l3_count"] = len(l3_memories)
                except Exception as e:
                    logger.warning(f"导出L3记忆失败: {e}")

            stats["total_count"] = stats["l1_count"] + stats["l2_count"] + stats["l3_count"]

            # 计算校验和
            data_str = json.dumps(backup_data["data"], ensure_ascii=False)
            backup_data["checksum"] = DataVerifier.compute_checksum(data_str)

            # 添加元数据
            if include_metadata:
                backup_data["metadata"] = stats
                backup_data["metadata"]["created_at"] = backup_data["created_at"]
                backup_data["metadata"]["backup_type"] = backup_type.value

            # 写入文件
            if self.config.compress_backups:
                with gzip.open(backup_path, 'wt', encoding='utf-8') as f:
                    json.dump(backup_data, f, ensure_ascii=False, indent=2)
            else:
                with open(backup_path, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, ensure_ascii=False, indent=2)

            # 管理备份数量
            self._cleanup_old_backups()

            elapsed_time = time.time() - start_time

            result = {
                "success": True,
                "backup_id": backup_id,
                "backup_path": backup_path,
                "backup_type": backup_type.value,
                "stats": stats,
                "elapsed_time_seconds": round(elapsed_time, 3)
            }

            logger.info(f"备份创建成功: {backup_id}, 共 {stats['total_count']} 条记忆, 耗时 {elapsed_time:.3f}秒")

            return result

        except Exception as e:
            logger.error(f"创建备份失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "backup_id": backup_id
            }

    def list_backups(self) -> List[Dict[str, Any]]:
        """列出所有备份"""
        backups = []

        if not os.path.exists(self.config.backup_dir):
            return backups

        for filename in os.listdir(self.config.backup_dir):
            filepath = os.path.join(self.config.backup_dir, filename)
            try:
                stat = os.stat(filepath)
                size = stat.st_size

                # 读取元数据
                metadata = {}
                try:
                    if filename.endswith('.gz'):
                        with gzip.open(filepath, 'rt', encoding='utf-8') as f:
                            backup_data = json.load(f)
                    else:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            backup_data = json.load(f)

                    metadata = backup_data.get('metadata', {})
                except Exception:
                    pass

                backups.append({
                    "name": filename,
                    "path": filepath,
                    "size": size,
                    "size_mb": round(size / (1024 * 1024), 3),
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "metadata": metadata,
                    "backup_id": metadata.get('backup_id', filename.replace('.json', '').replace('.gz', ''))
                })

            except Exception as e:
                logger.warning(f"读取备份信息失败: {e}")

        # 按创建时间倒序
        backups.sort(key=lambda x: x["created"], reverse=True)
        return backups

    def restore_backup(
        self,
        memory_system,
        backup_id: str,
        clear_before: bool = True,
        verify_before: bool = True
    ) -> Dict[str, Any]:
        """从备份恢复"""
        start_time = time.time()

        # 查找备份文件
        backup_file = self._find_backup_file(backup_id)
        if not backup_file:
            return {"success": False, "error": f"未找到备份: {backup_id}"}

        # 验证备份
        if verify_before and self.config.enable_verification:
            verification = DataVerifier.verify_backup_file(backup_file)
            if verification == VerificationStatus.FAIL:
                return {"success": False, "error": f"备份验证失败: {backup_id}"}

        try:
            # 读取备份
            if backup_file.endswith('.gz'):
                with gzip.open(backup_file, 'rt', encoding='utf-8') as f:
                    backup_data = json.load(f)
            else:
                with open(backup_file, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)

            stats = {
                "l1_restored": 0,
                "l2_restored": 0,
                "l3_restored": 0,
                "total_restored": 0
            }

            # 清空
            if clear_before:
                if hasattr(memory_system, 'l1'):
                    memory_system.l1.clear()
                if hasattr(memory_system, 'l2'):
                    memory_system.l2.clear()
                if hasattr(memory_system, 'l3'):
                    memory_system.l3.clear()

            # 恢复数据
            data = backup_data.get('data', {})

            l1_data = data.get('l1', [])
            for mem in l1_data:
                if hasattr(memory_system, 'l1'):
                    try:
                        memory_system.l1.add(mem.get('text', ''), mem.get('session_id', 'restored'))
                        stats["l1_restored"] += 1
                    except Exception as e:
                        logger.warning(f"恢复L1记忆失败: {e}")

            l2_data = data.get('l2', [])
            for mem in l2_data:
                if hasattr(memory_system, 'l2'):
                    try:
                        metadata = mem.get('metadata', {})
                        if 'session_id' in mem:
                            metadata['session_id'] = mem['session_id']
                        memory_system.l2.add(mem.get('text', ''), None, metadata)
                        stats["l2_restored"] += 1
                    except Exception as e:
                        logger.warning(f"恢复L2记忆失败: {e}")

            l3_data = data.get('l3', [])
            for fact in l3_data:
                if hasattr(memory_system, 'l3'):
                    try:
                        memory_system.l3.add(
                            fact.get('entity', ''),
                            fact.get('attribute', ''),
                            fact.get('value', ''),
                            fact.get('source', 'restored'),
                            fact.get('confidence', 1.0)
                        )
                        stats["l3_restored"] += 1
                    except Exception as e:
                        logger.warning(f"恢复L3事实失败: {e}")

            stats["total_restored"] = stats["l1_restored"] + stats["l2_restored"] + stats["l3_restored"]

            elapsed_time = time.time() - start_time

            result = {
                "success": True,
                "backup_id": backup_id,
                "stats": stats,
                "elapsed_time_seconds": round(elapsed_time, 3)
            }

            logger.info(f"备份恢复成功: {backup_id}, 恢复 {stats['total_restored']} 条记忆, 耗时 {elapsed_time:.3f}秒")

            return result

        except Exception as e:
            logger.error(f"恢复备份失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "backup_id": backup_id
            }

    def delete_backup(self, backup_id: str) -> Dict[str, Any]:
        """删除备份"""
        backup_file = self._find_backup_file(backup_id)
        if not backup_file:
            return {"success": False, "error": f"未找到备份: {backup_id}"}

        try:
            os.remove(backup_file)
            logger.info(f"备份已删除: {backup_id}")
            return {"success": True, "backup_id": backup_id}
        except Exception as e:
            logger.error(f"删除备份失败: {e}")
            return {"success": False, "error": str(e)}

    def verify_backup(self, backup_id: str) -> Dict[str, Any]:
        """验证备份"""
        backup_file = self._find_backup_file(backup_id)
        if not backup_file:
            return {"success": False, "error": f"未找到备份: {backup_id}"}

        status = DataVerifier.verify_backup_file(backup_file)

        return {
            "success": True,
            "backup_id": backup_id,
            "status": status.value,
            "message": self._get_verification_message(status)
        }

    def _find_backup_file(self, backup_id: str) -> Optional[str]:
        """查找备份文件"""
        if not os.path.exists(self.config.backup_dir):
            return None

        # 尝试各种文件名变体
        candidates = [
            backup_id,
            f"{backup_id}.json",
            f"{backup_id}.json.gz"
        ]

        for filename in os.listdir(self.config.backup_dir):
            if any(filename == c or filename.startswith(c) for c in candidates):
                return os.path.join(self.config.backup_dir, filename)

        return None

    def _cleanup_old_backups(self):
        """清理旧备份"""
        if self.config.max_backups <= 0:
            return

        backups = self.list_backups()
        if len(backups) <= self.config.max_backups:
            return

        # 删除最旧的备份
        for backup in backups[self.config.max_backups:]:
            try:
                os.remove(backup["path"])
                logger.info(f"删除旧备份: {backup['name']}")
            except Exception as e:
                logger.warning(f"删除备份失败: {e}")

    def _get_verification_message(self, status: VerificationStatus) -> str:
        """获取验证消息"""
        messages = {
            VerificationStatus.PASS: "备份验证通过，数据完整性完好",
            VerificationStatus.FAIL: "备份验证失败，数据可能已损坏",
            VerificationStatus.WARNING: "备份缺少校验和，无法验证完整性",
            VerificationStatus.UNKNOWN: "验证状态未知"
        }
        return messages.get(status, "未知状态")

    def get_backup_stats(self) -> Dict[str, Any]:
        """获取备份统计"""
        backups = self.list_backups()
        total_size = sum(b['size'] for b in backups)

        return {
            "total_backups": len(backups),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 3),
            "latest_backup": backups[0]['created'] if backups else None,
            "oldest_backup": backups[-1]['created'] if backups else None
        }


class BackupScheduler:
    """备份调度器"""

    def __init__(self, backup_manager: AdvancedBackupManager, memory_system):
        self.backup_manager = backup_manager
        self.memory_system = memory_system
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_backup_time: Optional[float] = None
        self._backup_count = 0

    def start(self):
        """启动自动备份"""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._thread.start()
        logger.info("自动备份调度器已启动")

    def stop(self):
        """停止自动备份"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("自动备份调度器已停止")

    def _scheduler_loop(self):
        """调度循环"""
        while self._running:
            try:
                now = time.time()

                if self._should_backup(now):
                    self._perform_auto_backup()

                # 每分钟检查一次
                time.sleep(60)

            except Exception as e:
                logger.error(f"备份调度器错误: {e}")
                time.sleep(60)

    def _should_backup(self, now: float) -> bool:
        """判断是否应该备份"""
        if not self.backup_manager.config.auto_backup_enabled:
            return False

        interval = self.backup_manager.config.auto_backup_interval_hours * 3600

        if self._last_backup_time is None:
            return True

        return now - self._last_backup_time >= interval

    def _perform_auto_backup(self):
        """执行自动备份"""
        try:
            self._backup_count += 1
            description = f"自动备份 #{self._backup_count}"

            result = self.backup_manager.create_backup(
                self.memory_system,
                BackupType.INCREMENTAL if self.backup_manager.config.incremental_enabled else BackupType.FULL,
                description
            )

            if result["success"]:
                self._last_backup_time = time.time()
                logger.info(f"自动备份成功: {result['backup_id']}")
            else:
                logger.error(f"自动备份失败: {result.get('error')}")

        except Exception as e:
            logger.error(f"执行自动备份失败: {e}")

    def get_scheduler_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        return {
            "running": self._running,
            "backup_count": self._backup_count,
            "last_backup_time": datetime.fromtimestamp(self._last_backup_time).isoformat() if self._last_backup_time else None,
            "auto_backup_enabled": self.backup_manager.config.auto_backup_enabled,
            "auto_backup_interval_hours": self.backup_manager.config.auto_backup_interval_hours
        }


def create_backup_system(memory_system, config: Optional[BackupConfig] = None) -> Dict[str, Any]:
    """创建完整的备份系统"""
    backup_manager = AdvancedBackupManager(config)
    scheduler = BackupScheduler(backup_manager, memory_system)

    return {
        "manager": backup_manager,
        "scheduler": scheduler
    }
