from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Article(Base):
    """文章模型"""
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    url = Column(String(1000), unique=True, nullable=False, index=True)
    published_date = Column(DateTime, nullable=True)
    content = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    notified = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<Article(title='{self.title}', url='{self.url}')>"
