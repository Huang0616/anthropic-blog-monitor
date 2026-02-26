from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Article(Base):
    """文章模型"""
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(2000), nullable=False, index=True)
    url = Column(String(1000), unique=True, nullable=False, index=True)
    published_date = Column(DateTime, nullable=True)
    content = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    notified = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<Article(title='{self.title}', url='{self.url}')>"


class ScraperState(Base):
    """爬虫状态 - 存储最后检查时间"""
    __tablename__ = "scraper_state"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)  # 例如："last_check"
    value = Column(String(500), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ScraperState(key='{self.key}', value='{self.value}')>"
