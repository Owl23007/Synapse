"""测试系统通信连接的脚本"""
import asyncio
import sys
import os
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.io.message_bus import MessageBus, Message, MessagePriority
from src.core.logger import LogConfig

# 配置日志
logger = LogConfig.get_instance().get_logger("test_connection", "test_connection.log")

async def test_message_handler(message):
    """测试消息处理器"""
    logger.info(f"收到测试消息: {message}")
    
async def main():
    """主测试函数"""
    logger.info("开始连接测试...")
    
    # 创建消息总线实例
    message_bus = MessageBus()
    
    # 订阅测试主题
    await message_bus.subscribe("test_topic", test_message_handler)
    
    # 发送测试消息
    test_messages = [
        ("普通消息", MessagePriority.NORMAL),
        ("高优先级消息", MessagePriority.HIGH),
        ("紧急消息", MessagePriority.URGENT)
    ]
    
    for content, priority in test_messages:
        message = Message(
            msg_type="test",
            data={"content": content, "timestamp": datetime.now().isoformat()},
            priority=priority
        )
        
        logger.info(f"发送测试消息 [{priority.name}]: {content}")
        await message_bus.publish("test_topic", message)
        await asyncio.sleep(1)  # 等待消息处理
        
    # 测试与WebUI的连接
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            # 测试主服务API
            logger.info("测试主服务API连接...")
            try:
                async with session.post(
                    "http://localhost:2333/api/v1/agent",
                    json={"message": "测试消息", "user_id": "test_user"},
                    headers={"X-API-Key": "your-secret-key"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"主服务API响应成功: {json.dumps(data, ensure_ascii=False)}")
                    else:
                        logger.error(f"主服务API响应错误: {response.status}")
            except Exception as e:
                logger.error(f"连接主服务API失败: {str(e)}")
            
            # 测试WebUI
            logger.info("测试WebUI连接...")
            try:
                async with session.get("http://localhost:8081") as response:
                    if response.status == 200:
                        logger.info("WebUI连接成功")
                    else:
                        logger.error(f"WebUI响应错误: {response.status}")
            except Exception as e:
                logger.error(f"连接WebUI失败: {str(e)}")
                
    except Exception as e:
        logger.error(f"网络测试过程中出错: {str(e)}")
    
    # 关闭消息总线
    await message_bus.shutdown()
    logger.info("连接测试完成")

if __name__ == "__main__":
    asyncio.run(main())
