"""
Конфигурация приложения
Загрузка настроек из переменных окружения
"""

import os
from typing import Optional


class Settings:
    """Настройки приложения"""
    
    # База данных
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/documatica")
    
    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 часа
    
    # Email
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.yandex.ru")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "noreply@documatica.ru")
    
    # DaData
    DADATA_API_KEY: str = os.getenv("DADATA_API_KEY", "")
    DADATA_SECRET_KEY: str = os.getenv("DADATA_SECRET_KEY", "")
    
    # Т-Банк (Тинькофф) эквайринг
    TBANK_TERMINAL_KEY: str = os.getenv("TBANK_TERMINAL_KEY", "")
    TBANK_PASSWORD: str = os.getenv("TBANK_PASSWORD", "")
    TBANK_PRODUCTION: bool = os.getenv("TBANK_PRODUCTION", "false").lower() == "true"
    TBANK_MOCK: bool = os.getenv("TBANK_MOCK", "false").lower() == "true"  # Mock-режим для тестирования
    
    # OpenAI API
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Базовый URL приложения (для callback'ов)
    BASE_URL: str = os.getenv("BASE_URL", "https://oplatanalogov.ru")
    
    # Debug режим
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Feature Flags
    # Новая логика сохранения документов: один UUID, обновление вместо создания новых версий
    FEATURE_NEW_SAVE_LOGIC: bool = os.getenv("FEATURE_NEW_SAVE_LOGIC", "false").lower() == "true"


settings = Settings()
