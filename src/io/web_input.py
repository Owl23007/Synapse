from typing import Optional, Dict, Any
import asyncio
import json
from collections import defaultdict
from .base_input import BaseInputHandler
from .message_bus import MessageBus, Message, MessagePriority

class WebInputHandler(BaseInputHandler):
    def __init__(self, message_bus: MessageBus):
        super().__init__()
        self.message_bus = message_bus
        self._current_input: Optional[str] = None
        self._current_user_id: Optional[str] = None
        self._input_queues: Dict[str, asyncio.Queue[Dict[str, Any]]] = defaultdict(asyncio.Queue)
        self._user_sessions: Dict[str, Dict[str, Any]] = {}

    async def get_input(self, user_id: Optional[str] = None, timeout: Optional[float] = None) -> Optional[str]:
        try:
            if user_id:
                input_data = await asyncio.wait_for(
                    self._input_queues[user_id].get(),
                    timeout=timeout
                )
                self._current_input = input_data.get("content", "")
                self._current_user_id = user_id
            else:
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
            error_msg = Message(
                content=f"获取Web输入时出错: {str(e)}",
                type="error",
                priority=MessagePriority.HIGH
            )
            await self.message_bus.publish("system_error", error_msg)
            return None

    @property
    def current_user_id(self) -> Optional[str]:
        return self._current_user_id

    async def handle_input(self, data: Dict[str, Any]) -> None:
        user_id = data.get("user_id")
        if not user_id:
            return
            
        if user_id not in self._user_sessions:
            self._user_sessions[user_id] = {
                "last_active": asyncio.get_event_loop().time(),
                "message_count": 0,
                "session_start": asyncio.get_event_loop().time()
            }
        else:
            self._user_sessions[user_id]["last_active"] = asyncio.get_event_loop().time()
            self._user_sessions[user_id]["message_count"] += 1
            
        await self._input_queues[user_id].put(data)
        
        input_msg = Message(
            content=json.dumps(data),
            type="input",
            user_id=user_id,
            priority=MessagePriority.NORMAL
        )
        await self.message_bus.publish("user_input", input_msg)
        
    async def setup(self) -> None:
        await self.message_bus.subscribe("web_input", self.handle_input)
        asyncio.create_task(self._cleanup_sessions())
        
        ready_msg = Message(
            content="Web输入处理器已就绪",
            type="info",
            priority=MessagePriority.LOW
        )
        await self.message_bus.publish("system_notification", ready_msg)
        
    async def _cleanup_sessions(self) -> None:
        while True:
            current_time = asyncio.get_event_loop().time()
            expired_users = []
            
            for user_id, session in self._user_sessions.items():
                if current_time - session["last_active"] > 1800:
                    expired_users.append(user_id)
                    
            for user_id in expired_users:
                del self._user_sessions[user_id]
                if user_id in self._input_queues:
                    del self._input_queues[user_id]
                    
            await asyncio.sleep(300)
        
    async def cleanup(self) -> None:
        self._current_input = None
        self._input_queues.clear()
        self._user_sessions.clear()
        
    def get_active_users(self) -> Dict[str, Dict[str, Any]]:
        return self._user_sessions.copy()
        
    async def broadcast_message(self, message: str, exclude_user: Optional[str] = None) -> None:
        for user_id in self._user_sessions:
            if user_id != exclude_user:
                broadcast_msg = Message(
                    content=message,
                    type="broadcast",
                    user_id=user_id,
                    priority=MessagePriority.NORMAL
                )
                await self.message_bus.publish("system_message", broadcast_msg)