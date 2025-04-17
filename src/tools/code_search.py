from typing import Dict, Any
import aiohttp
from .base_tool import MCPTool

class CodeSearchTool(MCPTool):
    """代码搜索工具"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(
            name="code_search",
            description="搜索代码库中的相关代码",
            mcp_config=config
        )
        
    async def validate_params(self, params: Dict[str, Any]) -> bool:
        """验证参数"""
        required = ['query', 'languages']
        return all(key in params for key in required)
        
    async def call_mcp_api(self, params: Dict[str, Any]) -> Any:
        """调用代码搜索API"""
        url = f"{self.mcp_config['base_url']}/search/code"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"API call failed: {await response.text()}")