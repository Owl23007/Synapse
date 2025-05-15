import os
import yaml
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

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
class Config:
    """配置类"""
    # 基础配置
    debug: bool = False
    log_level: str = "INFO"
    
    # AI API配置
    ai_api: AIAPIConfig = field(default_factory=AIAPIConfig)
    
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

def load_config(config_path: Optional[str] = None) -> Config:
    """加载支持 include 的多 yaml 配置，自动合并 secrets.yaml"""
    if not config_path:
        config_path = os.path.join("config", "default.yaml")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    config_dict = _load_yaml_with_include(config_path)
    config = Config()
    # 基础配置
    if 'system' in config_dict:
        config.debug = config_dict['system'].get('debug', config.debug)
        config.log_level = config_dict['system'].get('log_level', config.log_level)
    # AI API配置
    ai_api_config = AIAPIConfig()
    if 'openai' in config_dict:
        openai = config_dict['openai']
        ai_api_config.openai_api_base = openai.get('api_base', ai_api_config.openai_api_base)
        ai_api_config.openai_api_key = openai.get('api_key', ai_api_config.openai_api_key)
        ai_api_config.openai_org_id = openai.get('organization_id', ai_api_config.openai_org_id)
    if 'azure_openai' in config_dict:
        azure = config_dict['azure_openai']
        ai_api_config.azure_api_base = azure.get('api_base', ai_api_config.azure_api_base)
        ai_api_config.azure_api_key = azure.get('api_key', ai_api_config.azure_api_key)
        ai_api_config.azure_api_version = azure.get('api_version', ai_api_config.azure_api_version)
        ai_api_config.azure_deployment_name = azure.get('deployment_name', ai_api_config.azure_deployment_name)
    if 'anthropic' in config_dict:
        anthropic = config_dict['anthropic']
        ai_api_config.anthropic_api_base = anthropic.get('api_base', ai_api_config.anthropic_api_base)
        ai_api_config.anthropic_api_key = anthropic.get('api_key', ai_api_config.anthropic_api_key)
    if 'proxy' in config_dict:
        proxy = config_dict['proxy']
        ai_api_config.http_proxy = proxy.get('http', ai_api_config.http_proxy)
        ai_api_config.https_proxy = proxy.get('https', ai_api_config.https_proxy)
    config.ai_api = ai_api_config
    # ...可继续扩展其他配置...
    return config