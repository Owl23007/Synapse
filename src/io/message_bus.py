# -*- coding: utf-8 -*-
"""消息总线和消息基类模块，用于系统内部组件通信"""

import asyncio
import json
import uuid
import time
from typing import Dict, List, Any, Callable, Coroutine, Optional, Union

class Message:
    """统一消息格式，支持不同类型的数据载荷"""
    
    def __init__(self, msg_type: str, data: Any, source: str, metadata: Dict = None):
        self.id = str(uuid.uuid4())
        self.type = msg_type
        self.data = data
        self.source = source  # 消息来源
        self.metadata = metadata or {}  # 元数据，如时间戳、优先级等
        self.trace_path = []  # 消息流经路径
        self.created_at = time.time()
    
    def add_trace(self, component_name: str) -> None:
        """记录消息经过的组件"""
        self.trace_path.append(component_name)
    
    def to_dict(self) -> Dict:
        """将消息转换为字典格式用于序列化"""
        return {
            "id": self.id,
            "type": self.type,
            "data": self.data,
            "source": self.source,
            "metadata": self.metadata,
            "trace_path": self.trace_path,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Message':
        """从字典创建消息对象"""
        msg = cls(data["type"], data["data"], data["source"], data.get("metadata"))
        msg.id = data["id"]
        msg.trace_path = data.get("trace_path", [])
        msg.created_at = data.get("created_at", time.time())
        return msg
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"Message(id={self.id}, type={self.type}, source={self.source})"


class MessageBus:
    """事件总线，用于组件间通信"""
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.middleware: List[Callable] = []  # 中间件处理链
        self._running = False
        self._queue = asyncio.Queue()
    
    def subscribe(self, msg_type: str, callback: Callable) -> None:
        """订阅特定类型的消息"""
        if msg_type not in self.subscribers:
            self.subscribers[msg_type] = []
        self.subscribers[msg_type].append(callback)
    
    def unsubscribe(self, msg_type: str, callback: Callable) -> None:
        """取消订阅特定类型的消息"""
        if msg_type in self.subscribers:
            if callback in self.subscribers[msg_type]:
                self.subscribers[msg_type].remove(callback)
    
    def add_middleware(self, middleware_func: Callable) -> None:
        """添加中间件处理函数"""
        self.middleware.append(middleware_func)
    
    async def publish(self, message: Message) -> None:
        """发布消息到总线"""
        await self._queue.put(message)
    
    async def start(self) -> None:
        """启动消息总线处理循环"""
        self._running = True
        while self._running:
            message = await self._queue.get()
            
            # 应用中间件
            for middleware in self.middleware:
                try:
                    message = await middleware(message)
                    if message is None:  # 中间件可以完全拦截消息
                        break
                except Exception as e:
                    print(f"Middleware error: {e}")
                    continue
            
            if message is None:
                self._queue.task_done()
                continue
            
            # 分发消息给订阅者
            callbacks = self.subscribers.get(message.type, []) + self.subscribers.get("*", [])
            for callback in callbacks:
                try:
                    asyncio.create_task(callback(message))
                except Exception as e:
                    print(f"Callback error: {e}")
            
            self._queue.task_done()
    
    async def stop(self) -> None:
        """停止消息总线"""
        self._running = False
        # 等待所有任务完成
        await self._queue.join()


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
        await self.message_bus.publish(message)