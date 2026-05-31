"""
备份与导出/导入模块
基于第一性原理：确定性、可移植、格式稳定
"""

import json
import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class MemoryExporter:
    """记忆导出器"""

    @staticmethod
    def export_memory(
        memory_system,
        export_path: str,
        include_l1: bool = True,
        include_l2: bool = True,
        include_l3: bool = True,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        导出记忆数据

        Args:
            memory_system: 记忆系统实例
            export_path: 导出文件路径
            include_l1: 是否导出L1记忆
            include_l2: 是否导出L2记忆
            include_l3: 是否导出L3记忆
            session_id: 可选，仅导出指定会话记忆

        Returns:
            导出结果统计
        """
        export_data = {
            "version": "1.0.0",
            "export_time": datetime.utcnow().isoformat(),
            "system": "agent_memory_system",
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
            "total_count": 0,
            "export_path": export_path,
            "success": False
        }

        try:
            # 导出L1记忆（瞬时记忆）
            if include_l1 and hasattr(memory_system, 'l1'):
                try:
                    l1_memories = memory_system.l1.get_all()
                    if session_id:
                        l1_memories = [m for m in l1_memories if m.get('session_id') == session_id]
                    export_data["data"]["l1"] = l1_memories
                    stats["l1_count"] = len(l1_memories)
                except Exception as e:
                    logger.warning(f"导出L1记忆失败: {e}")

            # 导出L2记忆（情景记忆）
            if include_l2 and hasattr(memory_system, 'l2'):
                try:
                    l2_memories = memory_system.l2.get_all()
                    if session_id:
                        l2_memories = [m for m in l2_memories if m.get('session_id') == session_id]
                    export_data["data"]["l2"] = l2_memories
                    stats["l2_count"] = len(l2_memories)
                except Exception as e:
                    logger.warning(f"导出L2记忆失败: {e}")

            # 导出L3记忆（事实记忆）
            if include_l3 and hasattr(memory_system, 'l3'):
                try:
                    l3_memories = memory_system.l3.get_all()
                    export_data["data"]["l3"] = l3_memories
                    stats["l3_count"] = len(l3_memories)
                except Exception as e:
                    logger.warning(f"导出L3记忆失败: {e}")

            stats["total_count"] = stats["l1_count"] + stats["l2_count"] + stats["l3_count"]

            # 写入文件
            os.makedirs(os.path.dirname(os.path.abspath(export_path)), exist_ok=True)
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            stats["success"] = True
            logger.info(f"记忆导出成功: {export_path}, 总计 {stats['total_count']} 条")

        except Exception as e:
            stats["error"] = str(e)
            logger.error(f"记忆导出失败: {e}")

        return stats


class MemoryImporter:
    """记忆导入器"""

    @staticmethod
    def import_memory(
        memory_system,
        import_path: str,
        clear_before_import: bool = False
    ) -> Dict[str, Any]:
        """
        导入记忆数据

        Args:
            memory_system: 记忆系统实例
            import_path: 导入文件路径
            clear_before_import: 导入前是否清空

        Returns:
            导入结果统计
        """

        stats = {
            "l1_imported": 0,
            "l2_imported": 0,
            "l3_imported": 0,
            "total_imported": 0,
            "import_path": import_path,
            "success": False
        }

        try:
            # 读取文件
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)

            # 清空
            if clear_before_import:
                try:
                    if hasattr(memory_system, 'l1'):
                        memory_system.l1.clear()
                    if hasattr(memory_system, 'l2'):
                        memory_system.l2.clear()
                    if hasattr(memory_system, 'l3'):
                        memory_system.l3.clear()
                    logger.info("导入前已清空记忆系统")
                except Exception as e:
                    logger.warning(f"清空记忆系统失败: {e}")

            # 导入L1
            l1_data = import_data.get("data", {}).get("l1", [])
            for mem in l1_data:
                try:
                    if hasattr(memory_system, 'l1'):
                        memory_system.l1.add(mem.get('text', ''), mem.get('session_id', 'imported'))
                        stats["l1_imported"] += 1
                except Exception as e:
                    logger.warning(f"导入L1记忆失败: {e}")

            # 导入L2
            l2_data = import_data.get("data", {}).get("l2", [])
            for mem in l2_data:
                try:
                    if hasattr(memory_system, 'l2'):
                        metadata = mem.get('metadata', {})
                        # 添加 session_id 到 metadata
                        if 'session_id' in mem:
                            metadata['session_id'] = mem['session_id']
                        memory_system.l2.add(mem.get('text', ''), None, metadata)
                        stats["l2_imported"] += 1
                except Exception as e:
                    logger.warning(f"导入L2记忆失败: {e}")

            # 导入L3
            l3_data = import_data.get("data", {}).get("l3", [])
            for fact in l3_data:
                try:
                    if hasattr(memory_system, 'l3'):
                        memory_system.l3.add(
                            fact.get('entity', ''),
                            fact.get('attribute', ''),
                            fact.get('value', ''),
                            fact.get('source', 'imported'),
                            fact.get('confidence', 1.0)
                        )
                        stats["l3_imported"] += 1
                except Exception as e:
                    logger.warning(f"导入L3事实失败: {e}")

            stats["total_imported"] = stats["l1_imported"] + stats["l2_imported"] + stats["l3_imported"]
            stats["success"] = True

            logger.info(f"记忆导入成功: 总计 {stats['total_imported']} 条")

        except Exception as e:
            stats["error"] = str(e)
            logger.error(f"记忆导入失败: {e}")

        return stats


class BackupManager:
    """备份管理器"""

    def __init__(self, backup_dir: str = "./data/backups"):
        self.backup_dir = backup_dir
        os.makedirs(self.backup_dir, exist_ok=True)

    def create_backup(
        self,
        memory_system,
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建备份"""

        if name is None:
            name = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        backup_path = os.path.join(self.backup_dir, f"{name}.json")

        exporter = MemoryExporter()
        result = exporter.export_memory(
            memory_system,
            backup_path,
            include_l1=True,
            include_l2=True,
            include_l3=True
        )

        result["backup_name"] = name
        return result

    def list_backups(self) -> List[Dict[str, Any]]:
        """列出所有备份"""

        backups = []

        if not os.path.exists(self.backup_dir):
            return backups

        for filename in os.listdir(self.backup_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.backup_dir, filename)
                try:
                    stat = os.stat(filepath)
                    backups.append({
                        "name": filename,
                        "path": filepath,
                        "size": stat.st_size,
                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat()
                    })
                except Exception as e:
                    logger.warning(f"读取备份信息失败: {e}")

        # 按创建时间倒序
        backups.sort(key=lambda x: x["created"], reverse=True)
        return backups

    def restore_backup(
        self,
        memory_system,
        backup_name: str
    ) -> Dict[str, Any]:
        """从备份恢复"""

        backup_path = os.path.join(self.backup_dir, backup_name)
        if not backup_path.endswith('.json'):
            backup_path += '.json'

        if not os.path.exists(backup_path):
            return {"success": False, "error": f"备份不存在: {backup_name}"}

        importer = MemoryImporter()
        result = importer.import_memory(
            memory_system,
            backup_path,
            clear_before_import=True
        )

        result["backup_name"] = backup_name
        return result

    def delete_backup(self, backup_name: str) -> Dict[str, Any]:
        """删除备份"""

        backup_path = os.path.join(self.backup_dir, backup_name)
        if not backup_path.endswith('.json'):
            backup_path += '.json'

        if os.path.exists(backup_path):
            try:
                os.remove(backup_path)
                return {"success": True, "backup_name": backup_name}
            except Exception as e:
                return {"success": False, "error": str(e)}

        return {"success": False, "error": f"备份不存在: {backup_name}"}
