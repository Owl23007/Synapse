from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
import uuid
import os
import yaml

app = FastAPI(title="Synapse WebUI")

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 模板引擎
templates = Jinja2Templates(directory="templates")

# 读取debug配置（优先环境变量，其次webui/config/default.yaml，最后默认False）
def is_debug():
    env_debug = os.getenv('SYNAPSE_DEBUG')
    if env_debug is not None:
        return env_debug.lower() in ('1', 'true', 'yes', 'on')
    # 优先读取webui/config/default.yaml
    try:
        with open(os.path.join(os.path.dirname(__file__), 'config/default.yaml'), 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            return config.get('system', {}).get('debug', False)
    except Exception:
        return False

def get_port():
    # 优先环境变量
    port_env = os.getenv('SYNAPSE_WEBUI_PORT')
    if port_env and port_env.isdigit():
        return int(port_env)
    # 读取webui/config/default.yaml
    try:
        with open(os.path.join(os.path.dirname(__file__), 'config/default.yaml'), 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            port = config.get('system', {}).get('port')
            if port and isinstance(port, int):
                return port
    except Exception:
        pass
    return 8000  # 默认端口

@app.get("/", response_class=HTMLResponse)
async def chat_ui(request: Request):
    """聊天界面"""
    return templates.TemplateResponse("chat.html", {"request": request})

@app.post("/api/chat")
async def handle_chat(request: Request):
    """处理聊天消息，转发到主应用"""
    data = await request.json()
    message = data.get("message", "")
    # 简单生成user_id（实际可用session/cookie等）
    user_id = data.get("user_id") or str(uuid.uuid4())
    if is_debug():
        print(f"[DEBUG] /api/chat 收到请求: user_id={user_id}, message={message}, data={data}")

    # TODO: 这里应通过消息总线与主Agent通信，获取AI回复
    # 目前先返回模拟响应
    return JSONResponse({
        "status": "success",
        "reply": f"我收到了你的消息: '{message}' 🌸",
        "user_id": user_id
    })

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=get_port())