"""
Configuration module for Telegram Bot
Загрузка переменных окружения и конфигурация бота
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Настройки бота из .env файла"""

    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str

    # Supabase
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_ANON_KEY: Optional[str] = None

    # Backend API
    BACKEND_API_URL: str = "http://localhost:8000"
    API_TIMEOUT: int = 30  # Таймаут API запросов в секундах
    API_RETRY_COUNT: int = 3  # Количество повторов при ошибках

    # Webhook (опционально для production)
    WEBHOOK_URL: Optional[str] = None
    WEBHOOK_PATH: str = "/webhook"
    
    # Bot Settings
    RATE_LIMIT: int = 5  # Количество запросов в минуту
    MAX_ARTICLES_PER_USER: int = 50  # Максимум артикулов на пользователя
    USE_WEBHOOK: bool = False  # True для production, False для разработки
    
    # Environment
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = None  # Файл для логов (опционально)

    class Config:
        env_file = "../.env"
        case_sensitive = True
        extra = "ignore"  # Игнорировать дополнительные переменные


# Создаем глобальный экземпляр настроек
settings = Settings()

