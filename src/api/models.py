from pydantic import BaseModel
from typing import Optional, Any

class APIResponse(BaseModel):
    """统一的API响应模型"""
    status: str
    message: str
    data: Optional[Any] = None
    user_id: Optional[str] = None

class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
