"""
Embedding模块 - 文本向量化
基于第一性原理：轻量开源、低成本高精度
"""
import hashlib
from typing import List, Optional, Any

# 可选依赖
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


class EmbeddingModel:
    """轻量级Embedding模型"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self._dimension = 384  # all-MiniLM-L6-v2输出维度
    
    def _load_model(self) -> None:
        """延迟加载模型"""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except ImportError:
                # 如果没有sentence_transformers，使用模拟Embedding
                print("Warning: sentence_transformers not found, using mock embedding")
                self._model = None
    
    def encode(self, text: str) -> Any:
        """编码单个文本"""
        self._load_model()
        
        if self._model and HAS_NUMPY:
            return self._model.encode(text, convert_to_numpy=True)
        else:
            # 模拟Embedding（用于开发测试）
            return self._mock_encode(text)
    
    def encode_batch(self, texts: List[str]) -> Any:
        """批量编码"""
        self._load_model()
        
        if self._model and HAS_NUMPY:
            return self._model.encode(texts, convert_to_numpy=True)
        else:
            return [self._mock_encode(text) for text in texts]
    
    def _mock_encode(self, text: str) -> Any:
        """模拟Embedding（用于开发测试）"""
        if HAS_NUMPY:
            hash_bytes = hashlib.sha256(text.encode('utf-8')).digest()
            rng = np.random.RandomState(int.from_bytes(hash_bytes[:4], 'little'))
            vector = rng.randn(self._dimension).astype(np.float32)
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm
            return vector
        else:
            # 无numpy时返回None
            return None
    
    @property
    def dimension(self) -> int:
        """获取向量维度"""
        return self._dimension


# 全局单例
_embedding_model: Optional[EmbeddingModel] = None


def get_embedding_model() -> EmbeddingModel:
    """获取Embedding模型单例"""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = EmbeddingModel()
    return _embedding_model
