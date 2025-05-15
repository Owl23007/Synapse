import asyncio
import sys
import signal
import os
from typing import Set
import platform
import uvicorn
from fastapi import FastAPI

# 设置 TensorFlow 环境变量
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # 0=全部, 1=INFO, 2=WARNING, 3=ERROR

# 添加项目根目录到 Python 路径
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from src.core.agent_core import AgentCore
from src.core.config import load_config
from src.memory.memory_manager import MemoryManager
from src.io.message_bus import MessageBus
from src.io.web_input import WebInputHandler
from src.tools.base_tool import ToolManager
from src.data.rag_manager import RAGManager
from src.core.utils import setup_logging
from src.core.logger import LogConfig
from src.api.endpoints import app as api_app

# 获取配置好的logger
logger = LogConfig.get_instance().get_logger("main", "__main__.log")

class Application:
    """应用程序主类"""
    
    def __init__(self):
        # 初始化配置
        self.config = None
        self.message_bus = None
        self.memory_manager = None
        self.rag_manager = None
        self.tool_manager = None
        self.trigger_manager = None
        self.agent = None
        
    async def initialize(self):
        """初始化应用程序"""
        # 加载配置
        self.config = load_config()
        
        # 初始化日志
        self.logger = LogConfig.get_instance().get_logger("main", "__main__.log")
        self.logger.info("正在启动应用程序...")
        
        # 初始化核心组件
        self.message_bus = MessageBus()
        self.logger.info("消息总线已启动")
        
        self.memory_manager = MemoryManager(config=self.config)
        self.logger.info("记忆管理器初始化完成")
        
        self.rag_manager = RAGManager(config=self.config)
        self.logger.info("RAG系统初始化完成")
        
        self.tool_manager = ToolManager(config=self.config)
        self.logger.info("工具管理器初始化完成")
        
        self.web_input = WebInputHandler(message_bus=self.message_bus)
        self.logger.info("Web输入处理器初始化完成")
        
        # 初始化Agent
        self.agent = AgentCore(
            message_bus=self.message_bus,
            config=self.config
        )
        self.logger.info("智能体已启动")
        
        # 组件列表,用于批量启动和停止
        self.components = [
            self.message_bus,
            self.web_input,
            self.agent
        ]
        
    async def start(self):
        """启动应用程序"""
        await self.initialize()
        # 将agent实例添加到FastAPI应用状态中
        api_app.state.agent = self.agent
        
        config = self.config
        host = config.system.host  # 使用配置中的host
        port = config.system.port  # 使用配置中的port
        
        # 启动FastAPI服务
        logger.info(f"正在启动API服务 {host}:{port}...")
        
        return config, host, port

def main():
    """程序入口"""
    app = Application()
    loop = asyncio.get_event_loop()
    config, host, port = loop.run_until_complete(app.start())
    
    # 启动FastAPI服务
    uvicorn.run(api_app, host=host, port=port)

if __name__ == "__main__":
    main()