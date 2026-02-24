import httpx
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import re
import asyncio
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


class AnthropicScraper:
    """Anthropic 博客爬虫 - 简化版"""
    
    def __init__(self):
        self.base_url = "https://www.anthropic.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def fetch_page(self, url: str) -> Optional[str]:
        """获取页面内容"""
        async with httpx.AsyncClient(headers=self.headers, timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text
    
    async def scrape_engineering(self) -> List[Dict]:
        """爬取 Engineering 博客"""
        url = f"{self.base_url}/engineering"
        html = await self.fetch_page(url)
        if not html:
            return []
        
        articles = []
        soup = BeautifulSoup(html, 'html.parser')
        
        for card in soup.find_all('a', href=re.compile(r'/engineering/[^/]+$'))[:15]:
            href = card.get('href', '')
            if not href or href == '/engineering':
                continue
            
            title = card.get_text(strip=True)
            if not title:
                title = href.split('/')[-1].replace('-', ' ').title()
            
            articles.append({
                "title": title,
                "url": f"{self.base_url}{href}",
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
        
        for card in soup.find_all('a', href=re.compile(r'/news/[^/]+$'))[:10]:
            href = card.get('href', '')
            if not href or href == '/news':
                continue
            
            title = card.get_text(strip=True)
            if not title:
                title = href.split('/')[-1].replace('-', ' ').title()
            
            articles.append({
                "title": title,
                "url": f"{self.base_url}{href}",
                "source": "news",
                "published_date": None
            })
        
        return articles
    
    async def scrape_article_content(self, url: str) -> Optional[str]:
        """获取文章内容 - 简化版"""
        html = await self.fetch_page(url)
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # 提取所有段落
        paragraphs = soup.find_all('p')
        if paragraphs:
            content = ' '.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
            if len(content) > 100:
                return content[:3000]
        
        # 备用：提取所有文本
        text = soup.get_text(separator=' ', strip=True)
        return text[:3000] if len(text) > 200 else None
    
    async def scrape_all(self, months: int = 3) -> List[Dict]:
        """爬取所有文章"""
        print("=" * 60)
        print("开始爬取 Anthropic 博客...")
        print("=" * 60)
        
        eng = await self.scrape_engineering()
        print(f"Engineering: {len(eng)} 篇")
        
        news = await self.scrape_news()
        print(f"News: {len(news)} 篇")
        
        # 合并去重
        all_articles = eng + news
        seen = set()
        unique = []
        for a in all_articles:
            if a['url'] not in seen:
                seen.add(a['url'])
                unique.append(a)
        
        print(f"去重后：{len(unique)} 篇")
        print("\n获取内容...")
        
        # 获取内容（带速率限制）
        for i, article in enumerate(unique[:10]):
            if i > 0:
                await asyncio.sleep(1)
            content = await self.scrape_article_content(article['url'])
            article['content'] = content
            print(f"[{i+1}/10] {article['title'][:50]}... {'✓' if content else '✗'}")
        
        print("\n" + "=" * 60)
        return unique
