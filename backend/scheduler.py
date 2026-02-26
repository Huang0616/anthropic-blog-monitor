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
from models import Article, ScraperState
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
    
    async def get_last_check_time(self) -> datetime:
        """获取最后检查时间"""
        async with self.db_session_factory() as session:
            result = await session.execute(
                select(ScraperState).where(ScraperState.key == "last_check")
            )
            state = result.scalar_one_or_none()
            
            if state and state.value:
                try:
                    return datetime.fromisoformat(state.value)
                except:
                    pass
            
            # 默认返回 7 天前的时间
            return datetime.now() - timedelta(days=7)
    
    async def update_last_check_time(self, check_time: datetime):
        """更新最后检查时间"""
        async with self.db_session_factory() as session:
            result = await session.execute(
                select(ScraperState).where(ScraperState.key == "last_check")
            )
            state = result.scalar_one_or_none()
            
            if state:
                state.value = check_time.isoformat()
                state.updated_at = datetime.now()
            else:
                state = ScraperState(
                    key="last_check",
                    value=check_time.isoformat()
                )
                session.add(state)
            
            await session.commit()
    
    async def scrape_and_process(self):
        """爬取并处理一篇新文章（仅 Engineering）"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print("\n" + "=" * 60)
        print(f"[{timestamp}] 🚀 开始爬取并处理文章...")
        print("=" * 60)
        
        try:
            # 获取最后检查时间
            last_check = await self.get_last_check_time()
            print(f"📅 最后检查时间：{last_check.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 只抓取一篇 Engineering 新文章（基于时间戳）
            article_data = await self.scraper.scrape_one_engineering_article_by_date(last_check)
            
            if not article_data:
                print("没有新文章，跳过本次执行")
                return
            
            # 检查是否已存在（双重检查）
            async with self.db_session_factory() as session:
                result = await session.execute(
                    select(Article).where(Article.url == article_data['url'])
                )
                existing = result.scalar_one_or_none()
                
                if existing:
                    print(f"⏭️  跳过已存在：{article_data['title'][:50]}...")
                    return
                
                # 生成摘要（传入 Jina Reader 获取的内容）
                content = article_data.get('content', '')
                try:
                    summary = await self.summarizer.summarize(
                        title=article_data['title'],
                        content=content
                    )
                except Exception as e:
                    print(f"⚠️  摘要生成失败：{e}，使用标题作为摘要")
                    summary = article_data['title']
                
                new_article = Article(
                    title=article_data['title'],
                    url=article_data['url'],
                    published_date=article_data.get('published_date'),
                    content=content,
                    summary=summary,
                    notified=False
                )
                
                session.add(new_article)
                print(f"✅ 添加新文章：{new_article.title[:60]}...")
                
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
                
                # 更新最后检查时间
                await self.update_last_check_time(datetime.now())
                
        except Exception as e:
            print(f"\n❌ 爬取处理失败：{e}")
            import traceback
            traceback.print_exc()
            raise
        
        finally:
            end_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print("\n" + "=" * 60)
            print(f"[{end_timestamp}] 📊 处理完成")
            print("=" * 60)
    
    def start(self):
        """启动调度器"""
        # 添加定时任务：每 5 分钟执行一次
        self.scheduler.add_job(
            self.scrape_and_process,
            'interval',
            minutes=5,
            id='periodic_scrape',
            name='每 5 分钟文章爬取'
        )
        
        self.scheduler.start()
        self.is_running = True
        print(f"调度器已启动，每 5 分钟执行一次")
    
    def stop(self):
        """停止调度器"""
        self.scheduler.shutdown()
        self.is_running = False
        print("调度器已停止")
