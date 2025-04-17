from typing import Optional
from .base_input import BaseInputHandler
from .message_bus import MessageBus

class WebInputHandler(BaseInputHandler):
    def __init__(self, message_bus: MessageBus):
        super().__init__()
        self.message_bus = message_bus
        self._current_input: Optional[str] = None

    async def get_input(self) -> str:
        """从Web界面获取输入"""
        # 订阅Web输入消息
        async for message in self.message_bus.subscribe("web_input"):
            self._current_input = message.get("content", "")
            if self._current_input:
                return self._current_input

    async def setup(self):
        """设置Web输入处理器"""
        await self.message_bus.publish("system_notification", {
            "type": "info",
            "content": "Web输入处理器已就绪"
        })

    async def cleanup(self):
        """清理资源"""
        self._current_input = None