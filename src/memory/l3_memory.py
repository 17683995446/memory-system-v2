"""
L3 永久事实记忆 - 结构化存储
基于第一性原理：精准查询、逻辑推理、不可自动销毁、迭代更新
"""
import sqlite3
import os
import time
import json
from typing import Dict, List, Optional, Any
from threading import Lock


class Triple:
    """三元组：实体-属性-关系"""
    def __init__(
        self,
        entity: str,
        attribute: str,
        value: str,
        source: str = "system",
        confidence: float = 1.0,
        version: int = 1
    ):
        self.entity = entity
        self.attribute = attribute
        self.value = value
        self.source = source
        self.confidence = confidence
        self.version = version
        self.timestamp = time.time()
        self.triple_id = f"{entity}::{attribute}"
    
    def to_dict(self) -> Dict:
        return {
            "id": self.triple_id,
            "entity": self.entity,
            "attribute": self.attribute,
            "value": self.value,
            "source": self.source,
            "confidence": self.confidence,
            "version": self.version,
            "timestamp": self.timestamp
        }


class L3Memory:
    """L3事实记忆 - SQLite实现"""
    
    def __init__(self, db_file: str = "./data/l3_memory.db"):
        self._lock = Lock()
        self.db_file = db_file
        self._init_db()
    
    def _init_db(self) -> None:
        """初始化数据库"""
        os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS triples (
                    id TEXT PRIMARY KEY,
                    entity TEXT NOT NULL,
                    attribute TEXT NOT NULL,
                    value TEXT NOT NULL,
                    source TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    version INTEGER NOT NULL,
                    timestamp REAL NOT NULL
                )
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_entity ON triples (entity)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_attribute ON triples (attribute)
            ''')
            conn.commit()
    
    def add(self, entity: str, attribute: str, value: str, source: str = "system", confidence: float = 1.0) -> str:
        """添加或更新三元组"""
        with self._lock:
            triple_id = f"{entity}::{attribute}"
            
            # 检查是否存在
            existing = self._get_by_id(triple_id)
            
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                if existing:
                    # 更新，版本+1
                    new_version = existing["version"] + 1
                    cursor.execute('''
                        UPDATE triples 
                        SET value = ?, source = ?, confidence = ?, version = ?, timestamp = ?
                        WHERE id = ?
                    ''', (value, source, confidence, new_version, time.time(), triple_id))
                else:
                    # 新增
                    cursor.execute('''
                        INSERT INTO triples (id, entity, attribute, value, source, confidence, version, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (triple_id, entity, attribute, value, source, confidence, 1, time.time()))
                
                conn.commit()
            return triple_id
    
    def query_by_entity(self, entity: str) -> List[Dict]:
        """根据实体查询"""
        with self._lock:
            with sqlite3.connect(self.db_file) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM triples WHERE entity = ?', (entity,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
    
    def query_by_keyword(self, keyword: str) -> List[Dict]:
        """关键词精确匹配查询"""
        with self._lock:
            with sqlite3.connect(self.db_file) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM triples 
                    WHERE entity LIKE ? OR attribute LIKE ? OR value LIKE ?
                ''', (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
    
    def get(self, entity: str, attribute: str) -> Optional[Dict]:
        """获取特定三元组"""
        triple_id = f"{entity}::{attribute}"
        return self._get_by_id(triple_id)
    
    def _get_by_id(self, triple_id: str) -> Optional[Dict]:
        """根据ID获取"""
        with sqlite3.connect(self.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM triples WHERE id = ?', (triple_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def delete(self, entity: str, attribute: str) -> bool:
        """删除三元组（需要谨慎操作）"""
        triple_id = f"{entity}::{attribute}"
        with self._lock:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM triples WHERE id = ?', (triple_id,))
                conn.commit()
                return cursor.rowcount > 0
    
    def delete_by_key(self, key: str) -> bool:
        """根据key删除三元组（key匹配entity或value）"""
        with self._lock:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                # 尝试匹配entity或value
                cursor.execute('DELETE FROM triples WHERE entity = ? OR value = ?', (key, key))
                conn.commit()
                return cursor.rowcount > 0
    
    def size(self) -> int:
        """获取三元组总数"""
        with self._lock:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM triples')
                return cursor.fetchone()[0]
    
    def get_all(self) -> List[Dict]:
        """获取所有三元组"""
        with self._lock:
            with sqlite3.connect(self.db_file) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM triples')
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
    
    def clear(self) -> None:
        """清空所有事实"""
        with self._lock:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM triples')
                conn.commit()
