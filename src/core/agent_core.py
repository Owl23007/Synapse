import asyncio
from typing import Dict, Any, Optional
from src.io.message_bus import MessageBus
from src.core.config import Config
from src.core.logger import LogConfig
from src.memory.memory_manager import MemoryManager
from src.data.rag_manager import RAGManager
from src.tools.base_tool import ToolManager
from src.triggers.trigger_manager import TriggerManager

logger = LogConfig.get_instance().get_logger("agent", "agent.log")

class AgentCore:
    """智能体核心类,负责协调各个子系统"""
    
    def __init__(self, message_bus: MessageBus, config: Config):
        self.message_bus = message_bus
        self.config = config
        self.memory = MemoryManager(config)
        self.rag = RAGManager(config)
        self.tools = ToolManager()
        self.triggers = TriggerManager()
        self._running = False
        
    async def start(self):
        """启动智能体"""
        self._running = True
        
        # 注册消息处理器
        await self.message_bus.subscribe("user_input", self._handle_input)
        await self.message_bus.subscribe("system", self._handle_system)
        
        # 初始化各个子系统
        await self.memory.init()
        await self.rag.init()
        await self.tools.init()
        await self.triggers.init()
        
        logger.info("智能体已启动")
        
    async def stop(self):
        """停止智能体"""
        self._running = False
        
        # 清理各个子系统
        await self.memory.cleanup()
        await self.rag.cleanup() 
        await self.tools.cleanup()
        await self.triggers.cleanup()
        
        logger.info("智能体已停止")
        
    async def _handle_input(self, message: Dict[str, Any]):
        """处理用户输入，支持多用户user_id"""
        if not self._running:
            return
        try:
            content = message.get("content", "").strip()
            user_id = message.get("user_id")  # 获取user_id
            if not content:
                return
            # 检查触发器
            if await self.triggers.check(content):
                return
            # 获取上下文记忆
            context = await self.memory.get_context(content)
            # 获取相关知识
            knowledge = await self.rag.get_knowledge(content)
            # 处理响应
            response = await self._process_response(content, context, knowledge)
            # 发送响应，带user_id
            await self.message_bus.publish("agent_output", {
                "type": "text",
                "content": response,
                "user_id": user_id
            })
            # 存储对话记忆
            await self.memory.add_interaction(content, response)
        except Exception as e:
            logger.error(f"处理输入时出错: {str(e)}", exc_info=True)
            logger.error(f"输入内容: {content}")
            logger.error(f"消息内容: {message}")
            await self.message_bus.publish("agent_output", {
                "type": "error",
                "content": f"处理输入时出错: {str(e)}",
                "user_id": message.get("user_id")
            })
            
    async def _handle_system(self, message: Dict[str, Any]):
        """处理系统消息"""
        if message.get("type") == "shutdown":
            self._running = False
            
    async def _process_response(self, query: str, context: Dict, knowledge: Dict) -> str:
        """生成响应"""
        # TODO: 实现响应生成逻辑
        return f"收到输入: {query}"