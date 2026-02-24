import httpx
import json
from pathlib import Path
from typing import Optional
from datetime import datetime


class Summarizer:
    """文章摘要生成器 - 直接访问 URL 模式"""
    
    def __init__(self):
        self.api_config = self._load_openclaw_config()
        self.request_count = 0
    
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
            
            providers = config.get('models', {}).get('providers', {})
            dashscope_config = providers.get('custom-coding-dashscope-aliyuncs-com', {})
            
            if dashscope_config:
                api_key = dashscope_config.get('apiKey', '')
                base_url = dashscope_config.get('baseUrl', 'https://coding.dashscope.aliyuncs.com/v1')
                
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
    
    async def summarize(self, title: str, url: str, max_length: int = 2000) -> Optional[str]:
        """
        让模型直接访问 URL 并生成摘要 - 流式返回
        
        Args:
            title: 文章标题
            url: 文章 URL（模型会自己访问）
            max_length: 摘要最大长度
        
        Returns:
            摘要文本，失败返回 None
        """
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        self.request_count += 1
        
        prompt = f"""请访问以下链接并总结文章的主要内容：

文章标题：{title}
文章链接：{url}

要求：
1. 详细总结文章的核心内容，不限制字数
2. 提取关键观点和技术细节
3. 使用中文输出
4. 保持专业但易懂的风格
5. 重要信息不要遗漏

请流式返回完整的文章内容总结。"""

        try:
            print(f"[{timestamp}] 🤖 正在请求模型访问 URL 并生成摘要 (请求 #{self.request_count})...")
            print(f"  URL: {url}")
            
            async with httpx.AsyncClient(timeout=180.0) as client:
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
                                "content": "你是一个专业的技术文章分析助手。请直接访问用户提供的 URL，阅读文章内容，然后生成详细的中文总结。不限制字数，要包含文章的核心观点、技术细节和重要信息。"
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "max_tokens": 4000,
                        "temperature": 0.7,
                        "stream": True
                    }
                )
                
                response.raise_for_status()
                
                # 流式处理
                summary_chunks = []
                async for line in response.aiter_lines():
                    if line.startswith('data: '):
                        data = line[6:]
                        if data.strip() == '[DONE]':
                            break
                        try:
                            chunk = json.loads(data)
                            if chunk.get('choices') and len(chunk['choices']) > 0:
                                content = chunk['choices'][0].get('delta', {}).get('content', '')
                                if content:
                                    summary_chunks.append(content)
                        except json.JSONDecodeError:
                            continue
                
                summary = ''.join(summary_chunks).strip()
                
                if summary:
                    print(f"[{timestamp}] ✅ 摘要生成成功 ({len(summary)} 字符)")
                    return summary
                else:
                    print(f"[{timestamp}] ❌ 未生成有效内容")
                    return None
                    
        except httpx.TimeoutException as e:
            print(f"[{timestamp}] ❌ 请求超时：{e}")
            return None
        except Exception as e:
            print(f"[{timestamp}] ❌ 生成摘要失败：{e}")
            return None
