import os
import logging
import logging.handlers
from typing import Dict, Optional

class LogConfig:
    """日志配置管理器,单例模式"""
    
    _instance = None
    
    def __init__(self):
        if LogConfig._instance is not None:
            raise RuntimeError("LogConfig是单例类,请使用get_instance()获取实例")
            
        # 默认配置
        self.log_path = "logs"
        self.default_level = logging.INFO
        self.format = "%(asctime)s | %(levelname)s | %(name)s - %(message)s"
        self.date_format = "%Y-%m-%d %H:%M:%S"
        
        # 缓存的logger实例
        self.loggers: Dict[str, logging.Logger] = {}
        
        # 创建日志目录
        if not os.path.exists(self.log_path):
            os.makedirs(self.log_path)
            
    @classmethod
    def get_instance(cls) -> 'LogConfig':
        """获取LogConfig单例"""
        if cls._instance is None:
            cls._instance = LogConfig()
        return cls._instance
        
    def get_logger(self, name: str, filename: Optional[str] = None) -> logging.Logger:
        """获取logger实例
        
        Args:
            name: logger名称
            filename: 日志文件名,默认使用name.log
            
        Returns:
            logging.Logger: 配置好的logger实例
        """
        if name in self.loggers:
            return self.loggers[name]
            
        # 创建logger
        logger = logging.getLogger(name)
        logger.setLevel(self.default_level)
        
        # 创建格式器
        formatter = logging.Formatter(
            fmt=self.format,
            datefmt=self.date_format
        )
        
        # 添加控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 添加文件处理器
        if filename:
            file_path = os.path.join(self.log_path, filename)
            file_handler = logging.handlers.RotatingFileHandler(
                filename=file_path,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
        # 缓存logger实例
        self.loggers[name] = logger
        return logger
        
    def set_level(self, level: int):
        """设置全局日志级别"""
        self.default_level = level
        for logger in self.loggers.values():
            logger.setLevel(level)
            
    def cleanup(self):
        """清理日志处理器"""
        for logger in self.loggers.values():
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)