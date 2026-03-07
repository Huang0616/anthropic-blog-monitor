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
    
    # 首次爬取（延迟 15 秒，避免与定时任务冲突）
    # asyncio.create_task(initial_scrape())


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
    scrape_job = scheduler.scheduler.get_job('periodic_scrape') if scheduler else None
    translate_job = scheduler.scheduler.get_job('translate_existing_articles') if scheduler else None
    return {
        "status": "running",
        "scheduler_running": scheduler.is_running if scheduler else False,
        "scrape_job": {
            "next_run": str(scrape_job.next_run_time) if scrape_job else None,
        },
        "translate_job": {
            "next_run": str(translate_job.next_run_time) if translate_job else None,
        },
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
            "content": article.content,  # 添加原文内容
            "translation": article.translation,  # 添加翻译内容
            "translated_at": article.translated_at.isoformat() if article.translated_at else None,
            "content_translation": article.content_translation,  # 添加全文翻译
            "content_translated_at": article.content_translated_at.isoformat() if article.content_translated_at else None,
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


@app.post("/translate")
async def trigger_translate():
    """手动触发翻译未翻译文章"""
    try:
        await scheduler.translate_existing_articles()
        return {"status": "success", "message": "翻译任务执行完成"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/articles/{article_id}")
async def delete_article(article_id: int, db: AsyncSession = Depends(get_db)):
    """删除指定文章"""
    result = await db.execute(
        select(Article).where(Article.id == article_id)
    )
    article = result.scalar_one_or_none()
    
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    
    await db.delete(article)
    await db.commit()
    
    return {"status": "success", "message": f"文章已删除：{article.title}"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
