import os
import yaml
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class Config:
    """配置类"""
    # 基础配置
    debug: bool = False
    log_level: str = "INFO"
    
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

def load_config(config_path: Optional[str] = None) -> Config:
    """加载配置文件
    
    Args:
        config_path: 配置文件路径,默认为 config/default.yaml
        
    Returns:
        Config: 配置对象
    """
    if not config_path:
        config_path = os.path.join("config", "default.yaml")
        
    if not os.path.exists(config_path):
        # 如果配置文件不存在,加载模板并创建默认配置
        template_path = config_path + ".template"
        if os.path.exists(template_path):
            with open(template_path, encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            # 保存默认配置    
            with open(config_path, "w", encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False)
        else:
            config_data = {}
    else:
        # 加载已有配置
        with open(config_path, encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
            
    # 创建配置对象
    config = Config()
    
    # 使用配置文件更新默认值
    for key, value in config_data.items():
        if hasattr(config, key):
            setattr(config, key, value)
            
    return config