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
        # 使用 GLM-4.7 模型
        return {
            "base_url": "https://open.bigmodel.cn/api/coding/paas/v4",
            "api_key": "a18ad9d58bea4ebeaf24f5c48e47e648.YRzUI6jSN2ODgf3F",
            "model": "glm-4.7"
        }
    
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
