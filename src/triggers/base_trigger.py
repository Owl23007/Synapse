# -*- coding: utf-8 -*-
"""触发器基类模块"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import time
import re
from pydantic import BaseModel, Field

from ..io.message_bus import Message


class TriggerConfig(BaseModel):
    """触发器配置模型"""
    name: str = Field(..., description="触发器名称")
    description: str = Field(..., description="触发器描述")
    enabled: bool = Field(default=True, description="是否启用")
    priority: int = Field(default=0, description="优先级,数字越大优先级越高")
    conditions: Dict[str, Any] = Field(default={}, description="触发条件配置")


class BaseTrigger(ABC):
    """触发器基类"""
    
    def __init__(self, config: TriggerConfig):
        self.config = config
        
    @abstractmethod
    async def check(self, input_text: str, context: Optional[Dict] = None) -> bool:
        """检查是否触发
        
        Args:
            input_text: 输入文本
            context: 上下文信息
            
        Returns:
            bool: 是否触发
        """
        pass
        
    @abstractmethod
    async def execute(self, input_text: str, context: Optional[Dict] = None) -> Any:
        """执行触发器动作
        
        Args:
            input_text: 触发的输入文本
            context: 上下文信息
            
        Returns:
            Any: 执行结果
        """
        pass
        
    def is_enabled(self) -> bool:
        """是否启用"""
        return self.config.enabled
        
    def get_priority(self) -> int:
        """获取优先级"""
        return self.config.priority


class KeywordTrigger(BaseTrigger):
    """基于关键词的触发器"""
    
    def __init__(self, config: TriggerConfig, keywords: List[str], case_sensitive: bool = False):
        super().__init__(config)
        self.keywords = keywords
        self.case_sensitive = case_sensitive
    
    async def check(self, input_text: str, context: Optional[Dict] = None) -> bool:
        """检查消息是否包含关键词"""
        if not self.is_enabled():
            return False
        
        if not self.case_sensitive:
            input_text = input_text.lower()
            keywords = [k.lower() for k in self.keywords]
        else:
            keywords = self.keywords
        
        for keyword in keywords:
            if keyword in input_text:
                return True
        
        return False
    
    async def execute(self, input_text: str, context: Optional[Dict] = None) -> Any:
        return {
            'matched_keywords': [k for k in self.keywords if k in input_text]
        }


class RegexTrigger(BaseTrigger):
    """基于正则表达式的触发器"""
    
    def __init__(self, config: TriggerConfig, patterns: List[str]):
        super().__init__(config)
        self.patterns = [re.compile(pattern) for pattern in patterns]
    
    async def check(self, input_text: str, context: Optional[Dict] = None) -> bool:
        """检查消息是否匹配正则表达式"""
        if not self.is_enabled():
            return False
        
        for pattern in self.patterns:
            if pattern.search(input_text):
                return True
        
        return False
    
    async def execute(self, input_text: str, context: Optional[Dict] = None) -> Any:
        matches = []
        for pattern in self.patterns:
            match = pattern.search(input_text)
            if match:
                matches.append(match.group())
        return {
            'matched_patterns': matches
        }


class ScheduleTrigger(BaseTrigger):
    """基于时间的定时触发器"""
    
    def __init__(self, config: TriggerConfig, interval: int):
        """
        初始化定时触发器
        
        Args:
            config: 触发器配置
            interval: 触发间隔，以秒为单位
        """
        super().__init__(config)
        self.interval = interval
        self.last_check = time.time()
    
    async def check(self, input_text: str, context: Optional[Dict] = None) -> bool:
        """检查是否到达触发时间"""
        current_time = time.time()
        
        if current_time - self.last_check >= self.interval:
            self.last_check = current_time
            return True
        
        return False
    
    async def execute(self, input_text: str, context: Optional[Dict] = None) -> Any:
        return {
            'trigger_time': time.time(),
            'interval': self.interval
        }