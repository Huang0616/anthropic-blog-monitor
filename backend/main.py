from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime
import asyncio

from config import settings
from database import init_db, get_db, async_session_maker
from models import Article
from scraper import AnthropicScraper
from summarizer import Summarizer
from notifier import FeishuNotifier
from scheduler import BlogScheduler

# 创建 FastAPI 应用
app = FastAPI(
    title="Anthropic Blog Monitor",
    description="Anthropic 博客监控服务",
    version="1.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
scheduler = None
scraper = AnthropicScraper()
summarizer = Summarizer()
notifier = FeishuNotifier()


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    global scheduler
    
    # 初始化数据库
    await init_db()
    print("数据库初始化完成")
    
    # 启动定时任务
    scheduler = BlogScheduler(async_session_maker)
    scheduler.start()
    
    # 首次爬取
    asyncio.create_task(initial_scrape())


async def initial_scrape():
    """首次启动时执行一次爬取"""
    await asyncio.sleep(5)  # 等待 5 秒后执行
    try:
        await scheduler.scrape_and_process()
    except Exception as e:
        print(f"首次爬取失败：{e}")


@app.get("/")
async def root():
    """健康检查"""
    return {
        "status": "ok",
        "service": "Anthropic Blog Monitor",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/status")
async def get_status():
    """服务状态"""
    return {
        "status": "running",
        "scheduler_running": scheduler.is_running if scheduler else False,
        "next_run": str(scheduler.scheduler.get_job('daily_scrape').next_run_time) if scheduler else None,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/articles", response_model=List[dict])
async def get_articles(
    limit: int = 50,
    skip: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """获取文章列表"""
    result = await db.execute(
        select(Article)
        .order_by(desc(Article.created_at))
        .offset(skip)
        .limit(limit)
    )
    articles = result.scalars().all()
    
    return [
        {
            "id": article.id,
            "title": article.title,
            "url": article.url,
            "published_date": article.published_date.isoformat() if article.published_date else None,
            "summary": article.summary,
            "created_at": article.created_at.isoformat(),
            "notified": article.notified
        }
        for article in articles
    ]


@app.get("/articles/{article_id}")
async def get_article(article_id: int, db: AsyncSession = Depends(get_db)):
    """获取单篇文章详情"""
    result = await db.execute(
        select(Article).where(Article.id == article_id)
    )
    article = result.scalar_one_or_none()
    
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    
    return {
        "id": article.id,
        "title": article.title,
        "url": article.url,
        "published_date": article.published_date.isoformat() if article.published_date else None,
        "content": article.content,
        "summary": article.summary,
        "created_at": article.created_at.isoformat(),
        "notified": article.notified
    }


@app.post("/scrape")
async def trigger_scrape():
    """手动触发爬取"""
    try:
        await scheduler.scrape_and_process()
        return {"status": "success", "message": "爬取完成"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
