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
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print("\n" + "=" * 60)
        print(f"[{timestamp}] 🚀 开始爬取并处理文章...")
        print("=" * 60)
        
        new_count = 0
        success_count = 0
        
        try:
            # 爬取文章
            articles = await self.scraper.scrape_all(months=3)
            
            async with self.db_session_factory() as session:
                for article_data in articles:
                    # 检查是否已存在
                    result = await session.execute(
                        select(Article).where(Article.url == article_data['url'])
                    )
                    existing = result.scalar_one_or_none()
                    
                    if existing:
                        print(f"⏭️  跳过已存在：{article_data['title'][:50]}...")
                        continue  # 已存在，跳过
                    
                    new_count += 1
                    
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
                    print(f"✅ 添加新文章：{new_article.title[:60]}...")
                    success_count += 1
                    
                    # 推送通知
                    if summary and self.notifier.webhook_url:
                        print(f"📤 发送飞书推送...")
                        await self.notifier.send_article_notification(
                            title=new_article.title,
                            summary=summary,
                            url=new_article.url
                        )
                        new_article.notified = True
                    elif summary and not self.notifier.webhook_url:
                        print(f"⚠️  跳过推送（未配置 Webhook）")
                
                await session.commit()
                
        except Exception as e:
            print(f"\n❌ 爬取处理失败：{e}")
            import traceback
            traceback.print_exc()
            raise
        
        finally:
            end_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print("\n" + "=" * 60)
            print(f"[{end_timestamp}] 📊 处理完成统计:")
            print(f"  - 爬取文章总数：{len(articles)}")
            print(f"  - 新增文章：{new_count}")
            print(f"  - 成功处理：{success_count}")
            print("=" * 60)
    
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
