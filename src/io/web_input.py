from typing import Optional, Dict, Any
from .base_input import BaseInputHandler
from .message_bus import MessageBus, Message, MessagePriority
import asyncio
from collections import defaultdict

class WebInputHandler(BaseInputHandler):
    def __init__(self, message_bus: MessageBus):
        super().__init__()
        self.message_bus = message_bus
        self._current_input: Optional[str] = None
        self._input_queues = defaultdict(asyncio.Queue)  # 每个用户一个输入队列
        self._user_sessions: Dict[str, Dict[str, Any]] = {}  # 用户会话信息

    async def get_input(self, user_id: str = None, timeout: float = None) -> Optional[str]:
        """从Web界面获取输入
        
        Args:
            user_id: 用户ID，用于区分不同用户的输入
            timeout: 等待输入的超时时间（秒）
            
        Returns:
            获取到的输入字符串，超时返回None
        """
        try:
            if user_id:
                # 从特定用户的队列获取输入
                input_data = await asyncio.wait_for(
                    self._input_queues[user_id].get(),
                    timeout=timeout
                )
                self._current_input = input_data.get("content", "")
                self._current_user_id = user_id
            else:
                # 从任意用户队列获取输入
                while True:
                    for queue in self._input_queues.values():
                        if not queue.empty():
                            input_data = await queue.get()
                            self._current_input = input_data.get("content", "")
                            self._current_user_id = input_data.get("user_id")
                            return self._current_input
                    await asyncio.sleep(0.1)
            
            return self._current_input
            
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            await self.message_bus.publish(
                "system_error",
                Message(
                    msg_type="error",
                    data=f"获取Web输入时出错: {str(e)}",
                    priority=MessagePriority.HIGH
                )
            )
            return None

    @property
    def current_user_id(self):
        return getattr(self, '_current_user_id', None)

    async def handle_input(self, data: Dict[str, Any]) -> None:
        """处理来自Web的输入
        
        Args:
            data: 输入数据字典，包含content和user_id
        """
        user_id = data.get("user_id")
        if not user_id:
            return
            
        # 更新用户会话
        if user_id not in self._user_sessions:
            self._user_sessions[user_id] = {
                "last_active": asyncio.get_event_loop().time(),
                "message_count": 0,
                "session_start": asyncio.get_event_loop().time()
            }
        else:
            self._user_sessions[user_id]["last_active"] = asyncio.get_event_loop().time()
            self._user_sessions[user_id]["message_count"] += 1
            
        # 将输入放入对应用户的队列
        await self._input_queues[user_id].put(data)
        
        # 发布输入事件
        await self.message_bus.publish(
            "user_input",
            Message(
                msg_type="input",
                data=data,
                user_id=user_id,
                priority=MessagePriority.NORMAL
            )
        )
        
    async def setup(self):
        """设置Web输入处理器"""
        # 订阅web_input主题
        await self.message_bus.subscribe("web_input", self.handle_input)
        
        # 启动会话清理任务
        asyncio.create_task(self._cleanup_sessions())
        
        await self.message_bus.publish(
            "system_notification",
            Message(
                msg_type="info",
                data="Web输入处理器已就绪",
                priority=MessagePriority.LOW
            )
        )
        
    async def _cleanup_sessions(self):
        """清理过期的用户会话"""
        while True:
            current_time = asyncio.get_event_loop().time()
            expired_users = []
            
            for user_id, session in self._user_sessions.items():
                # 超过30分钟未活动的会话将被清理
                if current_time - session["last_active"] > 1800:
                    expired_users.append(user_id)
                    
            for user_id in expired_users:
                del self._user_sessions[user_id]
                if user_id in self._input_queues:
                    del self._input_queues[user_id]
                    
            await asyncio.sleep(300)  # 每5分钟检查一次
        
    async def cleanup(self):
        """清理资源"""
        self._current_input = None
        self._input_queues.clear()
        self._user_sessions.clear()
        
    def get_active_users(self) -> Dict[str, Dict[str, Any]]:
        """获取活跃用户列表
        
        Returns:
            包含用户会话信息的字典
        """
        return self._user_sessions.copy()
        
    async def broadcast_message(self, message: str, exclude_user: str = None):
        """向所有活跃用户广播消息
        
        Args:
            message: 要广播的消息
            exclude_user: 要排除的用户ID
        """
        for user_id in self._user_sessions:
            if user_id != exclude_user:
                await self.message_bus.publish(
                    "system_message",
                    Message(
                        msg_type="broadcast",
                        data=message,
                        user_id=user_id,
                        priority=MessagePriority.NORMAL
                    )
                )