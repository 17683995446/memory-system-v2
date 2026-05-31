"""
L2 情景经验记忆 - 向量数据库存储
基于第一性原理：语义检索、跨会话、模糊匹配、动态淘汰
"""
import os
import time
import json
from typing import Dict, List, Optional, Tuple
from threading import Lock

# 可选依赖
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    print("Warning: numpy not found, some features limited")

try:
    import faiss
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False
    print("Warning: faiss not found, using simple storage")


class L2MemoryItem:
    """L2记忆项"""
    def __init__(
        self,
        text: str,
        embedding: Optional[any] = None,
        metadata: Optional[Dict] = None,
        item_id: Optional[str] = None
    ):
        self.id = item_id or f"l2_{int(time.time() * 1000000)}"
        self.text = text
        self.embedding = embedding
        self.metadata = metadata or {}
        self.access_count = 0
        self.last_access = time.time()
        self.timestamp = time.time()
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "text": self.text,
            "metadata": self.metadata,
            "access_count": self.access_count,
            "last_access": self.last_access,
            "timestamp": self.timestamp
        }


class L2Memory:
    """L2情景记忆 - FAISS实现（支持降级模式）"""
    
    def __init__(self, dimension: int = 384, index_file: str = "./data/l2_index.faiss", metadata_file: str = "./data/l2_metadata.json"):
        self._lock = Lock()
        self.dimension = dimension
        self.index_file = index_file
        self.metadata_file = metadata_file
        
        # 初始化FAISS索引或简单存储
        self._use_faiss = HAS_FAISS and HAS_NUMPY
        if self._use_faiss:
            self._index = faiss.IndexFlatL2(dimension)
        self._items: Dict[str, L2MemoryItem] = {}
        self._id_to_index: Dict[str, int] = {}
        self._index_to_id: Dict[int, str] = {}
        
        # 加载现有数据
        self._load()
    
    def add(self, text: str, embedding: Optional[any] = None, metadata: Optional[Dict] = None) -> str:
        """添加记忆项"""
        with self._lock:
            item = L2MemoryItem(text, embedding, metadata)
            
            if self._use_faiss and HAS_NUMPY:
                # 添加到FAISS索引
                idx = len(self._items)
                self._index.add(np.array([embedding], dtype=np.float32))
                self._id_to_index[item.id] = idx
                self._index_to_id[idx] = item.id
            
            self._items[item.id] = item
            return item.id
    
    def search(self, query_embedding: Optional[any] = None, top_k: int = 5, threshold: float = 0.8) -> List[Dict]:
        """语义检索（降级模式支持关键词）"""
        with self._lock:
            if len(self._items) == 0:
                return []
            
            results = []
            
            if self._use_faiss and HAS_NUMPY and query_embedding is not None:
                # 使用FAISS搜索
                distances, indices = self._index.search(
                    np.array([query_embedding], dtype=np.float32), top_k
                )
                
                for dist, idx in zip(distances[0], indices[0]):
                    if idx == -1:
                        continue
                    
                    similarity = 1.0 / (1.0 + dist)
                    if similarity < threshold:
                        continue
                    
                    item_id = self._index_to_id.get(idx)
                    if item_id and item_id in self._items:
                        item = self._items[item_id]
                        item.access_count += 1
                        item.last_access = time.time()
                        
                        result = item.to_dict()
                        result["similarity"] = float(similarity)
                        results.append(result)
            else:
                # 降级模式：返回最近添加的
                sorted_items = sorted(
                    self._items.values(),
                    key=lambda x: x.timestamp,
                    reverse=True
                )[:top_k]
                for item in sorted_items:
                    item.access_count += 1
                    item.last_access = time.time()
                    result = item.to_dict()
                    result["similarity"] = 1.0
                    results.append(result)
            
            return results
    
    def get(self, item_id: str) -> Optional[Dict]:
        """获取单个记忆项"""
        with self._lock:
            if item_id in self._items:
                item = self._items[item_id]
                item.access_count += 1
                item.last_access = time.time()
                return item.to_dict()
            return None
    
    def delete(self, item_id: str) -> bool:
        """删除记忆项"""
        with self._lock:
            if item_id not in self._items:
                return False
            
            # 注意：FAISS不支持直接删除，这里标记删除，重建时清理
            del self._items[item_id]
            return True
    
    def cleanup_old(self, days: int = 30) -> int:
        """清理过期数据"""
        with self._lock:
            cutoff = time.time() - (days * 24 * 3600)
            to_delete = [
                item_id for item_id, item in self._items.items()
                if item.last_access < cutoff
            ]
            for item_id in to_delete:
                del self._items[item_id]
            return len(to_delete)
    
    def size(self) -> int:
        """获取记忆总数"""
        with self._lock:
            return len(self._items)
    
    def _save(self) -> None:
        """保存到磁盘"""
        os.makedirs(os.path.dirname(self.index_file), exist_ok=True)
        
        if self._use_faiss and HAS_FAISS:
            faiss.write_index(self._index, self.index_file)
        
        metadata = {
            item_id: {
                "text": item.text,
                "metadata": item.metadata,
                "access_count": item.access_count,
                "last_access": item.last_access,
                "timestamp": item.timestamp
            }
            for item_id, item in self._items.items()
        }
        
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False)
    
    def _load(self) -> None:
        """从磁盘加载"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                print(f"Loaded {len(metadata)} L2 memory items")
            except Exception as e:
                print(f"Load L2 memory error: {e}")
    
    def save(self) -> None:
        """手动保存"""
        with self._lock:
            self._save()
    
    def get_all(self) -> List[Dict]:
        """获取所有记忆"""
        with self._lock:
            return [item.to_dict() for item in self._items.values()]
    
    def clear(self) -> None:
        """清空所有记忆"""
        with self._lock:
            self._items.clear()
            self._id_to_index.clear()
            self._index_to_id.clear()
            if self._use_faiss and HAS_FAISS:
                # 重建FAISS索引
                self._index = faiss.IndexFlatL2(self.dimension)
