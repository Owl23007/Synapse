# -*- coding: utf-8 -*-
"""触发器管理系统"""

from typing import Dict, List, Any, Optional
import asyncio
import logging

from ..io.message_bus import Message, MessageBus
from .base_trigger import BaseTrigger, TriggerConfig
from src.core.logger import LogConfig

logger = LogConfig.get_instance().get_logger("trigger", "trigger.log")


class TriggerManager:
    """触发器管理器"""
    
    def __init__(self):
        self.triggers: Dict[str, BaseTrigger] = {}
        self._enabled = True
        
    async def init(self):
        """初始化触发器管理器"""
        # TODO: 从配置加载触发器
        logger.info("触发器管理器已初始化")
        
    async def cleanup(self):
        """清理触发器管理器"""
        self.triggers.clear()
        logger.info("触发器管理器已清理")
        
    def register_trigger(self, trigger: BaseTrigger):
        """注册触发器"""
        self.triggers[trigger.config.name] = trigger
        logger.info(f"注册触发器: {trigger.config.name}")
        
    def unregister_trigger(self, trigger_name: str):
        """注销触发器"""
        if trigger_name in self.triggers:
            del self.triggers[trigger_name]
            logger.info(f"注销触发器: {trigger_name}")
            
    async def check(self, input_text: str, context: Optional[Dict] = None) -> bool:
        """检查是否有触发器被触发
        
        Args:
            input_text: 输入文本
            context: 上下文信息
            
        Returns:
            bool: 是否有触发器被触发
        """
        if not self._enabled:
            return False
            
        # 按优先级排序触发器
        sorted_triggers = sorted(
            self.triggers.values(),
            key=lambda t: t.get_priority(),
            reverse=True
        )
        
        # 检查每个触发器
        for trigger in sorted_triggers:
            if not trigger.is_enabled():
                continue
                
            try:
                if await trigger.check(input_text, context):
                    logger.info(f"触发器 {trigger.config.name} 被触发")
                    # 执行触发器动作
                    await trigger.execute(input_text, context)
                    return True
            except Exception as e:
                logger.error(f"触发器 {trigger.config.name} 检查失败: {str(e)}")
                
        return False
        
    def enable(self):
        """启用触发器管理器"""
        self._enabled = True
        logger.info("触发器管理器已启用")
        
    def disable(self):
        """禁用触发器管理器"""
        self._enabled = False 
        logger.info("触发器管理器已禁用")
        
    def get_trigger(self, trigger_name: str) -> Optional[BaseTrigger]:
        """获取指定的触发器"""
        return self.triggers.get(trigger_name)
        
    def list_triggers(self) -> List[TriggerConfig]:
        """列出所有触发器配置"""
        return [t.config for t in self.triggers.values()]