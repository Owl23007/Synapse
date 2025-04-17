from abc import ABC, abstractmethod
from typing import Optional, AsyncGenerator

class BaseInputHandler(ABC):
    """输入处理器抽象基类"""
    
    @abstractmethod
    async def get_input(self) -> str:
        """获取输入"""
        pass
        
    @abstractmethod
    async def setup(self):
        """初始化设置"""
        pass
        
    @abstractmethod
    async def cleanup(self):
        """清理资源"""
        pass
        
    async def start(self):
        """启动组件"""
        await self.setup()
        
    async def stop(self):
        """停止组件"""
        await self.cleanup()
        
    async def input_stream(self) -> AsyncGenerator[str, None]:
        """输入流生成器"""
        while True:
            yield await self.get_input()