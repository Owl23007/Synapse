from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI(title="Synapse WebUI")

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 模板引擎
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def chat_ui(request: Request):
    """聊天界面"""
    return templates.TemplateResponse("chat.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)