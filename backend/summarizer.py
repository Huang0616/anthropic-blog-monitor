import httpx
import json
from pathlib import Path
from typing import Optional
from datetime import datetime


class Summarizer:
    """文章摘要生成器 - 使用 GLM-5 模型"""
    
    def __init__(self):
        self.api_config = {
            "base_url": "https://open.bigmodel.cn/api/paas/v4",
            "api_key": "261121ef2efb430e98acce303dadc547.9oO35c61oR4T8E8l",
            "model": "glm-5"
        }
    
    async def summarize(self, title: str, content: str) -> Optional[str]:
        if not content or len(content.strip()) < 50:
            return f"📝 {title}"
        
        prompt = f"用 200 字概括：{title}\n\n内容：{content[:2000]}"
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    f"{self.api_config['base_url']}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_config['api_key']}", "Content-Type": "application/json"},
                    json={
                        "model": self.api_config['model'],
                        "messages": [
                            {"role": "system", "content": "用中文简洁概括文章。"},
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 100000,
                        "temperature": 0.5
                    }
                )
                resp.raise_for_status()
                data = resp.json()
                
                if data.get('choices'):
                    message = data['choices'][0]['message']
                    # 优先使用 content，如果为空则使用 reasoning_content
                    result = message.get('content') or message.get('reasoning_content')
                    if result:
                        return result.strip()
                    
        except Exception as e:
            print(f"摘要失败：{e}")
            import traceback
            traceback.print_exc()
        
        return None
