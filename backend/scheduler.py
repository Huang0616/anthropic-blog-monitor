from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import Callable
import asyncio

from scraper import AnthropicScraper
from summarizer import Summarizer
from notifier import FeishuNotifier
from models import Article
from config import settings


class BlogScheduler:
    """定时任务调度器"""
    
    def __init__(self, db_session_factory: Callable):
        self.scheduler = AsyncIOScheduler()
        self.db_session_factory = db_session_factory
        self.scraper = AnthropicScraper()
        self.summarizer = Summarizer()
        self.notifier = FeishuNotifier()
        self.is_running = False
    
    async def scrape_and_process(self):
        """爬取并处理新文章"""
        print(f"[{datetime.now()}] 开始爬取文章...")
        
        try:
            # 爬取文章
            articles = await self.scraper.scrape_all(months=3)
            print(f"爬取到 {len(articles)} 篇文章")
            
            async with self.db_session_factory() as session:
                for article_data in articles:
                    # 检查是否已存在
                    result = await session.execute(
                        select(Article).where(Article.url == article_data['url'])
                    )
                    existing = result.scalar_one_or_none()
                    
                    if existing:
                        continue  # 已存在，跳过
                    
                    # 生成摘要
                    summary = await self.summarizer.summarize(
                        title=article_data['title'],
                        content=article_data.get('content', '')
                    )
                    
                    # 创建新文章记录
                    new_article = Article(
                        title=article_data['title'],
                        url=article_data['url'],
                        published_date=article_data.get('published_date'),
                        content=article_data.get('content', ''),
                        summary=summary,
                        notified=False
                    )
                    
                    session.add(new_article)
                    print(f"添加新文章：{new_article.title}")
                    
                    # 推送通知
                    if summary and self.notifier.webhook_url:
                        await self.notifier.send_article_notification(
                            title=new_article.title,
                            summary=summary,
                            url=new_article.url
                        )
                        new_article.notified = True
                
                await session.commit()
                print(f"[{datetime.now()}] 文章处理完成")
                
        except Exception as e:
            print(f"爬取处理失败：{e}")
            import traceback
            traceback.print_exc()
    
    def start(self):
        """启动调度器"""
        # 添加定时任务：每天上午 9 点执行
        self.scheduler.add_job(
            self.scrape_and_process,
            CronTrigger(hour=9, minute=0),
            id='daily_scrape',
            name='每日文章爬取'
        )
        
        self.scheduler.start()
        self.is_running = True
        print(f"调度器已启动，下次执行时间：{self.scheduler.get_job('daily_scrape').next_run_time}")
    
    def stop(self):
        """停止调度器"""
        self.scheduler.shutdown()
        self.is_running = False
        print("调度器已停止")
