import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class MCPTool(ABC):
    """MCP工具基类"""
    
    def __init__(self, name: str, description: str, mcp_config: Dict[str, Any]):
        self.name = name
        self.description = description
        self.mcp_config = mcp_config

    @abstractmethod
    async def validate_params(self, params: Dict[str, Any]) -> bool:
        """验证参数"""
        pass

    @abstractmethod
    async def call_mcp_api(self, params: Dict[str, Any]) -> Any:
        """调用MCP API"""
        pass

class ToolDescription(BaseModel):
    """工具描述模型"""
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具功能描述")
    parameters: Dict[str, Any] = Field(default={}, description="工具参数描述")
    required: List[str] = Field(default=[], description="必需参数列表")

class BaseTool(ABC):
    """工具基类"""
    
    def __init__(self):
        self._description = self.get_description()
        
    @abstractmethod
    def get_description(self) -> ToolDescription:
        """获取工具描述"""
        pass
        
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """执行工具功能"""
        pass
        
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """验证参数"""
        # 检查必需参数
        for param in self._description.required:
            if param not in params:
                raise ValueError(f"缺少必需参数: {param}")
                
        return True
        
class ToolManager:
    """工具管理器"""
    
    def __init__(self, config=None):
        self.tools: Dict[str, BaseTool] = {}
        self.config = config
        
    async def init(self):
        """初始化工具管理器"""
        # TODO: 动态加载工具
        pass
        
    async def cleanup(self):
        """清理工具管理器"""
        self.tools.clear()
        
    def register_tool(self, tool: BaseTool):
        """注册工具"""
        self.tools[tool.get_description().name] = tool
        
    def unregister_tool(self, tool_name: str):
        """注销工具"""
        if tool_name in self.tools:
            del self.tools[tool_name]
            
    async def execute_tool(self, tool_name: str, **params) -> Any:
        """执行工具
        
        Args:
            tool_name: 工具名称
            params: 工具参数
            
        Returns:
            Any: 工具执行结果
            
        Raises:
            ValueError: 工具不存在或参数无效
        """
        if tool_name not in self.tools:
            raise ValueError(f"工具不存在: {tool_name}")
            
        tool = self.tools[tool_name]
        
        # 验证参数
        tool.validate_params(params)
        
        # 执行工具
        return await tool.execute(**params)
        
    def get_tool_description(self, tool_name: str) -> Optional[ToolDescription]:
        """获取工具描述"""
        if tool_name in self.tools:
            return self.tools[tool_name].get_description()
        return None
        
    def list_tools(self) -> List[ToolDescription]:
        """列出所有工具"""
        return [tool.get_description() for tool in self.tools.values()]