"""
数据库迁移脚本 v2 - 扩展 title 字段长度
"""
import asyncio
from sqlalchemy import text
from database import engine


async def migrate():
    """执行数据库迁移"""
    print("开始数据库迁移 v2...")
    
    async with engine.begin() as conn:
        # 扩展 title 字段长度从 500 到 2000
        await conn.execute(text(
            "ALTER TABLE articles ALTER COLUMN title TYPE VARCHAR(2000)"
        ))
        print("✅ articles.title 字段已扩展至 VARCHAR(2000)")
        
        # 验证修改
        result = await conn.execute(text("""
            SELECT column_name, data_type, character_maximum_length 
            FROM information_schema.columns 
            WHERE table_name = 'articles' AND column_name = 'title'
        """))
        row = result.fetchone()
        if row:
            print(f"✅ 验证：title 字段类型 = {row[0]}, 最大长度 = {row[2]}")
    
    print("迁移 v2 完成！")


if __name__ == "__main__":
    asyncio.run(migrate())
