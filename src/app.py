import asyncio
import sys
import signal
import os
from typing import Set
import platform

# 设置 TensorFlow 环境变量
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # 0=全部, 1=INFO, 2=WARNING, 3=ERROR

# 添加项目根目录到 Python 路径
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from src.core.agent_core import AgentCore
from src.core.config import load_config
from src.memory.memory_manager import MemoryManager
from .io.message_bus import MessageBus
from .io.web_input import WebInputHandler
from src.tools.base_tool import ToolManager
from src.data.rag_manager import RAGManager
from src.core.utils import setup_logging
from src.core.logger import LogConfig

# 获取配置好的logger
logger = LogConfig.get_instance().get_logger("main", "__main__.log")

class Application:
    """应用程序主类"""
    
    def __init__(self):
        # 初始化配置
        self.config = load_config()
        
        # 初始化日志
        self.logger = LogConfig.get_instance().get_logger("main", "__main__.log")
        
        # 初始化消息总线
        self.message_bus = MessageBus()
        
        # 初始化组件
        self.web_input = WebInputHandler(self.message_bus)
        self.agent = AgentCore(self.message_bus, self.config)
        
        # 组件列表,用于批量启动和停止
        self.components = [
            self.message_bus,
            self.web_input,
            self.agent
        ]
        
    async def start(self):
        """启动应用程序"""
        try:
            self.logger.info("正在启动应用程序...")
            
            # 按顺序启动所有组件
            for component in self.components:
                await component.start()
                
            self.logger.info("应用程序启动完成")
            
            # 等待直到收到退出信号
            while True:
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            self.logger.info("收到退出信号")
        except Exception as e:
            self.logger.error(f"应用程序运行错误: {str(e)}")
        finally:
            await self.stop()
            
    async def stop(self):
        """停止应用程序"""
        self.logger.info("正在停止应用程序...")
        
        # 反序停止所有组件
        for component in reversed(self.components):
            try:
                await component.stop()
            except Exception as e:
                self.logger.error(f"停止组件时出错: {str(e)}")
                
        self.logger.info("应用程序已停止")

def main():
    """程序入口"""
    app = Application()
    
    try:
        asyncio.run(app.start())
    except KeyboardInterrupt:
        print("\n正在退出...")
    except Exception as e:
        print(f"程序异常退出: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()