# -*- coding: utf-8 -*-
"""消息总线和消息基类模块，用于系统内部组件通信"""

import asyncio
import json
import uuid
import time
from typing import Dict, List, Any, Callable, Coroutine, Optional, Union
from datetime import datetime
from collections import defaultdict
from ..core.logger import LogConfig

# 获取配置好的logger
logger = LogConfig.get_instance().get_logger("message_bus", "message_bus.log")

class Message:
    """消息类"""
    
    def __init__(self, msg_type: str, data: Any, source: str = None, 
                 metadata: Dict = None, context: Dict = None):
        self.id = str(uuid.uuid4())
        self.type = msg_type
        self.data = data
        self.source = source
        self.timestamp = datetime.now()
        self.metadata = metadata or {}
        self.context = context or {}
        self.memory_activation = 0.0
        
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'id': self.id,
            'type': self.type,
            'data': self.data,
            'source': self.source,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata,
            'context': self.context,
            'memory_activation': self.memory_activation
        }
        
    @classmethod
    def from_dict(cls, data: Dict) -> 'Message':
        """从字典创建消息实例"""
        msg = cls(
            msg_type=data['type'],
            data=data['data'],
            source=data.get('source'),
            metadata=data.get('metadata', {}),
            context=data.get('context', {})
        )
        msg.id = data['id']
        msg.timestamp = datetime.fromisoformat(data['timestamp'])
        msg.memory_activation = data.get('memory_activation', 0.0)
        return msg

class MessageBus:
    """消息总线,用于组件间通信"""
    
    def __init__(self):
        """初始化消息总线"""
        self._subscribers = defaultdict(list)
        self._running = True
        
    async def publish(self, topic: str, message: Dict[str, Any]) -> None:
        """发布消息到指定主题
        
        Args:
            topic: 消息主题
            message: 消息内容字典
        """
        if not self._running:
            return
            
        logger.debug(f"发布消息到主题 {topic}: {message}")
        
        if topic not in self._subscribers:
            return
            
        tasks = []
        for callback in self._subscribers[topic]:
            try:
                tasks.append(callback(message))
            except Exception as e:
                logger.error(f"处理消息时出错: {str(e)}")
                
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            
    async def subscribe(self, topic: str, callback: Callable) -> None:
        """订阅指定主题
        
        Args:
            topic: 要订阅的主题
            callback: 消息处理回调函数
        """
        logger.debug(f"订阅主题: {topic}")
        self._subscribers[topic].append(callback)
        
    async def unsubscribe(self, subscription: Any) -> None: 
        """取消订阅
        
        Args:
            subscription: 订阅标识
        """
        topic, callback = subscription
        if topic in self._subscribers:
            try:
                self._subscribers[topic].remove(callback)
            except ValueError:
                pass

    async def start(self) -> None:
        """启动消息总线"""
        self._running = True
        logger.info("消息总线已启动")
        
    async def stop(self) -> None:
        """停止消息总线"""
        self._running = False
        # 清理所有订阅
        self._subscribers.clear()
        logger.info("消息总线已停止")

class PluginInterface:
    """插件接口基类，提供基础的插件功能和通信方法"""
    
    def __init__(self, name: str, message_bus: MessageBus):
        self.name = name
        self.message_bus = message_bus
        self.enabled = True
    
    def enable(self) -> None:
        """启用插件"""
        self.enabled = True
    
    def disable(self) -> None:
        """禁用插件"""
        self.enabled = False
    
    async def register_handlers(self) -> None:
        """注册消息处理函数，在子类中实现"""
        pass
    
    async def unregister_handlers(self) -> None:
        """注销消息处理函数，在子类中实现"""
        pass
    
    async def send_message(self, msg_type: str, data: Any, metadata: Dict = None) -> None:
        """向消息总线发送消息"""
        message = Message(msg_type, data, self.name, metadata)
        await self.message_bus.send(message)