"""
Конфигурация базы данных
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# SQLite для простоты (можно заменить на PostgreSQL)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/documatica.db")

# Для SQLite
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # Для PostgreSQL убираем asyncpg для синхронного доступа
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
