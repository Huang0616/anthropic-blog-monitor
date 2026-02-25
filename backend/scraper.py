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
        """获取文章内容 - Jina Reader 方案"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 使用 Jina Reader 直接获取纯净文本
                resp = await client.get(f"https://r.jina.ai/{url}")
                resp.raise_for_status()
                content = resp.text.strip()
                
                if len(content) > 100:
                    print(f"  ✓ Jina Reader 成功 ({len(content)} 字符)")
                    return content[:5000]  # 返回更多内容给模型
                return None
        except Exception as e:
            print(f"  ✗ Jina Reader 失败：{e}")
            return None
    
    async def scrape_one_article(self, existing_urls: set) -> Optional[Dict]:
        """只抓取一篇新文章"""
        print("=" * 60)
        print("开始抓取单篇文章...")
        print("=" * 60)
        
        # 先尝试 Engineering 页面
        eng_articles = await self.scrape_engineering()
        for article in eng_articles:
            if article['url'] not in existing_urls:
                print(f"发现新文章 (Engineering): {article['title']}")
                content = await self.scrape_article_content(article['url'])
                article['content'] = content
                print(f"内容获取：{'✓' if content else '✗'}")
                print("=" * 60)
                return article
        
        # 再尝试 News 页面
        news_articles = await self.scrape_news()
        for article in news_articles:
            if article['url'] not in existing_urls:
                print(f"发现新文章 (News): {article['title']}")
                content = await self.scrape_article_content(article['url'])
                article['content'] = content
                print(f"内容获取：{'✓' if content else '✗'}")
                print("=" * 60)
                return article
        
        print("未发现新文章")
        print("=" * 60)
        return None
    
    async def scrape_all(self, months: int = 3) -> List[Dict]:
        """爬取所有文章（保留向后兼容）"""
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
