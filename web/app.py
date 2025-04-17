from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

app = FastAPI(title="Synapse WebUI")

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 模板引擎
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def chat_ui(request: Request):
    """可爱风格聊天界面"""
    return templates.TemplateResponse("chat.html", {"request": request})

@app.post("/api/chat")
async def handle_chat(request: Request):
    """处理聊天消息"""
    data = await request.json()
    message = data.get("message", "")
    
    # 这里应该调用主应用的AI处理逻辑
    # 目前先返回模拟响应
    return JSONResponse({
        "status": "success",
        "reply": f"我收到了你的消息: '{message}' 🌸"
    })

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)