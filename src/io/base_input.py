from abc import ABC, abstractmethod
from typing import Optional, AsyncGenerator

class BaseInputHandler(ABC):
    """输入处理器抽象基类"""
    
    @abstractmethod
    async def get_input(self, user_id: Optional[str] = None, timeout: Optional[float] = None) -> Optional[str]:
        """获取输入
        
        Args:
            user_id: 可选的用户ID
            timeout: 可选的超时时间（秒）
            
        Returns:
            输入字符串，如果超时则返回None
        """
        pass
        
    @abstractmethod
    async def setup(self) -> None:
        """初始化设置"""
        pass
        
    @abstractmethod
    async def cleanup(self) -> None:
        """清理资源"""
        pass
        
    async def start(self) -> None:
        """启动组件"""
        await self.setup()
        
    async def stop(self) -> None:
        """停止组件"""
        await self.cleanup()
        
    async def input_stream(self) -> AsyncGenerator[Optional[str], None]:
        """输入流生成器

        Returns:
            AsyncGenerator[Optional[str], None]: 异步生成器，生成输入字符串或None
        """
        while True:
            yield await self.get_input()