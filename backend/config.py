import os
import json
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # 数据库配置
    POSTGRES_USER: str = "anthropic_blog"
    POSTGRES_PASSWORD: str = "anthropic_blog_pass"
    POSTGRES_DB: str = "anthropic_blog"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    
    # API 配置
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # 飞书推送配置
    FEISHU_WEBHOOK: Optional[str] = None
    
    # 定时任务配置
    SCRAPE_INTERVAL_HOURS: int = 24
    
    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def async_database_url(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


class OpenClawConfig:
    """读取本地 OpenClaw 配置获取大模型 API 信息"""
    
    def __init__(self):
        self.config_path = Path.home() / ".openclaw" / "config.json"
        self.models_path = Path.home() / ".openclaw" / "models.json"
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        """加载 OpenClaw 配置"""
        config = {}
        
        # 尝试加载 config.json
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config['main'] = json.load(f)
            except Exception as e:
                print(f"加载 config.json 失败：{e}")
        
        # 尝试加载 models.json
        if self.models_path.exists():
            try:
                with open(self.models_path, 'r', encoding='utf-8') as f:
                    config['models'] = json.load(f)
            except Exception as e:
                print(f"加载 models.json 失败：{e}")
        
        return config
    
    def get_model_api_config(self, model_name: str = "qwen") -> Optional[dict]:
        """
        获取指定模型的 API 配置
        返回：{"base_url": "...", "api_key": "...", "model": "..."}
        """
        # 从 models.json 中查找
        models = self.config.get('models', {})
        
        # 查找包含 qwen 的模型配置
        for key, value in models.items():
            if isinstance(value, str) and ('qwen' in value.lower() or 'qwen' in key.lower()):
                # 这是一个模型映射
                model_id = value
                # 尝试从 main config 中获取 API 配置
                main_config = self.config.get('main', {})
                
                # 查找 API key 和 base_url
                api_key = None
                base_url = None
                
                # 常见的配置位置
                if 'api_key' in main_config:
                    api_key = main_config['api_key']
                if 'api_base' in main_config:
                    base_url = main_config['api_base']
                if 'base_url' in main_config:
                    base_url = main_config['base_url']
                
                if api_key and base_url:
                    return {
                        "base_url": base_url.rstrip('/'),
                        "api_key": api_key,
                        "model": model_id
                    }
        
        # 如果没找到，返回默认的 dashscope 配置
        return None


settings = Settings()
openclaw_config = OpenClawConfig()
