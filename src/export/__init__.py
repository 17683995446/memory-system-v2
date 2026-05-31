"""
记忆导出与分享功能模块
基于第一性原理：确定性、简洁性、可扩展性
"""

import json
import os
import time
import uuid
from typing import Dict, List, Optional, Any, IO
from collections import defaultdict


class MemoryExporter:
    """记忆导出类"""

    @staticmethod
    def export_to_json(
        memories: List[Dict[str, Any]],
        file_path: Optional[str] = None,
        include_metadata: bool = True
    ) -> str:
        """导出为JSON格式"""
        export_data = {
            "version": "1.0",
            "export_time": time.time(),
            "export_time_str": time.strftime("%Y-%m-%d %H:%M:%S"),
            "count": len(memories),
            "memories": memories
        }

        if not include_metadata:
            export_data = {
                "version": "1.0",
                "count": len(memories),
                "memories": [
                    {k: v for k, v in m.items() if k not in ['created_at', 'updated_at', 'access_count']}
                    for m in memories
                ]
            }

        if file_path:
            os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else '.', exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            return file_path
        else:
            return json.dumps(export_data, ensure_ascii=False, indent=2)

    @staticmethod
    def export_to_text(
        memories: List[Dict[str, Any]],
        file_path: Optional[str] = None
    ) -> str:
        """导出为文本格式"""
        lines = []
        for idx, mem in enumerate(memories, 1):
            lines.append(f"{'='*60}")
            lines.append(f"记忆 #{idx}")
            lines.append(f"{'='*60}")
            if 'memory_id' in mem:
                lines.append(f"ID: {mem['memory_id']}")
            if 'memory_level' in mem:
                lines.append(f"层级: {mem['memory_level']}")
            if 'created_at' in mem:
                lines.append(f"创建时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mem['created_at']))}")
            lines.append("")
            if 'content' in mem:
                lines.append(mem['content'])
            elif 'text' in mem:
                lines.append(mem['text'])
            lines.append("")
            lines.append("")

        result = '\n'.join(lines)

        if file_path:
            os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else '.', exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(result)
            return file_path
        else:
            return result

    @staticmethod
    def export_to_markdown(
        memories: List[Dict[str, Any]],
        file_path: Optional[str] = None
    ) -> str:
        """导出为Markdown格式"""
        lines = []
        lines.append("# 记忆导出")
        lines.append(f"导出时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"记忆数量: {len(memories)}")
        lines.append("")

        for idx, mem in enumerate(memories, 1):
            lines.append(f"## 记忆 {idx}")
            metadata = []
            if 'memory_id' in mem:
                metadata.append(f"- **ID**: {mem['memory_id']}")
            if 'memory_level' in mem:
                metadata.append(f"- **层级**: {mem['memory_level']}")
            if 'created_at' in mem:
                metadata.append(f"- **创建时间**: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mem['created_at']))}")
            if metadata:
                lines.extend(metadata)
                lines.append("")
            if 'content' in mem:
                lines.append(mem['content'])
            elif 'text' in mem:
                lines.append(mem['text'])
            lines.append("")
            lines.append("---")
            lines.append("")

        result = '\n'.join(lines)

        if file_path:
            os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else '.', exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(result)
            return file_path
        else:
            return result

    @staticmethod
    def export_to_csv(
        memories: List[Dict[str, Any]],
        file_path: Optional[str] = None
    ) -> str:
        """导出为CSV格式"""
        import csv
        from io import StringIO

        if not memories:
            return ""

        # 提取所有可能的字段
        fields = set()
        for mem in memories:
            fields.update(mem.keys())
        fields = sorted(list(fields))

        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()

        for mem in memories:
            # 处理可能缺失的字段
            row = {}
            for field in fields:
                value = mem.get(field, '')
                if isinstance(value, (list, dict)):
                    value = json.dumps(value, ensure_ascii=False)
                row[field] = value
            writer.writerow(row)

        result = output.getvalue()

        if file_path:
            os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else '.', exist_ok=True)
            with open(file_path, 'w', encoding='utf-8', newline='') as f:
                f.write(result)
            return file_path
        else:
            return result


class MemorySharer:
    """记忆分享类"""

    def __init__(self, storage_path: str = "./data/shares"):
        self.storage_path = storage_path
        os.makedirs(self.storage_path, exist_ok=True)

    def create_share(
        self,
        memory_ids: List[str],
        memories: List[Dict[str, Any]],
        share_type: str = "read",
        expires_at: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """创建分享链接"""
        share_id = str(uuid.uuid4())
        share_data = {
            "share_id": share_id,
            "memory_ids": memory_ids,
            "memories": memories,
            "share_type": share_type,
            "created_at": time.time(),
            "expires_at": expires_at,
            "access_count": 0,
            "metadata": metadata or {}
        }
        share_file = os.path.join(self.storage_path, f"{share_id}.json")
        with open(share_file, 'w', encoding='utf-8') as f:
            json.dump(share_data, f, ensure_ascii=False, indent=2)
        return share_id

    def get_share(self, share_id: str) -> Optional[Dict[str, Any]]:
        """获取分享内容"""
        share_file = os.path.join(self.storage_path, f"{share_id}.json")
        if not os.path.exists(share_file):
            return None

        with open(share_file, 'r', encoding='utf-8') as f:
            share_data = json.load(f)

        # 检查是否过期
        if share_data.get('expires_at') and time.time() > share_data['expires_at']:
            return None

        # 更新访问计数
        share_data['access_count'] = share_data.get('access_count', 0) + 1
        with open(share_file, 'w', encoding='utf-8') as f:
            json.dump(share_data, f, ensure_ascii=False, indent=2)

        return share_data

    def delete_share(self, share_id: str) -> bool:
        """删除分享"""
        share_file = os.path.join(self.storage_path, f"{share_id}.json")
        if os.path.exists(share_file):
            os.remove(share_file)
            return True
        return False

    def list_shares(self) -> List[Dict[str, Any]]:
        """列出所有分享"""
        shares = []
        for filename in os.listdir(self.storage_path):
            if filename.endswith('.json'):
                share_file = os.path.join(self.storage_path, filename)
                try:
                    with open(share_file, 'r', encoding='utf-8') as f:
                        share_data = json.load(f)
                        shares.append({
                            "share_id": share_data.get('share_id'),
                            "memory_count": len(share_data.get('memories', [])),
                            "share_type": share_data.get('share_type'),
                            "created_at": share_data.get('created_at'),
                            "expires_at": share_data.get('expires_at'),
                            "access_count": share_data.get('access_count', 0)
                        })
                except Exception:
                    continue
        return shares


class EnhancedMemoryWithExport:
    """
    增强的记忆系统（带导出与分享功能）
    装饰器模式实现
    """

    def __init__(self, memory_system):
        self.memory_system = memory_system
        self.exporter = MemoryExporter()
        self.sharer = MemorySharer()

    def _collect_memories(self) -> List[Dict[str, Any]]:
        """收集所有记忆"""
        memories = []

        # 获取 L1 记忆
        if hasattr(self.memory_system, 'l1') and hasattr(self.memory_system.l1, 'get_all'):
            l1_memories = self.memory_system.l1.get_all()
            memories.extend([
                {
                    'memory_id': f"L1-{i}",
                    'content': getattr(m, 'text', ''),
                    'memory_level': 'L1',
                    'created_at': time.time()
                } for i, m in enumerate(l1_memories)
            ])

        # 获取 L2 记忆
        if hasattr(self.memory_system, 'l2') and hasattr(self.memory_system.l2, 'get_all'):
            l2_memories = self.memory_system.l2.get_all()
            memories.extend([
                {
                    'memory_id': f"L2-{i}",
                    'content': getattr(m, 'text', ''),
                    'memory_level': 'L2',
                    'created_at': time.time()
                } for i, m in enumerate(l2_memories)
            ])

        # 获取 L3 记忆
        if hasattr(self.memory_system, 'l3') and hasattr(self.memory_system.l3, 'get_all'):
            l3_memories = self.memory_system.l3.get_all()
            memories.extend([
                {
                    'memory_id': f"L3-{i}",
                    'content': getattr(m, 'text', ''),
                    'memory_level': 'L3',
                    'created_at': time.time()
                } for i, m in enumerate(l3_memories)
            ])

        return memories

    def export_memories(
        self,
        export_format: str = "json",
        file_path: Optional[str] = None,
        include_metadata: bool = True
    ) -> str:
        """导出记忆"""
        memories = self._collect_memories()

        if export_format == "json":
            return self.exporter.export_to_json(memories, file_path, include_metadata)
        elif export_format == "text":
            return self.exporter.export_to_text(memories, file_path)
        elif export_format == "markdown":
            return self.exporter.export_to_markdown(memories, file_path)
        elif export_format == "csv":
            return self.exporter.export_to_csv(memories, file_path)
        else:
            return self.exporter.export_to_json(memories, file_path, include_metadata)

    def create_share(
        self,
        memory_ids: List[str],
        share_type: str = "read",
        expires_hours: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """创建分享"""
        memories = self._collect_memories()

        # 过滤指定的记忆
        if memory_ids:
            memories = [m for m in memories if m.get('memory_id') in memory_ids]

        expires_at = None
        if expires_hours:
            expires_at = time.time() + (expires_hours * 3600)

        return self.sharer.create_share(
            memory_ids=memory_ids,
            memories=memories,
            share_type=share_type,
            expires_at=expires_at,
            metadata=metadata
        )

    def get_share(self, share_id: str) -> Optional[Dict[str, Any]]:
        """获取分享"""
        return self.sharer.get_share(share_id)

    def delete_share(self, share_id: str) -> bool:
        """删除分享"""
        return self.sharer.delete_share(share_id)

    def list_shares(self) -> List[Dict[str, Any]]:
        """列出所有分享"""
        return self.sharer.list_shares()
