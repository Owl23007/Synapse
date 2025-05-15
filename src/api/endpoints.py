from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging
from .models import APIResponse, ChatRequest
from typing import Optional
import os
import yaml

# 创建FastAPI应用
app = FastAPI(
    title="Synapse AI API",
    description="Synapse AI Agent API documentation",
    version="1.0.0",
)

# 加载配置文件
def load_config():
    global API_KEY
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'ai_api.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            API_KEY = config.get('security', {}).get('api_key') or os.getenv("SYNAPSE_API_KEY", "your-secret-key")
    except Exception as e:
        logging.error(f"加载配置文件失败: {str(e)}")
        API_KEY = os.getenv("SYNAPSE_API_KEY", "your-secret-key")

# 在应用启动时加载配置
load_config()

# 设置速率限制器
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return _rate_limit_exceeded_handler(request, exc)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该配置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API密钥认证
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME)

async def verify_api_key(api_key: str = Depends(api_key_header)) -> bool:
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'ai_api.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            valid_key = config.get('security', {}).get('api_key') or os.getenv("SYNAPSE_API_KEY", "your-secret-key")
            if api_key != valid_key:
                raise HTTPException(
                    status_code=403,
                    detail="无效的API密钥"
                )
            return True
    except Exception as e:
        logging.error(f"验证API密钥时出错: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="服务器内部错误"
        )

@app.post("/api/v1/agent", response_model=APIResponse)
@limiter.limit("10/minute")
async def agent_chat(
    request: Request,
    chat_request: ChatRequest,
    authenticated: bool = Depends(verify_api_key)
):
    """
    处理聊天请求端点
    
    Args:
        chat_request: 包含消息内容和用户ID的请求体
        
    Returns:
        APIResponse: 标准化的API响应
    """
    try:
        # test 
        return APIResponse(
            status="success",
            message="处理成功",
            data= '',
            user_id=chat_request.user_id
        )
        # 从应用状态获取agent实例
        agent = request.app.state.agent
        if not agent:
            return APIResponse(
                status="error",
                message="Agent未初始化",
                user_id=chat_request.user_id
            )
            
        # 调用Agent处理消息
        context = await agent.memory.get_context(chat_request.message)
        knowledge = await agent.rag.get_knowledge(chat_request.message)
        response = await agent._process_response(chat_request.message, context, knowledge)
        
        return APIResponse(
            status="success",
            message="处理成功",
            data=response,
            user_id=chat_request.user_id
        )
    except Exception as e:
        logging.error(f"处理请求时出错: {str(e)}")
        return APIResponse(
            status="error",
            message=str(e),
            user_id=chat_request.user_id
        )