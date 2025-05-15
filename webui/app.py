from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
import os
import yaml
import aiohttp
import asyncio
import logging

app = FastAPI(title="Synapse WebUI")

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 模板引擎
templates = Jinja2Templates(directory="templates")

def load_main_config():
    """加载主服务配置"""
    try:
        # 首先尝试从环境变量获取配置文件路径
        config_path = os.getenv('SYNAPSE_CONFIG_PATH')
        if not config_path:
            # 使用默认路径
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'default.yaml')
        
        if os.path.exists(config_path):
            print(f"[DEBUG] Loading main config from: {config_path}")
            with open(config_path, 'r', encoding='utf-8') as f:
                main_config = yaml.safe_load(f)
                return main_config.get('system', {})
        else:
            print(f"[WARNING] Config file not found at: {config_path}")
    except Exception as e:
        print(f"[ERROR] Failed to load main config: {e}")
    return {}

def load_config():
    """加载配置"""
    # 默认配置
    config = {
        'system': {
            'debug': False,
            'port': 8080,
            'log_level': 'INFO',
            'agent_url': None  # 预设为 None
        }
    }
    
    # 加载主服务配置
    main_config = load_main_config()
    agent_port = main_config.get('port', 2333)  # 默认2333端口
    agent_host = os.getenv('SYNAPSE_AGENT_HOST', '127.0.0.1')
    default_agent_url = f'http://{agent_host}:{agent_port}/api/v1/agent'
    config['system']['agent_url'] = default_agent_url

    # 读取配置文件
    try:
        config_path = os.path.join(os.path.dirname(__file__), 'config/default.yaml')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                file_config = yaml.safe_load(f)
                if file_config and 'system' in file_config:
                    # 只更新特定的键，保留原有的 agent_url
                    system_config = file_config['system']
                    for key in ['debug', 'port', 'log_level']:
                        if key in system_config:
                            config['system'][key] = system_config[key]
    except Exception as e:
        print(f"Warning: Failed to load config file: {e}")

    # 环境变量覆盖
    if os.getenv('SYNAPSE_DEBUG', '').lower() in ('1', 'true', 'yes', 'on'):
        config['system']['debug'] = True
        
    port_env = os.getenv('SYNAPSE_WEBUI_PORT')
    if port_env and port_env.isdigit():
        config['system']['port'] = int(port_env)
        
    env_agent_url = os.getenv('SYNAPSE_AGENT_URL')
    if env_agent_url:
        config['system']['agent_url'] = env_agent_url
    
    return config

# 加载配置
config = load_config()

# 初始化日志配置
log_level = config['system'].get('log_level', 'INFO')
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def is_debug():
    return config['system']['debug']

def get_port():
    return config['system']['port']

def get_agent_url():
    return config['system']['agent_url']

@app.get("/", response_class=HTMLResponse)
async def chat_ui(request: Request):
    """聊天界面"""
    return templates.TemplateResponse("chat.html", {"request": request})

@app.post("/chat")
async def chat_api(request: Request):
    """处理聊天请求，转发到 agent 服务"""
    try:
        data = await request.json()
        agent_url = get_agent_url()
        
        if not agent_url:
            return JSONResponse(
                status_code=503,
                content={"status": "error", "message": "Agent service URL not configured"}
            )
            
        if is_debug():
            print(f"[DEBUG] Forwarding request to {agent_url}")
            print(f"[DEBUG] Request data: {data}")
        
        # 使用aiohttp进行异步HTTP请求
        async with aiohttp.ClientSession() as session:
            async with session.post(
                agent_url,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=aiohttp.ClientTimeout(total=30)  # 30秒超时
            ) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    if is_debug():
                        print(f"[DEBUG] Successful response: {response_data}")
                    return JSONResponse(content=response_data)
                else:
                    print(f"[ERROR] Agent service returned {response.status}: {response_data}")
                    return JSONResponse(
                        status_code=response.status,
                        content={"status": "error", "message": f"Agent service error: {response_data}"}
                    )
                    
    except asyncio.TimeoutError:
        print("[ERROR] Request to agent service timed out")
        return JSONResponse(
            status_code=504,
            content={"status": "error", "message": "Request to agent service timed out"}
        )
    except requests.exceptions.ConnectionError:
        print("[ERROR] Could not connect to agent service")
        return JSONResponse(
            status_code=503,
            content={"status": "error", "message": "Could not connect to agent service"}
        )
    except Exception as e:
        print(f"[ERROR] Unexpected error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.post("/api/agent")
async def handle_chat(request: Request):
    """处理聊天消息，转发到主程序API"""
    try:
        data = await request.json()
        user_id = data.get('user_id', '')
        message = data.get('message', '')
        
        if not message:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Message is required", "user_id": user_id}
            )
            
        agent_url = get_agent_url()
        if not agent_url:
            return JSONResponse(
                status_code=503,
                content={"status": "error", "message": "Agent service URL not configured", "user_id": user_id}
            )
            
        if is_debug():
            logging.debug(f"Forwarding request to {agent_url}")
            logging.debug(f"Request data: {data}")
        
        # 使用aiohttp进行异步HTTP请求
        async with aiohttp.ClientSession() as session:
            async with session.post(
                agent_url,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=aiohttp.ClientTimeout(total=30)  # 30秒超时
            ) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    if is_debug():
                        logging.debug(f"Successful response: {response_data}")
                    response_data['user_id'] = user_id  # 确保响应中包含user_id
                    return JSONResponse(content=response_data)
                else:
                    logging.error(f"Agent service returned {response.status}: {response_data}")
                    return JSONResponse(
                        status_code=response.status,
                        content={
                            "status": "error", 
                            "message": f"Agent service error", 
                            "user_id": user_id,
                            "details": response_data
                        }
                    )
        return JSONResponse(
            status_code=504,
            content={"status": "error", "message": "Request to agent service timed out"}
        )
        
    except asyncio.TimeoutError:
        logging.error("Request to agent service timed out")
        return JSONResponse(
            status_code=504,
            content={
                "status": "error", 
                "message": "Request to agent service timed out",
                "user_id": user_id
            }
        )
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error", 
                "message": "Internal server error",
                "user_id": user_id,
                "details": str(e)
            }
        )
    
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=get_port())