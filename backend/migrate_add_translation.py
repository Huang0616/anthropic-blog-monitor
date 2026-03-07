"""
数据库迁移脚本：添加翻译字段
运行方式：python migrate_add_translation.py
"""

import asyncio
from sqlalchemy import text
from database import async_engine, Base
from models import Article, ScraperState


async def migrate():
    """执行数据库迁移"""
    print("开始数据库迁移...")
    
    async with async_engine.begin() as conn:
        # 检查字段是否已存在
        result = await conn.execute(
            text("SELECT name FROM pragma_table_info('articles') WHERE name='translation'")
        )
        translation_exists = result.fetchone()
        
        result = await conn.execute(
            text("SELECT name FROM pragma_table_info('articles') WHERE name='translated_at'")
        )
        translated_at_exists = result.fetchone()
        
        # 添加 translation 字段
        if not translation_exists:
            print("添加 translation 字段...")
            await conn.execute(
                text("ALTER TABLE articles ADD COLUMN translation TEXT")
            )
        else:
            print("translation 字段已存在，跳过")
        
        # 添加 translated_at 字段
        if not translated_at_exists:
            print("添加 translated_at 字段...")
            await conn.execute(
                text("ALTER TABLE articles ADD COLUMN translated_at DATETIME")
            )
        else:
            print("translated_at 字段已存在，跳过")
    
    print("数据库迁移完成！")


if __name__ == "__main__":
    asyncio.run(migrate())
