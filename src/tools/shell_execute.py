from typing import Dict, Any
import aiohttp
from .base_tool import MCPTool

class ShellExecuteTool(MCPTool):
    """Shell命令执行工具"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(
            name="shell_execute",
            description="执行Shell命令并返回结果",
            mcp_config=config
        )
        
    async def validate_params(self, params: Dict[str, Any]) -> bool:
        """验证参数"""
        if 'command' not in params:
            return False
            
        # 检查是否包含危险命令
        dangerous_commands = ['rm -rf', 'mkfs', 'dd', '> /dev']
        command = params['command'].lower()
        return not any(cmd in command for cmd in dangerous_commands)
        
    async def call_mcp_api(self, params: Dict[str, Any]) -> Any:
        """调用Shell执行API"""
        url = f"{self.mcp_config['base_url']}/execute/shell"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, 
                json=params,
                timeout=self.mcp_config.get('timeout', 30)
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"API call failed: {await response.text()}")