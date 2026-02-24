import httpx
from typing import Optional
from config import openclaw_config


class Summarizer:
    """文章摘要生成器"""
    
    def __init__(self):
        self.api_config = openclaw_config.get_model_api_config("qwen")
        
        # 如果没有找到配置，使用默认的 Dashscope 配置
        if not self.api_config:
            print("警告：未找到 OpenClaw 配置，使用默认 Dashscope 配置")
            self.api_config = {
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "api_key": "",  # 需要用户设置
                "model": "qwen-plus"
            }
    
    async def summarize(self, title: str, content: str, max_length: int = 500) -> Optional[str]:
        """
        生成文章摘要
        
        Args:
            title: 文章标题
            content: 文章内容
            max_length: 摘要最大长度
        
        Returns:
            摘要文本，失败返回 None
        """
        if not content:
            return None
        
        # 截取内容（避免 token 超限）
        truncated_content = content[:3000]
        
        prompt = f"""请为以下文章生成一个简洁的中文摘要（300 字以内）：

文章标题：{title}

文章内容：
{truncated_content}

请用中文输出摘要，包含文章的核心观点和主要结论。"""

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.api_config['base_url']}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_config['api_key']}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.api_config['model'],
                        "messages": [
                            {
                                "role": "system",
                                "content": "你是一个专业的技术文章摘要助手，擅长提取文章核心内容并生成简洁的中文摘要。"
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "max_tokens": 500,
                        "temperature": 0.7
                    }
                )
                
                response.raise_for_status()
                data = response.json()
                
                if data.get('choices') and len(data['choices']) > 0:
                    summary = data['choices'][0]['message']['content']
                    return summary.strip()
                else:
                    print(f"API 返回异常：{data}")
                    return None
                    
        except Exception as e:
            print(f"生成摘要失败：{e}")
            return None
