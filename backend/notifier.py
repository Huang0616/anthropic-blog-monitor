import httpx
from typing import Optional
from config import settings


class FeishuNotifier:
    """飞书消息推送"""
    
    def __init__(self):
        self.webhook_url = settings.FEISHU_WEBHOOK
    
    async def send_article_notification(self, title: str, summary: str, url: str) -> bool:
        """
        推送新文章通知
        
        Args:
            title: 文章标题
            summary: 文章摘要
            url: 文章链接
        
        Returns:
            是否发送成功
        """
        if not self.webhook_url:
            print("警告：未配置飞书 Webhook，跳过推送")
            return False
        
        # 构建富文本消息
        content = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": "📰 Anthropic 新文章推送"
                    },
                    "template": "blue"
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**{title}**"
                        }
                    },
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": summary[:500] + "..." if len(summary) > 500 else summary
                        }
                    },
                    {
                        "tag": "action",
                        "actions": [
                            {
                                "tag": "button",
                                "text": {
                                    "tag": "plain_text",
                                    "content": "阅读原文 📖"
                                },
                                "url": url,
                                "type": "primary"
                            }
                        ]
                    }
                ]
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.webhook_url,
                    json=content,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                print(f"推送成功：{title}")
                return True
        except Exception as e:
            print(f"推送失败：{e}")
            return False
