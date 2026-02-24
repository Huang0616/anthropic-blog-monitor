import httpx
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json


class AnthropicScraper:
    """Anthropic 博客爬虫"""
    
    def __init__(self):
        self.base_url = "https://www.anthropic.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    
    async def fetch_page(self, url: str) -> Optional[str]:
        """获取页面内容"""
        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.text
        except Exception as e:
            print(f"获取页面失败 {url}: {e}")
            return None
    
    async def scrape_engineering(self) -> List[Dict]:
        """爬取 Engineering 博客 - 从页面提取文章列表"""
        url = f"{self.base_url}/engineering"
        html = await self.fetch_page(url)
        if not html:
            return []
        
        articles = []
        
        # 从 HTML 中提取文章链接和标题
        # 查找类似：href="/engineering/article-slug"
        import re
        
        # 匹配文章卡片
        pattern = r'href="(/engineering/[^"]+)"'
        matches = re.findall(pattern, html)
        
        seen_slugs = set()
        for slug in matches:
            if slug in seen_slugs or slug.count('/') > 2:
                continue
            seen_slugs.add(slug)
            
            # 提取标题（从附近的文本）
            title_pattern = rf'{re.escape(slug)}[^>]*>([^<]+)'
            title_match = re.search(title_pattern, html)
            title = title_match.group(1).strip() if title_match else slug.split('/')[-1].replace('-', ' ').title()
            
            articles.append({
                "title": title,
                "url": f"{self.base_url}{slug}",
                "source": "engineering",
                "published_date": None
            })
        
        return articles[:15]  # 限制数量
    
    async def scrape_news(self) -> List[Dict]:
        """爬取 News 页面"""
        url = f"{self.base_url}/news"
        html = await self.fetch_page(url)
        if not html:
            return []
        
        articles = []
        import re
        
        # 匹配新闻链接
        pattern = r'href="(/news/[^"]+)"'
        matches = re.findall(pattern, html)
        
        seen_slugs = set()
        for slug in matches:
            if slug in seen_slugs or slug == '/news':
                continue
            seen_slugs.add(slug)
            
            articles.append({
                "title": slug.split('/')[-1].replace('-', ' ').title(),
                "url": f"{self.base_url}{slug}",
                "source": "news",
                "published_date": None
            })
        
        return articles[:10]
    
    async def scrape_article_content(self, url: str) -> Optional[str]:
        """获取文章正文内容"""
        html = await self.fetch_page(url)
        if not html:
            return None
        
        import re
        
        # 1. 尝试提取 meta description
        desc_match = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]+)"', html)
        if desc_match:
            return desc_match.group(1)
        
        # 2. 尝试提取 og:description
        og_match = re.search(r'<meta[^>]+property="og:description"[^>]+content="([^"]+)"', html)
        if og_match:
            return og_match.group(1)
        
        # 3. 从 script 标签中的 JSON 数据提取（Next.js SSR）
        json_match = re.search(r'"summary":"([^"]+)"', html)
        if json_match:
            # 处理转义字符
            summary = json_match.group(1).replace('\\n', ' ').replace('\\"', '"')
            return summary[:2000]
        
        # 4. 尝试提取所有段落文本
        paragraphs = re.findall(r'<p[^>]*>([^<]+)</p>', html)
        if paragraphs:
            content = ' '.join(paragraphs[:10])  # 取前 10 段
            content = ' '.join(content.split())  # 清理空白
            return content[:2000] if len(content) > 50 else None
        
        return None
    
    async def scrape_all(self, months: int = 3) -> List[Dict]:
        """爬取所有文章"""
        all_articles = []
        
        # 爬取 Engineering
        eng_articles = await self.scrape_engineering()
        all_articles.extend(eng_articles)
        
        # 爬取 News
        news_articles = await self.scrape_news()
        all_articles.extend(news_articles)
        
        # 去重（基于 URL）
        seen_urls = set()
        unique_articles = []
        for article in all_articles:
            if article['url'] not in seen_urls:
                seen_urls.add(article['url'])
                unique_articles.append(article)
        
        print(f"爬取到 {len(unique_articles)} 篇文章")
        
        # 获取详细内容（限制数量避免超时）
        for i, article in enumerate(unique_articles[:10]):
            content = await self.scrape_article_content(article['url'])
            article['content'] = content
            print(f"获取内容 {i+1}/{min(10, len(unique_articles))}: {article['title'][:50]}...")
        
        return unique_articles
