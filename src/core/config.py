import os
import yaml
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from glob import glob

@dataclass
class AIAPIConfig:
    """AI API配置类"""
    # OpenAI配置
    openai_api_base: str = "https://api.openai.com/v1"
    openai_api_key: str = ""
    openai_org_id: str = ""
    
    # Azure OpenAI配置
    azure_api_base: str = ""
    azure_api_key: str = ""
    azure_api_version: str = "2023-05-15"
    azure_deployment_name: str = ""
    
    # Anthropic配置
    anthropic_api_base: str = "https://api.anthropic.com"
    anthropic_api_key: str = ""
    
    # 代理配置
    http_proxy: str = ""
    https_proxy: str = ""

@dataclass
class APIConfig:
    """API配置类"""
    version: str = "v1"
    rate_limit: str = "10/minute"
    allowed_origins: list = field(default_factory=lambda: ["http://localhost:8080"])
    api_key: str = "your-secret-key"

@dataclass
class SystemConfig:
    """系统配置类"""
    port: int = 2333
    host: str = "0.0.0.0"
    name: str = "Synapse AI"
    version: str = "0.1.0"

@dataclass
class Config:
    """配置类"""
    # 基础配置
    debug: bool = False
    log_level: str = "INFO"
    
    # 系统配置
    system: SystemConfig = field(default_factory=SystemConfig)
    
    # AI API配置
    ai_api: AIAPIConfig = field(default_factory=AIAPIConfig)
    
    # API配置
    api: APIConfig = field(default_factory=APIConfig)
    
    # 记忆系统配置
    memory_backend: str = "sqlite"  # sqlite, redis, mongodb
    memory_path: str = "data/memory.db"
    memory_ttl: int = 3600  # 记忆过期时间(秒)
    memory_max_tokens: int = 2000  # 上下文最大token数
    
    # RAG系统配置
    vector_store: str = "faiss"  # faiss, milvus, elasticsearch
    vector_dim: int = 768
    chunk_size: int = 500
    chunk_overlap: int = 50
    
    # AI模型配置
    model_type: str = "openai"
    model_name: str = "gpt-3.5-turbo"
    api_base: str = "https://api.openai.com/v1"
    api_key: str = ""
    
    # 工具系统配置 
    enable_tools: bool = True
    tool_timeout: int = 30
    max_tool_calls: int = 5
    
    # 输入输出配置
    input_timeout: int = 300
    max_output_tokens: int = 1000
    show_thoughts: bool = True

def _deep_update(d: dict, u: dict) -> dict:
    """递归合并两个字典，u 优先"""
    for k, v in u.items():
        if isinstance(v, dict) and k in d and isinstance(d[k], dict):
            d[k] = _deep_update(d[k], v)
        else:
            d[k] = v
    return d

def _load_yaml_with_include(path: str, loaded=None) -> dict:
    """支持 include 的 yaml 加载"""
    if loaded is None:
        loaded = set()
    path = os.path.abspath(path)
    if path in loaded:
        return {}
    loaded.add(path)
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
    # 处理 include
    includes = data.pop('include', [])
    merged = {}
    for inc in includes:
        inc_path = os.path.join(os.path.dirname(path), inc)
        merged = _deep_update(merged, _load_yaml_with_include(inc_path, loaded))
    merged = _deep_update(merged, data)
    return merged

def load_config(config_dir: Optional[str] = None) -> Config:
    """从配置目录加载所有yaml配置文件
    
    Args:
        config_dir: 配置文件目录路径，默认为config目录
        
    Returns:
        Config: 合并后的配置对象
    """
    if not config_dir:
        config_dir = "config"
    if not os.path.exists(config_dir):
        raise FileNotFoundError(f"配置目录不存在: {config_dir}")
        
    # 首先加载default.yaml作为基础配置
    default_config_path = os.path.join(config_dir, "default.yaml")
    if not os.path.exists(default_config_path):
        raise FileNotFoundError(f"默认配置文件不存在: {default_config_path}")
        
    # 加载所有yaml配置文件
    config_dict = {}
    for yaml_file in sorted(glob(os.path.join(config_dir, "*.yaml"))):
        # 跳过示例配置文件
        if "example" in yaml_file.lower():
            continue
        file_config = _load_yaml_with_include(yaml_file)
        config_dict = _deep_update(config_dict, file_config)
        
    config = Config()
    
    # 基础配置
    if 'system' in config_dict:
        system = config_dict['system']
        config.system.port = system.get('port', config.system.port)
        config.system.host = system.get('host', config.system.host)
        config.system.name = system.get('name', config.system.name)
        config.system.version = system.get('version', config.system.version)
        config.debug = system.get('debug', config.debug)
        config.log_level = system.get('log_level', config.log_level)
        
    # AI API配置 
    if 'ai_api' in config_dict:
        ai_api = config_dict['ai_api']
        config.ai_api = AIAPIConfig(
            openai_api_base=ai_api.get('openai_api_base', config.ai_api.openai_api_base),
            openai_api_key=ai_api.get('openai_api_key', config.ai_api.openai_api_key),
            openai_org_id=ai_api.get('openai_org_id', config.ai_api.openai_org_id),
            azure_api_base=ai_api.get('azure_api_base', config.ai_api.azure_api_base),
            azure_api_key=ai_api.get('azure_api_key', config.ai_api.azure_api_key),
            azure_api_version=ai_api.get('azure_api_version', config.ai_api.azure_api_version),
            azure_deployment_name=ai_api.get('azure_deployment_name', config.ai_api.azure_deployment_name),
            anthropic_api_base=ai_api.get('anthropic_api_base', config.ai_api.anthropic_api_base),
            anthropic_api_key=ai_api.get('anthropic_api_key', config.ai_api.anthropic_api_key),
            http_proxy=ai_api.get('http_proxy', config.ai_api.http_proxy),
            https_proxy=ai_api.get('https_proxy', config.ai_api.https_proxy)
        )
    
    # API配置
    if 'api' in config_dict:
        api = config_dict['api']
        config.api = APIConfig(
            version=api.get('version', config.api.version),
            rate_limit=api.get('rate_limit', config.api.rate_limit),
            allowed_origins=api.get('allowed_origins', config.api.allowed_origins),
            api_key=api.get('api_key', config.api.api_key)
        )
        
    # 记忆系统配置
    if 'memory' in config_dict:
        memory = config_dict['memory']
        config.memory_backend = memory.get('backend', config.memory_backend)
        config.memory_path = memory.get('path', config.memory_path)
        config.memory_ttl = memory.get('ttl', config.memory_ttl)
        config.memory_max_tokens = memory.get('max_tokens', config.memory_max_tokens)
        
    # RAG系统配置
    if 'rag' in config_dict:
        rag = config_dict['rag']
        config.vector_store = rag.get('vector_store', config.vector_store)
        config.vector_dim = rag.get('vector_dim', config.vector_dim)
        config.chunk_size = rag.get('chunk_size', config.chunk_size)
        config.chunk_overlap = rag.get('chunk_overlap', config.chunk_overlap)
        
    # 工具系统配置
    if 'tools' in config_dict:
        tools = config_dict['tools']
        if isinstance(tools, dict):
            config.enable_tools = tools.get('enable', config.enable_tools)
            config.tool_timeout = tools.get('timeout', config.tool_timeout)
            config.max_tool_calls = tools.get('max_calls', config.max_tool_calls)
        
    # 输入输出配置
    if 'io' in config_dict:
        io = config_dict['io']
        config.input_timeout = io.get('input_timeout', config.input_timeout)
        config.max_output_tokens = io.get('max_output_tokens', config.max_output_tokens)
        config.show_thoughts = io.get('show_thoughts', config.show_thoughts)
        
    return config