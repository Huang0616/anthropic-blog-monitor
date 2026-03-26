from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import Callable
import asyncio

from scraper import AnthropicScraper
from summarizer import Summarizer
from translator import Translator
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
        self.translator = Translator()
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
            
            # 获取所有已存在的 URL
            async with self.db_session_factory() as session:
                result = await session.execute(select(Article.url))
                existing_urls = set(row[0] for row in result.all())
            
            # 只抓取一篇 Engineering 新文章（基于时间戳 + URL 去重）
            article_data = await self.scraper.scrape_one_engineering_article_by_date(last_check, existing_urls)
            
            if not article_data:
                print("没有新文章，发送系统状态报告")
                # 获取统计信息
                async with self.db_session_factory() as session:
                    # 文章总数
                    from sqlalchemy import func
                    count_result = await session.execute(select(func.count(Article.id)))
                    total_articles = count_result.scalar()
                    
                    # 最新文章
                    latest_result = await session.execute(
                        select(Article).order_by(Article.created_at.desc()).limit(1)
                    )
                    latest_article = latest_result.scalar_one_or_none()
                    
                    latest_info = None
                    if latest_article:
                        latest_info = {
                            'title': latest_article.title,
                            'published_date': latest_article.published_date or latest_article.created_at
                        }
                    
                    # 发送状态报告
                    if self.notifier.webhook_url:
                        await self.notifier.send_status_report(
                            total_articles=total_articles,
                            last_check=datetime.now(),
                            latest_article=latest_info
                        )
                
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
                
                # 翻译标题和摘要
                translation = None
                if summary:
                    try:
                        print(f"🌐 开始翻译...")
                        translation = await self.translator.translate(
                            title=article_data['title'],
                            summary=summary
                        )
                        if translation:
                            print(f"✅ 翻译成功")
                        else:
                            print(f"⚠️  翻译失败，继续处理")
                    except Exception as e:
                        print(f"⚠️  翻译失败：{e}，继续处理")
                
                new_article = Article(
                    title=article_data['title'],
                    url=article_data['url'],
                    published_date=article_data.get('published_date'),
                    content=content,
                    summary=summary,
                    translation=str(translation) if translation else None,  # 存储为 JSON 字符串
                    translated_at=datetime.now() if translation else None,
                    notified=False
                )
                
                session.add(new_article)
                print(f"✅ 添加新文章：{new_article.title[:60]}...")
                
                # 推送通知
                if summary and self.notifier.webhook_url:
                    print(f"📤 发送飞书推送...")
                    notify_success = await self.notifier.send_article_notification(
                        title=new_article.title,
                        summary=summary,
                        url=new_article.url,
                        translation=translation
                    )
                    if notify_success:
                        new_article.notified = True
                        print("✅ 飞书推送成功，已标记 notified=True")
                    else:
                        new_article.notified = False
                        print("❌ 飞书推送失败，保留 notified=False")
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
    
    async def translate_existing_articles(self):
        """翻译未翻译的文章（一次只处理1篇，包含全文翻译）"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print("\n" + "=" * 60)
        print(f"[{timestamp}] 🌐 开始翻译未翻译文章...")
        print("=" * 60)

        try:
            async with self.db_session_factory() as session:
                # 查询未全文翻译的文章（优先翻译有内容的）
                from sqlalchemy import or_
                result = await session.execute(
                    select(Article).where(
                        or_(
                            Article.content_translation.is_(None),
                            Article.content_translation == ''
                        ),
                        Article.content.isnot(None),  # 必须有内容才能全文翻译
                        Article.content != ''
                    ).order_by(Article.created_at.desc()).limit(1)  # 一次只处理1篇
                )
                article = result.scalar_one_or_none()

                if not article:
                    print("✅ 所有文章已翻译，无需处理")
                    return

                print(f"📝 开始翻译文章：{article.title[:50]}...")

                try:
                    # 调用全文翻译接口
                    content_translation = await self.translator.translate_full_content(
                        title=article.title,
                        summary=article.summary or article.title,
                        content=article.content
                    )

                    if content_translation:
                        import json

                        # 存储全文翻译结果
                        article.content_translation = json.dumps(content_translation, ensure_ascii=False)
                        article.content_translated_at = datetime.now()
                        print(f"✅ 全文翻译成功")

                        # 同时更新标题和摘要的翻译（如果之前没有翻译）
                        if not article.translation and (content_translation.get('title') or content_translation.get('summary')):
                            simple_translation = {
                                "title": content_translation.get('title', ''),
                                "summary": content_translation.get('summary', '')
                            }
                            article.translation = json.dumps(simple_translation, ensure_ascii=False)
                            article.translated_at = datetime.now()
                            print(f"✅ 同时更新标题和摘要翻译")
                    else:
                        print(f"⚠️  全文翻译失败，跳过")

                except Exception as e:
                    print(f"❌ 翻译文章失败：{e}")
                    import traceback
                    traceback.print_exc()

                await session.commit()
                print(f"\n✅ 本次翻译任务完成")

        except Exception as e:
            print(f"\n❌ 翻译任务失败：{e}")
            import traceback
            traceback.print_exc()
    
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
        
        # 添加翻译任务：每 10 分钟执行一次，初始延迟 5 分钟
        from apscheduler.triggers.interval import IntervalTrigger
        self.scheduler.add_job(
            self.translate_existing_articles,
            IntervalTrigger(minutes=10),
            id='translate_existing_articles',
            name='每 10 分钟翻译未翻译文章',
            next_run_time=datetime.now() + timedelta(minutes=5)  # 初始延迟 5 分钟
        )
        
        self.scheduler.start()
        self.is_running = True
        print(f"调度器已启动：爬取任务每 5 分钟执行，翻译任务每 10 分钟执行")
    
    def stop(self):
        """停止调度器"""
        self.scheduler.shutdown()
        self.is_running = False
        print("调度器已停止")
