# -*- coding: utf-8 -*-
"""触发器管理系统"""

from typing import Dict, List, Any, Optional
import asyncio
import logging

from ..io.message_bus import Message, MessageBus
from .base_trigger import BaseTrigger

# 配置日志
logger = logging.getLogger(__name__)


class TriggerManager:
    """管理多个触发器，协调触发逻辑"""
    
    def __init__(self, message_bus: MessageBus):
        self.message_bus = message_bus
        self.triggers: Dict[str, BaseTrigger] = {}
        self.register_handlers()
    
    def register_handlers(self):
        """注册消息总线处理函数"""
        self.message_bus.subscribe("input", self.handle_input)
        self.message_bus.subscribe("raw_input", self.handle_input)  # 处理原始输入
        self.message_bus.subscribe("schedule_check", self.handle_schedule_check)  # 处理定时检查
    
    def register_trigger(self, trigger: BaseTrigger) -> None:
        """注册新触发器"""
        self.triggers[trigger.name] = trigger
        logger.info(f"已注册触发器: {trigger.name}")
    
    def unregister_trigger(self, trigger_name: str) -> None:
        """注销触发器"""
        if trigger_name in self.triggers:
            del self.triggers[trigger_name]
            logger.info(f"已注销触发器: {trigger_name}")
    
    def get_trigger(self, trigger_name: str) -> Optional[BaseTrigger]:
        """获取指定名称的触发器"""
        return self.triggers.get(trigger_name)
    
    def get_all_triggers(self) -> List[BaseTrigger]:
        """获取所有触发器"""
        return list(self.triggers.values())
    
    async def handle_input(self, message: Message) -> None:
        """处理输入消息，评估是否触发"""
        triggered_results = []
        
        # 评估每个触发器
        for trigger_name, trigger in self.triggers.items():
            if trigger.enabled:
                try:
                    if await trigger.evaluate(message):
                        triggered_results.append((trigger, trigger.priority))
                except Exception as e:
                    logger.error(f"触发器 {trigger_name} 评估过程中出错: {e}")
        
        # 按优先级排序
        triggered_results.sort(key=lambda x: x[1], reverse=True)
        
        # 如果有触发器被激活，创建并发布触发消息
        for trigger, _ in triggered_results:
            # 创建新的触发消息
            trigger_msg = Message(
                "trigger", 
                {
                    "trigger_name": trigger.name,
                    "original_message": message.data,
                    "metadata": message.metadata
                }, 
                "trigger_manager",
                {
                    "priority": trigger.priority,
                    "trigger_time": trigger.last_triggered
                }
            )
            
            # 发布触发消息
            logger.debug(f"触发器 {trigger.name} 已激活，创建消息: {trigger_msg.id}")
            await self.message_bus.publish(trigger_msg)
    
    async def handle_schedule_check(self, message: Message) -> None:
        """处理定时检查消息"""
        # 处理基于时间的触发器
        for trigger_name, trigger in self.triggers.items():
            if trigger.enabled and hasattr(trigger, 'interval'):
                try:
                    if await trigger.evaluate(message):
                        # 创建新的触发消息
                        trigger_msg = Message(
                            "schedule_trigger", 
                            {
                                "trigger_name": trigger.name,
                                "schedule_type": "interval",
                                "interval": getattr(trigger, 'interval', 0)
                            }, 
                            "trigger_manager",
                            {"priority": trigger.priority}
                        )
                        
                        # 发布触发消息
                        logger.debug(f"定时触发器 {trigger.name} 已激活")
                        await self.message_bus.publish(trigger_msg)
                except Exception as e:
                    logger.error(f"定时触发器 {trigger_name} 评估过程中出错: {e}")
    
    def get_trigger_status(self) -> Dict[str, Dict]:
        """获取所有触发器的状态信息"""
        return {name: trigger.get_metadata() for name, trigger in self.triggers.items()}