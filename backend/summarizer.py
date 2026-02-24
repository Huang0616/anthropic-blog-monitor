import httpx
import json
from pathlib import Path
from typing import Optional


class Summarizer:
    """文章摘要生成器"""
    
    def __init__(self):
        self.api_config = self._load_openclaw_config()
    
    def _load_openclaw_config(self) -> dict:
        """从 OpenClaw 配置加载大模型 API 配置"""
        config_path = Path.home() / ".openclaw" / "openclaw.json"
        
        if not config_path.exists():
            print(f"警告：未找到 OpenClaw 配置文件 {config_path}")
            return {
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "api_key": "",
                "model": "qwen-plus"
            }
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 从 models.providers 中获取 custom-coding-dashscope-aliyuncs-com 配置
            providers = config.get('models', {}).get('providers', {})
            dashscope_config = providers.get('custom-coding-dashscope-aliyuncs-com', {})
            
            if dashscope_config:
                api_key = dashscope_config.get('apiKey', '')
                base_url = dashscope_config.get('baseUrl', 'https://coding.dashscope.aliyuncs.com/v1')
                
                # 查找 qwen3.5-plus 模型
                models = dashscope_config.get('models', [])
                model_id = 'qwen3.5-plus'
                for m in models:
                    if 'qwen' in m.get('id', '').lower() and 'plus' in m.get('id', '').lower():
                        model_id = m['id']
                        break
                
                print(f"✅ 已加载 OpenClaw 配置：{base_url} / {model_id}")
                return {
                    "base_url": base_url.rstrip('/'),
                    "api_key": api_key,
                    "model": model_id
                }
            
            print("警告：未找到 Dashscope 配置，使用默认配置")
            return {
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "api_key": "",
                "model": "qwen-plus"
            }
            
        except Exception as e:
            print(f"加载 OpenClaw 配置失败：{e}")
            return {
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "api_key": "",
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
