import httpx
from typing import Optional, Dict
from datetime import datetime
from config import settings


class FeishuNotifier:
    """飞书消息推送"""
    
    def __init__(self):
        self.webhook_url = settings.FEISHU_WEBHOOK

    def _is_success_response(self, response: httpx.Response) -> bool:
        """校验飞书 webhook 返回值，避免把业务失败误判为成功。"""
        try:
            payload = response.json()
        except ValueError:
            print(f"推送失败：飞书返回了非 JSON 响应，status={response.status_code}")
            return False

        status_code = payload.get("StatusCode")
        code = payload.get("code")

        if status_code not in (None, 0) or code not in (None, 0):
            print(f"推送失败：飞书返回错误，status={response.status_code} body={payload}")
            return False

        return True
    
    async def send_article_notification(self, title: str, summary: str, url: str, translation: Optional[Dict[str, str]] = None) -> bool:
        """
        推送新文章通知
        
        Args:
            title: 文章标题（英文）
            summary: 文章摘要（英文）
            url: 文章链接
            translation: 翻译结果（包含 title 和 summary）
        
        Returns:
            是否发送成功
        """
        if not self.webhook_url:
            print("警告：未配置飞书 Webhook，跳过推送")
            return False
        
        # 构建卡片元素
        elements = []
        
        # 标题（优先显示翻译后的标题）
        if translation and translation.get('title'):
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**{translation['title']}**"
                }
            })
            # 原标题（折叠显示）
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"原标题：{title}"
                }
            })
        else:
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**{title}**"
                }
            })
        
        # 摘要（优先显示翻译后的摘要）
        if translation and translation.get('summary'):
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"📝 **中文摘要：**\n{translation['summary']}"
                }
            })
            # 英文摘要（折叠显示）
            if summary:
                elements.append({
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"---\n**English Summary:**\n{summary[:500]}{'...' if len(summary) > 500 else ''}"
                    }
                })
        elif summary:
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": summary[:500] + "..." if len(summary) > 500 else summary
                }
            })
        
        # 阅读按钮
        elements.append({
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
        })
        
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
                "elements": elements
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
                if not self._is_success_response(response):
                    return False
                print(f"推送成功：{title}")
                return True
        except Exception as e:
            print(f"推送失败：{e}")
            return False
    
    async def send_status_report(self, total_articles: int, last_check: datetime, latest_article: Optional[Dict] = None) -> bool:
        """
        推送系统状态报告
        
        Args:
            total_articles: 已监控文章总数
            last_check: 最后检查时间
            latest_article: 最新文章信息（包含 title, published_date）
        
        Returns:
            是否发送成功
        """
        if not self.webhook_url:
            print("警告：未配置飞书 Webhook，跳过推送")
            return False
        
        # 构建状态报告内容
        content_lines = [
            f"📊 **已监控文章总数：** {total_articles}",
            f"⏰ **最后检查时间：** {last_check.strftime('%Y-%m-%d %H:%M:%S')}",
        ]
        
        if latest_article:
            published_str = latest_article.get('published_date', '未知')
            if isinstance(published_str, datetime):
                published_str = published_str.strftime('%Y-%m-%d %H:%M:%S')
            content_lines.append(f"📄 **最新文章：** {latest_article.get('title', '未知')}")
            content_lines.append(f"📅 **发布时间：** {published_str}")
        
        content_lines.append("✅ **系统状态：** 运行正常")
        
        # 构建富文本消息
        content = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": "📊 Anthropic 博客监控 - 系统状态报告"
                    },
                    "template": "green"
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": "\n".join(content_lines)
                        }
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
                if not self._is_success_response(response):
                    return False
                print(f"状态报告推送成功")
                return True
        except Exception as e:
            print(f"状态报告推送失败：{e}")
            return False
