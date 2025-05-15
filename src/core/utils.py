from loguru import logger
import sys
from pathlib import Path
from typing import Optional, cast, Any
import os

def setup_logging(module_name: str, log_level: Optional[str] = None) -> Any:
    """设置日志配置
    
    Args:
        module_name: 模块名称
        log_level: 日志级别，默认为 None，将使用环境变量或默认值
        
    Returns:
        logger: 配置好的日志记录器
    """
    # 移除默认处理器
    logger.remove()
    
    # 创建日志目录
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 获取日志级别
    log_level = log_level or os.getenv("LOG_LEVEL", "INFO")
    
    # 添加控制台处理器
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
               "<level>{message}</level>",
        filter=lambda record: record["extra"].get("name", "") == module_name
    )
    
    # 添加文件处理器
    log_file = log_dir / f"{module_name}.log"
    logger.add(
        str(log_file),
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation="00:00",  # 每天轮换
        retention="7 days",  # 保留7天
        compression="zip",  # 压缩旧日志
        encoding="utf-8",
        filter=lambda record: record["extra"].get("name", "") == module_name
    )
    
    return logger.bind(name=module_name)
