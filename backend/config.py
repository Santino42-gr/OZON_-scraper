"""
Configuration module
Загрузка переменных окружения и конфигурация приложения
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Настройки приложения из .env файла"""

    # Supabase
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_ANON_KEY: Optional[str] = None

    # Database
    DATABASE_URL: Optional[str] = None

    # Backend
    BACKEND_API_URL: str = "http://localhost:8000"
    ENVIRONMENT: str = "development"

    # OZON API (будет позже)
    OZON_API_KEY: Optional[str] = None
    OZON_API_URL: Optional[str] = None

    # Security
    SECRET_KEY: str = "change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = "../.env"
        case_sensitive = True


# Создаем глобальный экземпляр настроек
settings = Settings()

