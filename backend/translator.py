import httpx
from typing import Optional, Dict
from datetime import datetime


class Translator:
    """文章翻译器 - 使用 GLM-4.7-flash 模型"""

    def __init__(self):
        self.api_config = {
            "base_url": "https://open.bigmodel.cn/api/coding/paas/v4",
            "api_key": "a18ad9d58bea4ebeaf24f5c48e47e648.YRzUI6jSN2ODgf3F",
            "model": "glm-4.7-flash"
        }

    async def translate(self, title: str, summary: str) -> Optional[Dict[str, str]]:
        """
        翻译标题和摘要为中文

        Args:
            title: 英文标题
            summary: 英文摘要

        Returns:
            包含翻译后的标题和摘要的字典，格式：{"title": "xxx", "summary": "xxx"}
            失败时返回 None
        """
        if not title and not summary:
            return None

        prompt = f"""将以下英文标题和摘要翻译成流畅的中文。直接输出翻译结果，格式：标题：xxx
摘要：xxx

标题：{title}

摘要：{summary}"""

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    f"{self.api_config['base_url']}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_config['api_key']}", "Content-Type": "application/json"},
                    json={
                        "model": self.api_config['model'],
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 100000,
                        "temperature": 0.3
                    }
                )
                resp.raise_for_status()
                data = resp.json()

                if data.get('choices'):
                    result_text = data['choices'][0]['message']['content'].strip()
                    # 解析结果
                    return self._parse_translation(result_text)

        except Exception as e:
            print(f"翻译失败：{e}")
            import traceback
            traceback.print_exc()

        return None

    async def translate_full_content(self, title: str, summary: str, content: str) -> Optional[Dict[str, str]]:
        """
        翻译全文内容（标题 + 摘要 + 全文），使用流式请求避免超时

        Args:
            title: 英文标题
            summary: 英文摘要
            content: 英文全文内容

        Returns:
            包含翻译后的标题、摘要和全文的字典，格式：{"title": "xxx", "summary": "xxx", "content": "xxx"}
            失败时返回 None
        """
        if not title and not summary and not content:
            return None

        prompt = f"""将以下英文内容翻译成流畅的中文。直接输出翻译结果，格式：
标题：xxx
摘要：xxx
全文：xxx

标题：{title}

摘要：{summary or '无'}

全文：
{content or '无'}"""

        try:
            print("🌐 开始流式翻译全文...")
            full_response = []

            async with httpx.AsyncClient(timeout=300.0) as client:
                # 使用流式请求
                async with client.stream(
                    "POST",
                    f"{self.api_config['base_url']}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_config['api_key']}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.api_config['model'],
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 100000,
                        "temperature": 0.3,
                        "stream": True  # 启用流式输出
                    }
                ) as response:
                    response.raise_for_status()

                    # 处理流式响应
                    async for line in response.aiter_lines():
                        if line.startswith('data: '):
                            data_str = line[6:]  # 去掉 'data: ' 前缀
                            if data_str.strip() == '[DONE]':
                                break
                            try:
                                import json
                                data = json.loads(data_str)
                                if data.get('choices') and len(data['choices']) > 0:
                                    delta = data['choices'][0].get('delta', {})
                                    content_chunk = delta.get('content', '')
                                    if content_chunk:
                                        full_response.append(content_chunk)
                            except json.JSONDecodeError:
                                continue

            # 合并完整响应
            result_text = ''.join(full_response)
            print(f"✅ 流式翻译完成，总长度：{len(result_text)} 字符")

            # 解析结果
            return self._parse_full_translation(result_text)

        except Exception as e:
            print(f"全文翻译失败：{e}")
            import traceback
            traceback.print_exc()

        return None

    def _parse_full_translation(self, text: str) -> Optional[Dict[str, str]]:
        """
        解析全文翻译结果

        预期格式：
        标题：xxx
        摘要：xxx
        全文：xxx
        """
        try:
            lines = text.strip().split('\n')
            result = {"title": "", "summary": "", "content": ""}

            current_key = None
            current_value = []

            for line in lines:
                if line.startswith('标题：') or line.startswith('标题:'):
                    if current_key and current_value:
                        result[current_key] = '\n'.join(current_value).strip()
                    current_key = "title"
                    current_value = [line.split('：', 1)[-1].split(':', 1)[-1].strip()]
                elif line.startswith('摘要：') or line.startswith('摘要:'):
                    if current_key and current_value:
                        result[current_key] = '\n'.join(current_value).strip()
                    current_key = "summary"
                    current_value = [line.split('：', 1)[-1].split(':', 1)[-1].strip()]
                elif line.startswith('全文：') or line.startswith('全文:'):
                    if current_key and current_value:
                        result[current_key] = '\n'.join(current_value).strip()
                    current_key = "content"
                    current_value = [line.split('：', 1)[-1].split(':', 1)[-1].strip()]
                elif current_key:
                    current_value.append(line)

            # 处理最后一个字段
            if current_key and current_value:
                result[current_key] = '\n'.join(current_value).strip()

            # 确保至少有一个字段有值
            if result["title"] or result["summary"] or result["content"]:
                return result

        except Exception as e:
            print(f"解析全文翻译结果失败：{e}")

        return None
    
    def _parse_translation(self, text: str) -> Optional[Dict[str, str]]:
        """
        解析翻译结果
        
        预期格式：
        标题：xxx
        摘要：xxx
        """
        try:
            lines = text.strip().split('\n')
            result = {"title": "", "summary": ""}
            
            current_key = None
            current_value = []
            
            for line in lines:
                if line.startswith('标题：') or line.startswith('标题:'):
                    if current_key and current_value:
                        result[current_key] = '\n'.join(current_value).strip()
                    current_key = "title"
                    current_value = [line.split('：', 1)[-1].split(':', 1)[-1].strip()]
                elif line.startswith('摘要：') or line.startswith('摘要:'):
                    if current_key and current_value:
                        result[current_key] = '\n'.join(current_value).strip()
                    current_key = "summary"
                    current_value = [line.split('：', 1)[-1].split(':', 1)[-1].strip()]
                elif current_key:
                    current_value.append(line)
            
            # 处理最后一个字段
            if current_key and current_value:
                result[current_key] = '\n'.join(current_value).strip()
            
            # 确保两个字段都有值
            if result["title"] or result["summary"]:
                return result
                
        except Exception as e:
            print(f"解析翻译结果失败：{e}")
        
        return None
