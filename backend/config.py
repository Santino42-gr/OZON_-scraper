"""
Configuration module
Загрузка переменных окружения и конфигурация приложения
"""

from pydantic_settings import BaseSettings
from typing import Optional, List


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

    # OZON API
    OZON_CLIENT_ID: Optional[str] = None
    OZON_API_KEY: Optional[str] = None
    OZON_RATE_LIMIT: int = 30
    OZON_TIMEOUT: int = 10
    OZON_CACHE_TTL: int = 3600

    # Security
    SECRET_KEY: str = "change-this-in-production"
    API_SECRET_KEY: str = "change-this-api-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS Configuration
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/backend.log"

    # Parser Market API (Web Scraping)
    PARSER_MARKET_API_KEY: str
    PARSER_MARKET_REGION: str = "Москва"
    PARSER_MARKET_TIMEOUT: int = 120  # Timeout for task completion (seconds)
    PARSER_MARKET_POLL_INTERVAL: int = 10  # Polling interval (seconds)
    PARSER_MARKET_MAX_RETRIES: int = 3

    # Scheduler (Automatic Tasks)
    ENABLE_SCHEDULER: bool = False  # Отключено по умолчанию для экономии расходов на API

    # Redis (optional)
    REDIS_URL: Optional[str] = None
    REDIS_PASSWORD: Optional[str] = None

    @property
    def cors_origins_list(self) -> List[str]:
        """Преобразовать CORS_ORIGINS из строки в список"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        # Docker Compose передает переменные через env_file, они доступны в окружении
        # Локально ищем .env файл
        env_file = [".env", "../.env"]  # Пробуем оба варианта
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Игнорировать дополнительные поля из .env
        # pydantic-settings автоматически читает из переменных окружения, даже если нет файла


# Создаем глобальный экземпляр настроек с обработкой ошибок
try:
    settings = Settings()
except Exception as e:
    import sys
    print(f"ERROR: Failed to load settings: {e}")
    print("Please check that .env file exists and contains all required variables:")
    print("  - SUPABASE_URL")
    print("  - SUPABASE_SERVICE_ROLE_KEY")
    print("  - PARSER_MARKET_API_KEY")
    sys.exit(1)

