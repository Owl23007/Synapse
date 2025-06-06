import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import networkx as nx
from pymongo import MongoClient
import redis
import jieba
import numpy as np
import json
import asyncio
import sqlite3
import aiosqlite
from src.core.config import Config
from ..io.message_bus import Message
from ..core.logger import LogConfig

# 获取配置好的logger
logger = LogConfig.get_instance().get_logger("memory_manager", "memory.log")

class MemorySystem:
    """三级记忆系统"""
    
    def __init__(self, config: Dict[str, Any]):
        logger.info("初始化记忆系统...")
        # 配置
        self.config: Dict[str, Any] = config
        
        # 初始化存储系统
        logger.info("连接MongoDB长期记忆存储...")
        self.mongo_client: MongoClient = MongoClient(config.get('mongodb_uri', 'mongodb://localhost:27017/'))
        self.db = self.mongo_client[config.get('db_name', 'synapse_memory')]
        
        # 初始化搜索和记忆方法
        self._store_context = self._store_in_context  # type: ignore
        self._store_cache = self._store_in_cache  # type: ignore
        self._store_longterm = self._store_in_longterm  # type: ignore
        self._search_context = self._search_in_context  # type: ignore
        self._search_cache = self._search_in_cache  # type: ignore
        self._search_longterm = self._search_in_longterm  # type: ignore
        self._calculate_context_activation = self._calculate_activation  # type: ignore
        self._calculate_cache_activation = self._calculate_activation  # type: ignore
        self._calculate_longterm_activation = self._calculate_activation  # type: ignore
        
        # Redis缓存
        logger.info("连接Redis短期记忆缓存...")
        self.redis_client: redis.Redis = redis.Redis(
            host=config.get('redis_host', 'localhost'),
            port=config.get('redis_port', 6379),
            db=config.get('redis_db', 0)
        )
        
        # 上下文记忆(图结构)
        logger.info("初始化上下文记忆图结构...")
        self.context_graph: nx.Graph = nx.Graph()
        
        # 记忆激活阈值
        self.activation_threshold: float = config.get('activation_threshold', 0.5)
        logger.info(f"记忆激活阈值设置为: {self.activation_threshold}")
        
    async def store_memory(self, message: Message) -> None:
        """存储记忆到不同层级"""
        logger.info(f"开始存储消息ID: {message.id}的记忆...")
        
        # 1. 存入上下文图
        logger.debug("存储到上下文图...")
        self._store_context(message)
        
        # 2. 存入Redis短期缓存
        logger.debug("存储到Redis短期缓存...")
        await self._store_cache(message)
        
        # 3. 存入MongoDB长期记忆
        logger.debug("存储到MongoDB长期记忆...")
        await self._store_longterm(message)
        
        logger.info("记忆存储完成")

    async def retrieve_memory(self, query: str, context: Optional[Dict] = None) -> List[Dict]:
        """检索记忆"""
        logger.info(f"开始检索记忆，查询: {query}")
        results: list[dict[str, Any]] = []
        
        # 1. 从上下文图检索
        logger.debug("从上下文图检索...")
        context_results = await self._search_context(query)
        results.extend(context_results)
        
        # 2. 从Redis缓存检索
        logger.debug("从Redis缓存检索...")
        cache_results = await self._search_cache(query)
        results.extend(cache_results)
        
        # 3. 从MongoDB检索
        logger.debug("从MongoDB检索...")
        db_results = await self._search_longterm(query)
        results.extend(db_results)
        
        # 根据相关度排序
        results.sort(key=lambda x: x.get('relevance', 0), reverse=True)
        logger.info(f"检索完成，找到{len(results)}条相关记忆")
        return results

    async def calculate_activation(self, message: Message) -> float:
        """计算记忆激活度"""
        logger.debug(f"计算消息ID: {message.id}的激活度...")
        activation = 0.0
        
        # 1. 上下文相关性
        context_activation = self._calculate_context_activation(message.to_dict())
        activation += context_activation * 0.4
        
        # 2. 短期记忆相关性
        cache_activation = await self._calculate_cache_activation(message)
        activation += cache_activation * 0.3
        
        # 3. 长期记忆相关性
        longterm_activation = self._calculate_longterm_activation(message.to_dict())
        activation += longterm_activation * 0.3
        
        logger.debug(f"最终激活度: {activation}")
        return activation
        
    async def _store_in_context(self, message: Message) -> None:
        """存储到上下文记忆"""
        if not message.content:
            return
        self.context_graph.add_node(message.id, data=message.to_dict())

    async def _store_in_cache(self, message: Message) -> None:
        """存储到缓存记忆"""
        if not message.content:
            return
        # 假设 redis_client.set 是同步方法
        self.redis_client.set(f"msg:{message.id}", json.dumps(message.to_dict()))

    async def _store_in_longterm(self, message: Message) -> None:
        """存储到长期记忆"""
        if not message.content:
            return
        # 假设 insert_one 是同步方法
        self.db.messages.insert_one(message.to_dict())

    async def _search_in_context(self, query: str) -> list[dict[str, Any]]:
        """在上下文记忆中搜索"""
        results: list[dict[str, Any]] = []
        for node in self.context_graph.nodes():
            data = self.context_graph.nodes[node].get('data', {})
            if self._calculate_similarity(query, data.get('content', '')) > 0.5:
                results.append(data)
        return results

    async def _search_in_cache(self, query: str) -> list[dict[str, Any]]:
        """在缓存记忆中搜索"""
        results: list[dict[str, Any]] = []
        for key in self.redis_client.scan_iter("msg:*"):
            value = self.redis_client.get(key)
            if value is None:
                continue
            data = json.loads(value)
            if self._calculate_similarity(query, data.get('content', '')) > 0.5:
                results.append(data)
        return results

    async def _search_in_longterm(self, query: str) -> list[dict[str, Any]]:
        """在长期记忆中搜索"""
        results: list[dict[str, Any]] = []
        for doc in self.db.messages.find({"$text": {"$search": query}}):
            results.append(doc)
        return results

    def _calculate_activation(self, memory: Dict[str, Any]) -> float:
        """计算记忆的活跃度"""
        # 简单实现：根据时间衰减
        time_diff = time.time() - memory.get('timestamp', 0)
        return max(0, 1 - time_diff / (24 * 3600))  # 24小时衰减到0

    def _store_context(self, message: Message) -> None:
        """存储到上下文图"""
        msg_id = message.id
        self.context_graph.add_node(msg_id, data=message.to_dict())
        
        # 连接相关消息
        for prev_id in self.context_graph.nodes():
            if (prev_id != msg_id):
                # 修正：只传递字符串内容给 _calculate_similarity
                similarity = self._calculate_similarity(
                    str(message.data.get('content', '')),
                    str(self.context_graph.nodes[prev_id]['data'].get('data', ''))
                )
                if similarity > 0.3:
                    self.context_graph.add_edge(msg_id, prev_id, weight=similarity)
                    
    async def _store_cache(self, message: Message) -> None:
        """存储到Redis缓存"""
        msg_dict = message.to_dict()
        expire_time = self.config.get('cache_expire_seconds', 3600)  # 默认1小时
        # setex 和 insert_one 实际为同步方法，不能 await，修正如下：
        self.redis_client.setex(
            f"msg:{message.id}",
            expire_time,
            json.dumps(msg_dict)
        )
        
    async def _store_longterm(self, message: Message) -> None:
        """存储到MongoDB长期记忆"""
        msg_dict = message.to_dict()
        msg_dict['stored_at'] = datetime.now()
        self.db.messages.insert_one(msg_dict)
        
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算两段文本的相似度"""
        if not isinstance(text1, str) or not isinstance(text2, str):
            return 0.0
            
        words1 = set(jieba.cut(text1))
        words2 = set(jieba.cut(text2))
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0

    def _calculate_context_activation(self, message: dict) -> float:
        """计算上下文相关性，返回0~1的分数"""
        # 这里简单实现：如果有content字段，返回0.5，否则0
        if message.get('content'):
            return 0.5
        return 0.0

    async def _calculate_cache_activation(self, message: Message) -> float:
        """计算短期记忆相关性，返回0~1的分数"""
        # 简单实现：如果消息内容包含'cache'，返回0.7，否则0.2
        if 'cache' in message.content:
            return 0.7
        return 0.2

    def _calculate_longterm_activation(self, message: dict) -> float:
        """计算长期记忆相关性，返回0~1的分数"""
        # 简单实现：如果有'timestamp'字段且在一天内，返回0.9，否则0.3
        ts = message.get('timestamp')
        if ts:
            now = time.time()
            if now - ts < 86400:
                return 0.9
        return 0.3

class MemoryManager:
    """记忆管理器"""
    
    def __init__(self, config: Config):
        self.config = config
        self.db_path = config.memory_path
        self.ttl = config.memory_ttl
        self.max_tokens = config.memory_max_tokens
        self._conn = None
        
    async def init(self):
        """初始化记忆管理器"""
        # 创建数据库连接
        self._conn = await aiosqlite.connect(self.db_path)
        
        # 创建必要的表
        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp REAL NOT NULL,
                relevance REAL DEFAULT 0,
                metadata TEXT
            )
        """)
        
        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                input TEXT NOT NULL,
                response TEXT NOT NULL,
                timestamp REAL NOT NULL,
                context TEXT
            )
        """)
        
        await self._conn.commit()
        logger.info("记忆管理器初始化完成")
        
    async def cleanup(self):
        """清理记忆管理器"""
        if self._conn:
            await self._conn.close()
            self._conn = None
        logger.info("记忆管理器已清理")
        
    async def add_memory(self, memory_type: str, content: str, metadata: Optional[Dict] = None):
        """添加记忆
        
        Args:
            memory_type: 记忆类型
            content: 记忆内容
            metadata: 元数据
        """
        if self._conn is None:
            raise RuntimeError("数据库连接未初始化 (_conn is None)")
        timestamp = datetime.now().timestamp()
        await self._conn.execute(
            "INSERT INTO memories (id, type, content, timestamp, metadata) VALUES (?, ?, ?, ?, ?)",
            (
                f"{memory_type}_{timestamp}",
                memory_type,
                content,
                timestamp,
                json.dumps(metadata) if metadata else None
            )
        )
        await self._conn.commit()
        
    async def get_context(self, query: str, limit: int = 5) -> List[Dict]:
        """获取相关上下文
        
        Args:
            query: 查询文本
            limit: 返回的记忆数量限制
            
        Returns:
            List[Dict]: 相关记忆列表
        """
        if self._conn is None:
            raise RuntimeError("数据库连接未初始化 (_conn is None)")
        async with self._conn.execute(
            "SELECT * FROM memories ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            
        memories = []
        for row in rows:
            memories.append({
                "id": row[0],
                "type": row[1],
                "content": row[2],
                "timestamp": row[3],
                "relevance": row[4],
                "metadata": json.loads(row[5]) if row[5] else None
            })
            
        return memories
        
    async def add_interaction(self, input_text: str, response: str, context: Optional[Dict] = None):
        """添加对话交互记录
        
        Args:
            input_text: 输入文本
            response: 响应文本
            context: 上下文信息
        """
        if self._conn is None:
            raise RuntimeError("数据库连接未初始化 (_conn is None)")
        await self._conn.execute(
            "INSERT INTO interactions (input, response, timestamp, context) VALUES (?, ?, ?, ?)",
            (
                input_text,
                response,
                datetime.now().timestamp(),
                json.dumps(context) if context else None
            )
        )
        await self._conn.commit()
        
    async def get_recent_interactions(self, limit: int = 10) -> List[Dict]:
        """获取最近的对话记录
        
        Args:
            limit: 返回的记录数量限制
            
        Returns:
            List[Dict]: 对话记录列表
        """
        if self._conn is None:
            raise RuntimeError("数据库连接未初始化 (_conn is None)")
        async with self._conn.execute(
            "SELECT * FROM interactions ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            
        interactions = []
        for row in rows:
            interactions.append({
                "id": row[0],
                "input": row[1],
                "response": row[2],
                "timestamp": row[3],
                "context": json.loads(row[4]) if row[4] else None
            })
            
        return interactions
        
    async def clear_old_memories(self, before_timestamp: Optional[float] = None):
        """清理旧记忆
        
        Args:
            before_timestamp: 清理该时间戳之前的记忆,默认使用TTL计算
        """
        if self._conn is None:
            raise RuntimeError("数据库连接未初始化 (_conn is None)")
        if before_timestamp is None:
            before_timestamp = datetime.now().timestamp() - self.ttl
            
        await self._conn.execute(
            "DELETE FROM memories WHERE timestamp < ?",
            (before_timestamp,)
        )
        await self._conn.commit()