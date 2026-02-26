#!/usr/bin/env python3
"""修复旧文章数据 - 重新获取 content 和 summary"""

import asyncio
import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from config import settings
from models import Base, Article
from summarizer import Summarizer


async def fix_articles():
    """修复所有文章的 content 和 summary"""
    
    # 创建数据库引擎
    engine = create_async_engine(settings.async_database_url, echo=False)
    async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    summarizer = Summarizer()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        async with async_session_maker() as session:
            # 获取所有文章
            result = await session.execute(select(Article))
            articles = result.scalars().all()
            
            print(f"找到 {len(articles)} 篇文章")
            
            for i, article in enumerate(articles):
                print(f"\n[{i+1}/{len(articles)}] 修复：{article.title[:50]}...")
                
                # 如果 content 是 URL（长度<100），重新获取
                if not article.content or len(article.content) < 100:
                    try:
                        print(f"  重新获取内容...")
                        resp = await client.get(f"https://r.jina.ai/{article.url}")
                        resp.raise_for_status()
                        content = resp.text.strip()
                        
                        if len(content) > 100:
                            article.content = content[:5000]
                            print(f"  ✓ 获取成功 ({len(content)} 字符)")
                        else:
                            print(f"  ✗ 获取失败，内容太短")
                            continue
                    except Exception as e:
                        print(f"  ✗ 获取失败：{e}")
                        continue
                
                # 如果 summary 为空，重新生成
                if not article.summary and article.content:
                    try:
                        print(f"  生成摘要...")
                        summary = await summarizer.summarize(
                            title=article.title,
                            content=article.content
                        )
                        
                        if summary:
                            article.summary = summary
                            print(f"  ✓ 摘要生成成功")
                        else:
                            print(f"  ✗ 摘要生成失败")
                    except Exception as e:
                        print(f"  ✗ 摘要生成失败：{e}")
                        continue
                
                await session.commit()
                print(f"  ✅ 修复完成")
                
                # 避免请求过快
                await asyncio.sleep(1)
    
    print("\n" + "=" * 60)
    print("所有文章修复完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(fix_articles())
