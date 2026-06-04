"""
记忆版本管理系统 - 支持历史数据回溯
基于第一性原理：版本快照、增量更新、历史可追溯
"""
import json
import os
import time
from typing import Dict, List, Optional, Any
from threading import Lock
from dataclasses import dataclass, asdict
from ..utils.logger import get_logger



@dataclass
class MemoryVersion:
    """记忆版本快照"""
    version_id: str
    item_id: str
    memory_level: str
    content: Dict
    timestamp: float
    action: str  # 'create', 'update', 'delete'
    operator: str  # 'system', 'user', 'auto'


class VersionManager:
    """记忆版本管理器"""
    
    def __init__(self, version_dir: str = "./data/versions"):
        self._logger = get_logger()
        self.version_dir = version_dir
        self._lock = Lock()
        self._versions: Dict[str, List[MemoryVersion]] = {}  # item_id -> versions
        self._max_versions_per_item = 10  # 每个item最多保留版本数
        
        os.makedirs(version_dir, exist_ok=True)
    
    def record_version(
        self,
        item_id: str,
        memory_level: str,
        content: Dict,
        action: str = 'update',
        operator: str = 'system'
    ) -> str:
        """记录版本快照"""
        with self._lock:
            version_id = f"v_{item_id}_{int(time.time() * 1000)}"
            
            version = MemoryVersion(
                version_id=version_id,
                item_id=item_id,
                memory_level=memory_level,
                content=content.copy(),
                timestamp=time.time(),
                action=action,
                operator=operator
            )
            
            if item_id not in self._versions:
                self._versions[item_id] = []
            
            self._versions[item_id].append(version)
            
            # 限制版本数量
            if len(self._versions[item_id]) > self._max_versions_per_item:
                self._versions[item_id] = self._versions[item_id][-self._max_versions_per_item:]
            
            self._save_to_disk(item_id)
            
            return version_id
    
    def get_versions(self, item_id: str, limit: int = None) -> List[Dict]:
        """获取历史版本"""
        with self._lock:
            if item_id not in self._versions:
                return []
            
            versions = self._versions[item_id]
            if limit:
                versions = versions[-limit:]
            
            return [asdict(v) for v in versions]
    
    def get_version(self, item_id: str, version_id: str) -> Optional[Dict]:
        """获取特定版本"""
        with self._lock:
            if item_id not in self._versions:
                return None
            
            for version in self._versions[item_id]:
                if version.version_id == version_id:
                    return asdict(version)
            
            return None
    
    def rollback_to_version(self, item_id: str, version_id: str) -> Optional[Dict]:
        """回滚到指定版本"""
        version = self.get_version(item_id, version_id)
        if version:
            # 记录回滚操作
            self.record_version(
                item_id=item_id,
                memory_level=version['memory_level'],
                content=version['content'],
                action='rollback',
                operator='user'
            )
            return version['content']
        return None
    
    def get_latest_version(self, item_id: str) -> Optional[Dict]:
        """获取最新版本"""
        versions = self.get_versions(item_id, limit=1)
        return versions[0] if versions else None
    
    def _save_to_disk(self, item_id: str) -> None:
        """保存到磁盘"""
        if item_id not in self._versions:
            return
        
        version_file = os.path.join(self.version_dir, f"{item_id}.json")
        versions_data = [asdict(v) for v in self._versions[item_id]]
        
        with open(version_file, 'w', encoding='utf-8') as f:
            json.dump(versions_data, f, ensure_ascii=False)
    
    def _load_from_disk(self, item_id: str) -> None:
        """从磁盘加载"""
        version_file = os.path.join(self.version_dir, f"{item_id}.json")
        
        if os.path.exists(version_file):
            try:
                with open(version_file, 'r', encoding='utf-8') as f:
                    versions_data = json.load(f)
                
                self._versions[item_id] = [
                    MemoryVersion(**v) for v in versions_data
                ]
            except Exception as e:
                logger.info(f"Load version error: {e}")


class MemoryCorrection:
    """记忆纠错器 - 人工修正入口"""
    
    def __init__(self, version_manager: VersionManager):
        self.version_manager = version_manager
        self._correction_queue: List[Dict] = []
    
    def submit_correction(
        self,
        item_id: str,
        new_content: Dict,
        reason: str,
        operator: str = 'user'
    ) -> str:
        """提交修正"""
        correction = {
            'item_id': item_id,
            'new_content': new_content,
            'reason': reason,
            'operator': operator,
            'timestamp': time.time(),
            'status': 'pending'
        }
        
        self._correction_queue.append(correction)
        
        version_id = self.version_manager.record_version(
            item_id=item_id,
            memory_level=new_content.get('memory_level', 'l2'),
            content=new_content,
            action='correction',
            operator=operator
        )
        
        return version_id
    
    def approve_correction(self, correction_id: int) -> bool:
        """批准修正"""
        if 0 <= correction_id < len(self._correction_queue):
            self._correction_queue[correction_id]['status'] = 'approved'
            return True
        return False
    
    def reject_correction(self, correction_id: int, reason: str) -> bool:
        """拒绝修正"""
        if 0 <= correction_id < len(self._correction_queue):
            self._correction_queue[correction_id]['status'] = 'rejected'
            self._correction_queue[correction_id]['reject_reason'] = reason
            return True
        return False
    
    def get_pending_corrections(self) -> List[Dict]:
        """获取待处理修正"""
        return [
            {**c, 'id': i}
            for i, c in enumerate(self._correction_queue)
            if c['status'] == 'pending'
        ]


# 全局单例
_version_manager = None
_memory_correction = None


def get_version_manager() -> VersionManager:
    global _version_manager
    if _version_manager is None:
        _version_manager = VersionManager()
    return _version_manager


def get_memory_correction() -> MemoryCorrection:
    global _memory_correction
    if _memory_correction is None:
        _memory_correction = MemoryCorrection(get_version_manager())
    return _memory_correction
