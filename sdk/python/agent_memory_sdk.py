"""
Python SDK for Agent Memory System
基于第一性原理：简洁、易用、可靠
"""
from typing import Dict, List, Any, Optional
import requests
import json


class AgentMemoryClient:
    """Agent Memory System Python Client"""
    
    def __init__(
        self,
        base_url: str = "http://localhost:5000",
        timeout: int = 30
    ):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def health(self) -> Dict[str, Any]:
        """健康检查"""
        url = f"{self.base_url}/health"
        response = self.session.get(url, timeout=self.timeout)
        return response.json()
    
    def add_memory(
        self,
        text: str,
        session_id: str = "default",
        level: str = "l2",
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """添加记忆"""
        url = f"{self.base_url}/api/v1/memory"
        data = {
            "text": text,
            "session_id": session_id,
            "level": level
        }
        if metadata:
            data["metadata"] = metadata
        response = self.session.post(url, json=data, timeout=self.timeout)
        return response.json()
    
    def get_memory(self, memory_id: str) -> Dict[str, Any]:
        """获取记忆"""
        url = f"{self.base_url}/api/v1/memory/{memory_id}"
        response = self.session.get(url, timeout=self.timeout)
        return response.json()
    
    def delete_memory(self, memory_id: str) -> Dict[str, Any]:
        """删除记忆"""
        url = f"{self.base_url}/api/v1/memory/{memory_id}"
        response = self.session.delete(url, timeout=self.timeout)
        return response.json()
    
    def recall(
        self,
        query: str,
        session_id: str = "default",
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """召回记忆"""
        url = f"{self.base_url}/api/v1/recall"
        data = {"query": query, "session_id": session_id}
        if limit:
            data["limit"] = limit
        response = self.session.post(url, json=data, timeout=self.timeout)
        return response.json()
    
    def add_fact(
        self,
        entity: str,
        attribute: str,
        value: str
    ) -> Dict[str, Any]:
        """添加事实"""
        url = f"{self.base_url}/api/v1/fact"
        data = {"entity": entity, "attribute": attribute, "value": value}
        response = self.session.post(url, json=data, timeout=self.timeout)
        return response.json()
    
    def query_facts(
        self,
        entity: Optional[str] = None,
        attribute: Optional[str] = None
    ) -> Dict[str, Any]:
        """查询事实"""
        url = f"{self.base_url}/api/v1/facts"
        params = {}
        if entity:
            params["entity"] = entity
        if attribute:
            params["attribute"] = attribute
        response = self.session.get(url, params=params, timeout=self.timeout)
        return response.json()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计"""
        url = f"{self.base_url}/api/v1/stats"
        response = self.session.get(url, timeout=self.timeout)
        return response.json()
    
    def preprocess(
        self,
        text: str,
        check_hallucination: bool = False
    ) -> Dict[str, Any]:
        """预处理文本"""
        url = f"{self.base_url}/api/v1/preprocess"
        data = {"text": text, "check_hallucination": check_hallucination}
        response = self.session.post(url, json=data, timeout=self.timeout)
        return response.json()
    
    def cleanup(
        self,
        level: str = "l2",
        days: Optional[int] = None
    ) -> Dict[str, Any]:
        """清理操作"""
        url = f"{self.base_url}/api/v1/governance/cleanup"
        data = {"level": level}
        if days:
            data["days"] = days
        response = self.session.post(url, json=data, timeout=self.timeout)
        return response.json()
    
    # 批量操作（高级API）
    def batch_add_memories(
        self,
        memories: List[Dict],
        session_id: str = "default"
    ) -> Dict[str, Any]:
        """批量添加记忆"""
        results = []
        for memory in memories:
            result = self.add_memory(
                text=memory["text"],
                session_id=session_id,
                level=memory.get("level", "l2"),
                metadata=memory.get("metadata")
            )
            results.append(result)
        return {
            "success": True,
            "total": len(results),
            "results": results
        }
    
    def batch_recall(
        self,
        queries: List[str],
        session_id: str = "default"
    ) -> Dict[str, Any]:
        """批量召回"""
        results = {}
        for query in queries:
            results[query] = self.recall(query, session_id)
        return {
            "success": True,
            "queries": len(queries),
            "results": results
        }
    
    def close(self):
        """关闭连接"""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# 便捷函数
def create_client(base_url: str = "http://localhost:5000") -> AgentMemoryClient:
    """创建客户端"""
    return AgentMemoryClient(base_url)
