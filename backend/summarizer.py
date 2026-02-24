import httpx
import json
from pathlib import Path
from typing import Optional
from datetime import datetime


class Summarizer:
    """文章摘要生成器 - 快速版"""
    
    def __init__(self):
        self.api_config = self._load_openclaw_config()
    
    def _load_openclaw_config(self) -> dict:
        config_path = Path.home() / ".openclaw" / "openclaw.json"
        if not config_path.exists():
            return {"base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "api_key": "", "model": "qwen-plus"}
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            providers = config.get('models', {}).get('providers', {})
            ds = providers.get('custom-coding-dashscope-aliyuncs-com', {})
            if ds:
                return {
                    "base_url": ds.get('baseUrl', '').rstrip('/'),
                    "api_key": ds.get('apiKey', ''),
                    "model": 'qwen3.5-plus'
                }
        except Exception as e:
            print(f"配置加载失败：{e}")
        
        return {"base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "api_key": "", "model": "qwen-plus"}
    
    async def summarize(self, title: str, content: str) -> Optional[str]:
        if not content or len(content.strip()) < 50:
            return f"📝 {title}"
        
        prompt = f"用 200 字概括：{title}\n\n内容：{content[:2000]}"
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{self.api_config['base_url']}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_config['api_key']}", "Content-Type": "application/json"},
                    json={
                        "model": self.api_config['model'],
                        "messages": [
                            {"role": "system", "content": "用中文简洁概括文章。"},
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 300,
                        "temperature": 0.5
                    }
                )
                resp.raise_for_status()
                data = resp.json()
                if data.get('choices'):
                    return data['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"摘要失败：{e}")
        
        return None
