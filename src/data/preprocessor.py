# -*- coding: utf-8 -*-
"""
前处理模块，负责提取上下文，计算相关性
"""

import asyncio
import logging
import re
from typing import Dict, List, Any, Optional, Tuple, Set

from ..io.message_bus import Message, MessageBus

# 配置日志
logger = logging.getLogger(__name__)


class ContextProcessor:
    """上下文处理器，负责计算上下文相关性和提取关键信息"""
    
    def __init__(self, message_bus: MessageBus, memory_manager=None):
        self.message_bus = message_bus
        self.memory_manager = memory_manager
        self.register_handlers()
    
    def register_handlers(self):
        """注册消息处理器"""
        self.message_bus.subscribe("trigger", self.process_trigger)
    
    async def process_trigger(self, message: Message) -> None:
        """处理触发消息，提取上下文"""
        try:
            trigger_data = message.data
            original_message = trigger_data.get("original_message", "")
            
            # 提取主题和实体
            entities, topics = await self._extract_entities_and_topics(original_message)
            
            # 如果有记忆管理器，获取相关记忆
            relevant_memories = []
            context_relevance = 0.0
            
            if self.memory_manager:
                # 获取相关记忆
                relevant_memories = await self.memory_manager.retrieve_memories(
                    topics=topics,
                    entities=entities,
                    max_results=5
                )
                
                # 计算上下文相关度
                context_relevance = await self._calculate_relevance(original_message, relevant_memories)
            
            # 创建预处理后的消息
            processed_msg = Message(
                "preprocessed",
                {
                    "original_message": original_message,
                    "entities": entities,
                    "topics": topics,
                    "relevant_memories": relevant_memories,
                    "context_relevance": context_relevance,
                    "trigger_name": trigger_data.get("trigger_name", "unknown"),
                },
                "context_processor",
                message.metadata
            )
            
            # 发布处理后的消息
            logger.debug(f"上下文处理完成，发布预处理消息: {processed_msg.id}")
            await self.message_bus.publish(processed_msg)
            
        except Exception as e:
            logger.error(f"处理触发消息时出错: {e}")
            # 创建错误消息
            error_msg = Message(
                "error",
                {
                    "error": str(e),
                    "module": "context_processor",
                    "original_message": message
                },
                "context_processor"
            )
            await self.message_bus.publish(error_msg)
    
    async def _extract_entities_and_topics(self, text: str) -> tuple:
        """从文本中提取实体和主题"""
        if not isinstance(text, str):
            return [], []
        
        # 这里实现简单的实体和主题提取
        # 在实际应用中可以使用更复杂的NLP方法，如命名实体识别
        words = re.findall(r'\w+', text.lower())
        
        # 简单的过滤词
        stop_words = {'的', '了', '是', '我', '你', '他', '她', '它', '这', '那', '有', '和', '与', 
                     'the', 'a', 'an', 'and', 'or', 'but', 'if', 'in', 'on', 'at', 'to', 'for', 'with'}
        
        # 过滤停用词
        filtered_words = [word for word in words if word not in stop_words and len(word) > 1]
        
        # 临时逻辑：将较长的词视为实体，较短的视为主题
        entities = [word for word in filtered_words if len(word) > 4]
        topics = [word for word in filtered_words if len(word) <= 4]
        
        return entities, topics
    
    async def _calculate_relevance(self, text: str, memories: List[Dict]) -> float:
        """计算输入文本与记忆的相关性"""
        if not memories or not text:
            return 0.0
        
        try:
            # 简单的相关性计算逻辑
            # 在实际应用中可以使用更复杂的算法，如余弦相似度等
            text_words = set(text.lower().split())
            memory_texts = [m.get('content', '') for m in memories]
            
            total_overlap = 0
            for memory_text in memory_texts:
                if not isinstance(memory_text, str):
                    continue
                memory_words = set(memory_text.lower().split())
                intersection = len(text_words.intersection(memory_words))
                union = max(len(text_words.union(memory_words)), 1)  # 避免除零错误
                overlap = intersection / union
                total_overlap += overlap
            
            # 计算平均重叠度
            avg_relevance = total_overlap / max(len(memories), 1)  # 避免除零错误
            # 缩放到0-1区间
            return min(avg_relevance * 5, 1.0)
            
        except Exception as e:
            logger.error(f"计算相关性时出错: {e}")
            return 0.0

def clean_data(data):
    # Implement data cleaning logic here
    cleaned_data = data.dropna()  # Example: dropping missing values
    return cleaned_data

def extract_features(data):
    # Implement feature extraction logic here
    features = data[['feature1', 'feature2']]  # Example: selecting specific features
    return features

def preprocess_data(data):
    # Combine cleaning and feature extraction
    cleaned_data = clean_data(data)
    features = extract_features(cleaned_data)
    return features