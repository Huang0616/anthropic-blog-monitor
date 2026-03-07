"""
数据库迁移脚本：添加全文翻译字段
"""
import asyncio
from sqlalchemy import text
from database import engine


async def migrate():
    """添加 content_translation 和 content_translated_at 字段"""
    async with engine.begin() as conn:
        # 检查字段是否已存在
        result = await conn.execute(
            text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='articles' 
                AND column_name='content_translation'
            """)
        )
        
        if not result.fetchone():
            print("添加 content_translation 字段...")
            await conn.execute(
                text("""
                    ALTER TABLE articles 
                    ADD COLUMN content_translation TEXT
                """)
            )
            print("✅ content_translation 字段添加成功")
        else:
            print("⏭️  content_translation 字段已存在，跳过")
        
        # 检查 content_translated_at 字段
        result = await conn.execute(
            text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='articles' 
                AND column_name='content_translated_at'
            """)
        )
        
        if not result.fetchone():
            print("添加 content_translated_at 字段...")
            await conn.execute(
                text("""
                    ALTER TABLE articles 
                    ADD COLUMN content_translated_at TIMESTAMP
                """)
            )
            print("✅ content_translated_at 字段添加成功")
        else:
            print("⏭️  content_translated_at 字段已存在，跳过")
        
        print("\n✅ 迁移完成")


if __name__ == "__main__":
    asyncio.run(migrate())
