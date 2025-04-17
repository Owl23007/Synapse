# -*- coding: utf-8 -*-
"""触发器基类模块"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import time
import re

from ..io.message_bus import Message


class BaseTrigger(ABC):
    """触发器基类，定义触发器的通用接口"""
    
    def __init__(self, name: str, config: Dict = None):
        self.name = name
        self.config = config or {}
        self.enabled = True
        self.priority = self.config.get("priority", 0)
        self.last_triggered = 0
        self.cooldown = self.config.get("cooldown", 0)  # 触发冷却时间，以秒为单位
    
    @abstractmethod
    async def evaluate(self, message: Message) -> bool:
        """评估消息是否应该触发处理流程"""
        pass
    
    def can_trigger(self) -> bool:
        """检查是否可以触发（考虑冷却时间）"""
        if not self.enabled:
            return False
        
        current_time = time.time()
        if current_time - self.last_triggered < self.cooldown:
            return False
        
        return True
    
    def update_last_triggered(self) -> None:
        """更新最后触发时间"""
        self.last_triggered = time.time()
    
    def enable(self) -> None:
        """启用触发器"""
        self.enabled = True
    
    def disable(self) -> None:
        """禁用触发器"""
        self.enabled = False
    
    def get_metadata(self) -> Dict:
        """获取触发器元数据"""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "priority": self.priority,
            "cooldown": self.cooldown,
            "last_triggered": self.last_triggered
        }


class KeywordTrigger(BaseTrigger):
    """基于关键词的触发器"""
    
    def __init__(self, name: str, keywords: List[str], case_sensitive: bool = False, config: Dict = None):
        super().__init__(name, config)
        self.keywords = keywords
        self.case_sensitive = case_sensitive
    
    async def evaluate(self, message: Message) -> bool:
        """检查消息是否包含关键词"""
        if not self.can_trigger():
            return False
        
        # 检查消息类型是否为文本
        if message.type != "text" and message.type != "input":
            return False
        
        text = message.data
        if isinstance(text, dict) and "content" in text:
            text = text.get("content", "")
        
        if not isinstance(text, str):
            return False
        
        # 关键词匹配
        if not self.case_sensitive:
            text = text.lower()
            keywords = [k.lower() for k in self.keywords]
        else:
            keywords = self.keywords
        
        for keyword in keywords:
            if keyword in text:
                self.update_last_triggered()
                return True
        
        return False


class RegexTrigger(BaseTrigger):
    """基于正则表达式的触发器"""
    
    def __init__(self, name: str, patterns: List[str], config: Dict = None):
        super().__init__(name, config)
        self.patterns = [re.compile(pattern) for pattern in patterns]
    
    async def evaluate(self, message: Message) -> bool:
        """检查消息是否匹配正则表达式"""
        if not self.can_trigger():
            return False
        
        # 检查消息类型是否为文本
        if message.type != "text" and message.type != "input":
            return False
        
        text = message.data
        if isinstance(text, dict) and "content" in text:
            text = text.get("content", "")
        
        if not isinstance(text, str):
            return False
        
        for pattern in self.patterns:
            if pattern.search(text):
                self.update_last_triggered()
                return True
        
        return False


class ScheduleTrigger(BaseTrigger):
    """基于时间的定时触发器"""
    
    def __init__(self, name: str, interval: int, config: Dict = None):
        """
        初始化定时触发器
        
        Args:
            name: 触发器名称
            interval: 触发间隔，以秒为单位
            config: 配置参数
        """
        super().__init__(name, config)
        self.interval = interval
        self.last_check = time.time()
    
    async def evaluate(self, message: Message) -> bool:
        """检查是否到达触发时间"""
        current_time = time.time()
        
        # 忽略消息内容，只检查时间
        if current_time - self.last_check >= self.interval:
            self.last_check = current_time
            self.update_last_triggered()
            return True
        
        return False