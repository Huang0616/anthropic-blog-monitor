"""
数据库迁移脚本 - 添加 ScraperState 表
"""
import asyncio
from sqlalchemy import text
from database import engine
from models import ScraperState, Base


async def migrate():
    """执行数据库迁移"""
    print("开始数据库迁移...")
    
    async with engine.begin() as conn:
        # 创建 ScraperState 表
        await conn.run_sync(ScraperState.metadata.create_all)
        print("✅ ScraperState 表创建成功")
        
        # 验证表已创建
        result = await conn.execute(text(
            "SELECT table_name FROM information_schema.tables WHERE table_name = 'scraper_state'"
        ))
        if result.fetchone():
            print("✅ 迁移完成：scraper_state 表已存在")
        else:
            print("❌ 迁移失败：scraper_state 表未创建")
    
    print("迁移完成！")


if __name__ == "__main__":
    asyncio.run(migrate())
