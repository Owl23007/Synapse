import os
from typing import Dict, List, Optional, Any
import numpy as np
from dataclasses import dataclass
from src.core.config import Config
from src.core.logger import LogConfig

logger = LogConfig.get_instance().get_logger("rag", "rag.log")

@dataclass
class Document:
    """文档类"""
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[np.ndarray] = None

class RAGManager:
    """RAG(检索增强生成)管理器"""
    
    def __init__(self, config: Config):
        self.config = config
        self.chunk_size = config.chunk_size
        self.chunk_overlap = config.chunk_overlap
        self.vector_store = None
        self.documents: List[Document] = []
        
    async def init(self):
        """初始化RAG系统"""
        # 初始化向量存储
        if self.config.vector_store == "faiss":
            import faiss
            self.vector_store = faiss.IndexFlatL2(self.config.vector_dim)
        # TODO: 支持其他向量存储
        
        # 加载知识库文档
        await self._load_documents()
        
        logger.info("RAG系统初始化完成")
        
    async def cleanup(self):
        """清理RAG系统"""
        self.documents.clear()
        self.vector_store = None
        logger.info("RAG系统已清理")
        
    async def _load_documents(self):
        """加载文档"""
        # TODO: 实现文档加载和分块
        pass
        
    async def add_document(self, content: str, metadata: Optional[Dict] = None):
        """添加文档到知识库
        
        Args:
            content: 文档内容
            metadata: 文档元数据
        """
        # 1. 文档分块
        chunks = self._split_text(content)
        
        # 2. 获取嵌入向量
        embeddings = await self._get_embeddings(chunks)
        
        # 3. 创建文档对象并存储
        for chunk, embedding in zip(chunks, embeddings):
            doc = Document(
                content=chunk,
                metadata=metadata or {},
                embedding=embedding
            )
            self.documents.append(doc)
            
            # 添加到向量索引
            if self.vector_store is not None:
                self.vector_store.add(embedding.reshape(1, -1))
                
    async def get_knowledge(self, query: str, top_k: int = 3) -> List[Dict]:
        """检索相关知识

        Args:
            query: 查询文本
            top_k: 返回的文档数量
        """
        # 1. 获取查询向量
        query_embedding = (await self._get_embeddings([query]))[0]
        
        # 2. 向量检索
        if self.vector_store is not None:
            D, I = self.vector_store.search(query_embedding.reshape(1, -1), top_k)
            results = []
            for idx in I[0]:
                if idx < len(self.documents) and self.documents:  # 检查列表是否为空
                    doc = self.documents[idx]
                    results.append({
                        "content": doc.content,
                        "metadata": doc.metadata,
                        "score": float(D[0][len(results)])
                    })
            return results
        
        return []
        
    def _split_text(self, text: str) -> List[str]:
        """文本分块"""
        # 简单的固定窗口分块
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            if end < len(text):
                # 尝试在分块重叠区域找到合适的分割点
                overlap_start = max(end - self.chunk_overlap, start)
                split_pos = text.rfind("。", overlap_start, end)
                if split_pos != -1:
                    end = split_pos + 1
                    
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start = end - self.chunk_overlap
            
        return chunks
        
    async def _get_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """获取文本嵌入向量"""
        # TODO: 实现向量模型调用
        # 临时返回随机向量
        return [
            np.random.randn(self.config.vector_dim).astype('float32')
            for _ in texts
        ]