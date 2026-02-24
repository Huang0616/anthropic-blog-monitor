import httpx
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re


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
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        """解析日期字符串"""
        if not date_str:
            return None
        
        # 尝试多种日期格式
        formats = [
            "%Y-%m-%d",
            "%B %d, %Y",
            "%b %d, %Y",
            "%Y年%m月%d日",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        
        return None
    
    async def scrape_engineering(self) -> List[Dict]:
        """爬取 Engineering 博客"""
        url = f"{self.base_url}/engineering"
        html = await self.fetch_page(url)
        if not html:
            return []
        
        articles = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # 查找文章卡片
        article_cards = soup.find_all('a', href=re.compile(r'/engineering/'))
        
        for card in article_cards[:20]:  # 限制数量
            href = card.get('href', '')
            if not href or href.startswith('#'):
                continue
            
            # 获取完整 URL
            full_url = href if href.startswith('http') else f"{self.base_url}{href}"
            
            # 提取标题
            title_elem = card.find(['h1', 'h2', 'h3', 'p'])
            title = title_elem.get_text(strip=True) if title_elem else "无标题"
            
            if title and len(title) > 10:  # 过滤太短的标题
                articles.append({
                    "title": title,
                    "url": full_url,
                    "source": "engineering",
                    "published_date": None
                })
        
        return articles
    
    async def scrape_news(self) -> List[Dict]:
        """爬取 News 页面"""
        url = f"{self.base_url}/news"
        html = await self.fetch_page(url)
        if not html:
            return []
        
        articles = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # 查找文章链接
        article_links = soup.find_all('a', href=re.compile(r'/news/'))
        
        for link in article_links[:20]:
            href = link.get('href', '')
            if not href or href.startswith('#'):
                continue
            
            full_url = href if href.startswith('http') else f"{self.base_url}{href}"
            
            # 提取标题
            title_elem = link.find(['h1', 'h2', 'h3', 'p'])
            title = title_elem.get_text(strip=True) if title_elem else "无标题"
            
            if title and len(title) > 10:
                articles.append({
                    "title": title,
                    "url": full_url,
                    "source": "news",
                    "published_date": None
                })
        
        return articles
    
    async def scrape_article_content(self, url: str) -> Optional[str]:
        """获取文章正文内容"""
        html = await self.fetch_page(url)
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # 查找主要内容区域
        content_areas = []
        
        # 尝试多种选择器
        for selector in ['article', 'main', '.content', '.post-content', '[role="main"]']:
            elements = soup.select(selector)
            for elem in elements:
                content_areas.append(elem)
        
        # 如果没有找到特定区域，使用 body
        if not content_areas:
            content_areas = [soup.find('body')]
        
        # 提取文本
        texts = []
        for area in content_areas:
            if area:
                # 移除脚本和样式
                for tag in area(['script', 'style', 'nav', 'footer', 'header']):
                    tag.decompose()
                texts.append(area.get_text(separator='\n', strip=True))
        
        content = '\n'.join(texts)
        
        # 清理空白行
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        return '\n'.join(lines[:500])  # 限制长度
    
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
        
        # 获取详细内容
        for article in unique_articles[:10]:  # 限制数量避免超时
            content = await self.scrape_article_content(article['url'])
            article['content'] = content
        
        return unique_articles
