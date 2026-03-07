"""
数据库重置脚本 - 清空文章并初始化时间戳
"""
import asyncio
from sqlalchemy import text, delete
from database import engine, async_session_maker
from models import Article, ScraperState
from datetime import datetime


async def reset():
    """重置数据库"""
    print("开始重置数据库...")
    
    async with engine.begin() as conn:
        # 1. 清空 articles 表
        await conn.execute(text("DELETE FROM articles"))
        print("✅ 已清空 articles 表")
        
        # 2. 设置 last_check 时间为 2025-10-01
        reset_time = datetime(2025, 10, 1)
        
        # 检查是否存在 last_check 记录
        result = await conn.execute(
            text("SELECT * FROM scraper_state WHERE key = :key"),
            {"key": "last_check"}
        )
        existing = result.fetchone()
        
        if existing:
            await conn.execute(
                text("UPDATE scraper_state SET value = :value, updated_at = :now WHERE key = :key"),
                {"value": reset_time.isoformat(), "now": datetime.now(), "key": "last_check"}
            )
            print(f"✅ 已更新 last_check 时间：{reset_time.strftime('%Y-%m-%d')}")
        else:
            await conn.execute(
                text("INSERT INTO scraper_state (key, value, updated_at) VALUES (:key, :value, :now)"),
                {"key": "last_check", "value": reset_time.isoformat(), "now": datetime.now()}
            )
            print(f"✅ 已创建 last_check 记录：{reset_time.strftime('%Y-%m-%d')}")
    
    print("\n数据库重置完成！")
    print("下次爬取将从 2025-10-01 开始检查新文章")


if __name__ == "__main__":
    asyncio.run(reset())
