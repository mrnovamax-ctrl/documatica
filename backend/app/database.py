"""
Конфигурация базы данных
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import Settings

settings = Settings()

# Используем только PostgreSQL
DATABASE_URL = settings.DATABASE_URL

# Убираем asyncpg для синхронного доступа
sync_url = DATABASE_URL.replace("+asyncpg", "")
engine = create_engine(sync_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency для получения сессии БД"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Инициализация таблиц БД"""
    from app.models import Base
    Base.metadata.create_all(bind=engine)
