"""消息总线和消息基类模块，用于系统内部组件通信"""

import asyncio
import json
import uuid
import time
from typing import Dict, List, Any, Callable, Coroutine, Optional, Union
from datetime import datetime
from collections import defaultdict
from ..core.logger import LogConfig
from enum import IntEnum

# 获取配置好的logger
logger = LogConfig.get_instance().get_logger("message_bus", "message_bus.log")

class MessagePriority(IntEnum):
    """消息优先级定义"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3

class Message:
    def __init__(
        self,
        content: str,
        source: Optional[str] = None,
        type: str = "text",
        metadata: Optional[Dict[Any, Any]] = None,
        context: Optional[Dict[Any, Any]] = None,
        user_id: Optional[str] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        max_retries: int = 3
    ) -> None:
        self.id = str(uuid.uuid4())  # 添加唯一ID
        self.content = content
        self.source = source
        self.type = type
        self.metadata = metadata or {}
        self.context = context or {}
        self.user_id = user_id
        self.timestamp = time.time()
        self.priority = priority
        self.retry_count = 0
        self.max_retries = max_retries
        self.data: dict[str, Any] = {}  # 添加通用数据字段

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "type": self.type,
            "source": self.source,
            "metadata": self.metadata,
            "context": self.context,
            "user_id": self.user_id,
            "timestamp": self.timestamp
        }

class MessageBus:
    """消息总线，用于组件间通信"""
    
    def __init__(self):
        """初始化消息总线"""
        self._subscribers = defaultdict(list)
        self._running = True
        self._message_queue = asyncio.PriorityQueue()
        self._processing_tasks = set()
        
    async def publish(self, topic: str, message: Union[Dict[str, Any], Message, str], 
                     priority: MessagePriority = MessagePriority.NORMAL) -> None:
        """发布消息到指定主题
        
        Args:
            topic: 消息主题
            message: 消息内容可以是字典、Message对象或字符串
            priority: 消息优先级
        """
        if not self._running:
            return
            
        if isinstance(message, dict):
            msg = Message(
                content=json.dumps(message),
                type=topic,
                priority=priority
            )
        elif isinstance(message, str):
            msg = Message(
                content=message,
                type=topic,
                priority=priority
            )
        else:
            msg = message
            
        logger.debug(f"发布消息到主题 {topic}: {msg.to_dict()}")
        
        await self._message_queue.put((-msg.priority.value, msg, topic))
        
        # 确保消息处理任务正在运行
        if not self._processing_tasks:
            task = asyncio.create_task(self._process_messages())
            self._processing_tasks.add(task)
            task.add_done_callback(self._processing_tasks.discard)
            
    async def _process_messages(self) -> None:
        """处理消息队列中的消息"""
        while self._running:
            try:
                _, message, topic = await self._message_queue.get()
                
                if topic not in self._subscribers:
                    self._message_queue.task_done()
                    continue
                    
                tasks = []
                for callback in self._subscribers[topic]:
                    try:
                        task = asyncio.create_task(self._execute_callback(callback, message))
                        tasks.append(task)
                    except Exception as e:
                        logger.error(f"创建消息处理任务时出错: {str(e)}")
                
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
                
                self._message_queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"处理消息队列时出错: {str(e)}")
                await asyncio.sleep(1)  # 避免过于频繁的错误
                
    async def _execute_callback(self, callback: Callable, message: Message) -> None:
        """执行回调函数，支持重试机制
        
        Args:
            callback: 消息处理回调函数
            message: 消息对象
        """
        while message.retry_count < message.max_retries:
            try:
                await callback(message.to_dict())
                return
            except Exception as e:
                message.retry_count += 1
                if message.retry_count >= message.max_retries:
                    logger.error(f"消息处理失败，已达到最大重试次数: {str(e)}")
                    return
                logger.warning(f"消息处理失败，正在重试 ({message.retry_count}/{message.max_retries}): {str(e)}")
                await asyncio.sleep(min(2 ** message.retry_count, 30))  # 指数退避
                
    async def subscribe(self, topic: str, callback: Callable) -> None:
        """订阅指定主题
        
        Args:
            topic: 要订阅的主题
            callback: 消息处理回调函数
        """
        logger.debug(f"订阅主题: {topic}")
        if not asyncio.iscoroutinefunction(callback):
            raise ValueError("回调函数必须是异步函数")
        self._subscribers[topic].append(callback)
        
    def unsubscribe(self, topic: str, callback: Callable) -> None:
        """取消订阅指定主题
        
        Args:
            topic: 要取消订阅的主题
            callback: 要移除的回调函数
        """
        if topic in self._subscribers and callback in self._subscribers[topic]:
            self._subscribers[topic].remove(callback)
            
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
        
    async def shutdown(self) -> None:
        """关闭消息总线"""
        self._running = False
        if self._processing_tasks:
            await asyncio.gather(*self._processing_tasks, return_exceptions=True)
        # 等待所有消息处理完成
        await self._message_queue.join()

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
    
    async def send_message(self, msg_type: str, data: Any, metadata: Optional[Dict[str, Any]] = None) -> None:
        """向消息总线发送消息"""
        message = Message(
            content=json.dumps(data) if not isinstance(data, str) else data,
            type=msg_type,
            source=self.name,
            metadata=metadata
        )
        await self.message_bus.publish(msg_type, message)