import httpx
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import re
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


class AnthropicScraper:
    """Anthropic 博客爬虫"""
    
    def __init__(self):
        self.base_url = "https://www.anthropic.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
        }
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError))
    )
    async def fetch_page(self, url: str) -> Optional[str]:
        """获取页面内容 - 带重试机制"""
        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.text
        except httpx.HTTPStatusError as e:
            print(f"HTTP 错误 {url}: {e.response.status_code}")
            return None
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
        """获取文章正文内容 - 增强版"""
        html = await self.fetch_page(url)
        if not html:
            return None
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # 方案 1: 尝试提取 Next.js 构建数据 (__NEXT_DATA__)
            next_data_script = soup.find('script', id='__NEXT_DATA__')
            if next_data_script and next_data_script.string:
                try:
                    next_data = json.loads(next_data_script.string)
                    props = next_data.get('props', {})
                    page_props = props.get('pageProps', {})
                    # 尝试多种可能的内容字段
                    content = (
                        page_props.get('content') or 
                        page_props.get('body') or 
                        page_props.get('article', {}).get('content') or
                        page_props.get('post', {}).get('content')
                    )
                    if content:
                        cleaned = self._clean_html_content(str(content))
                        if len(cleaned) > 100:
                            print(f"  ✓ 从 __NEXT_DATA__ 提取内容成功 ({len(cleaned)} 字符)")
                            return cleaned
                except (json.JSONDecodeError, KeyError, AttributeError) as e:
                    print(f"  解析 __NEXT_DATA__ 失败：{e}")
            
            # 方案 2: 查找文章容器
            article_container = soup.find('article') or soup.find('main')
            if article_container:
                # 移除不需要的元素
                for elem in article_container.find_all(['nav', 'header', 'footer', 'aside', 'script', 'style']):
                    elem.decompose()
                
                # 提取段落
                paragraphs = article_container.find_all('p')
                if paragraphs:
                    content = ' '.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
                    if len(content) > 100:
                        cleaned = ' '.join(content.split())
                        print(f"  ✓ 从 article 标签提取内容成功 ({len(cleaned)} 字符)")
                        return cleaned[:3000]
            
            # 方案 3: 查找常见内容容器 class
            content_classes = ['content', 'article-content', 'post-content', 'body', 'entry-content']
            for class_name in content_classes:
                content_div = soup.find(class_=class_name)
                if content_div:
                    content = content_div.get_text(separator=' ', strip=True)
                    if len(content) > 100:
                        print(f"  ✓ 从 class='{class_name}' 提取内容成功 ({len(content)} 字符)")
                        return content[:3000]
            
            # 方案 4: 使用 meta description 作为后备
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                desc = meta_desc['content'].strip()
                if len(desc) > 50:
                    print(f"  ✓ 从 meta description 提取内容 ({len(desc)} 字符)")
                    return desc
            
            # 方案 5: 提取所有文本（最后的手段）
            text_content = soup.get_text(separator=' ', strip=True)
            if len(text_content) > 200:
                print(f"  ✓ 使用全文提取 ({len(text_content)} 字符)")
                return text_content[:3000]
            
            print(f"  ✗ 无法提取内容")
            return None
            
        except Exception as e:
            print(f"  解析 HTML 失败：{e}")
            return None
    
    def _clean_html_content(self, content: str) -> str:
        """清理 HTML 内容"""
        # 移除 HTML 标签
        soup = BeautifulSoup(content, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)
        # 清理空白字符
        text = ' '.join(text.split())
        return text[:3000]
    
    async def scrape_all(self, months: int = 3) -> List[Dict]:
        """爬取所有文章 - 带速率限制"""
        import asyncio
        
        all_articles = []
        
        print("=" * 60)
        print("开始爬取 Anthropic 博客...")
        print("=" * 60)
        
        # 爬取 Engineering
        print("\n[1/2] 爬取 Engineering 博客...")
        eng_articles = await self.scrape_engineering()
        print(f"  找到 {len(eng_articles)} 篇文章")
        all_articles.extend(eng_articles)
        
        # 爬取 News
        print("\n[2/2] 爬取 News 页面...")
        news_articles = await self.scrape_news()
        print(f"  找到 {len(news_articles)} 篇文章")
        all_articles.extend(news_articles)
        
        # 去重（基于 URL）
        seen_urls = set()
        unique_articles = []
        for article in all_articles:
            if article['url'] not in seen_urls:
                seen_urls.add(article['url'])
                unique_articles.append(article)
        
        print(f"\n去重后共 {len(unique_articles)} 篇文章")
        
        # 获取详细内容（限制数量避免超时，添加速率限制）
        print("\n开始获取文章详细内容...")
        for i, article in enumerate(unique_articles[:10]):
            # 速率限制：每篇文章间隔 2 秒
            if i > 0:
                await asyncio.sleep(2)
            
            print(f"\n[{i+1}/{min(10, len(unique_articles))}] {article['title'][:60]}...")
            content = await self.scrape_article_content(article['url'])
            article['content'] = content
            if content:
                print(f"  ✓ 成功获取内容 ({len(content)} 字符)")
            else:
                print(f"  ✗ 内容获取失败")
        
        print("\n" + "=" * 60)
        print(f"爬取完成！共处理 {len(unique_articles)} 篇文章")
        print("=" * 60)
        
        return unique_articles
