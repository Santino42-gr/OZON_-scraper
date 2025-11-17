"""
OZON Bot Backend API
FastAPI приложение для обработки запросов от Telegram бота и админ-панели
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from loguru import logger
import sys
import uvicorn

# Импортируем настройки
from config import settings

# Импортируем роутеры
from routers import articles, users, reports, logs, stats, prices, comparison

# Импортируем middleware
from middlewares.logging_middleware import log_requests
from middlewares.error_handler import (
    global_exception_handler,
    validation_exception_handler,
    http_exception_handler
)

# Настройка логирования
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=settings.LOG_LEVEL
)
# Добавляем файловый логгер с обработкой ошибок
try:
    logger.add(
        settings.LOG_FILE,
        rotation="1 day",
        retention="7 days",
        level=settings.LOG_LEVEL
    )
except Exception as e:
    logger.warning(f"Failed to setup file logging: {e}")

# Создаем приложение FastAPI
app = FastAPI(
    title="OZON Bot API",
    description="Backend API для OZON Telegram Bot & Admin Panel MVP",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging middleware
app.middleware("http")(log_requests)

# Обработчики ошибок
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)

# Подключаем роутеры
app.include_router(articles.router, prefix="/api/v1/articles", tags=["Articles 📦"])
app.include_router(prices.router, prefix="/api/v1/articles", tags=["Prices 💰"])
app.include_router(comparison.router, prefix="/api/v1/comparison", tags=["Comparison ⚖️"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users 👥"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports 📊"])
app.include_router(logs.router, prefix="/api/v1/logs", tags=["Logs 📝"])
app.include_router(stats.router, prefix="/api/v1/stats", tags=["Statistics 📈"])


@app.on_event("startup")
async def startup_event():
    """Действия при запуске приложения"""
    logger.info("=" * 60)
    logger.info("🚀 Starting OZON Bot Backend API")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"API URL: {settings.BACKEND_API_URL}")
    logger.info(f"CORS Origins: {settings.cors_origins_list}")
    logger.info("=" * 60)

    # Проверка подключения к БД
    from database import check_database_connection
    if await check_database_connection():
        logger.success("✅ Database connection successful")
    else:
        logger.error("❌ Database connection failed")

    # Запуск планировщика задач (ОТКЛЮЧЕНО для экономии расходов на API)
    # Автоматические задачи мониторинга отключены по запросу клиента
    # Для включения: установите ENABLE_SCHEDULER=true в переменных окружения
    try:
        enable_scheduler = getattr(settings, 'ENABLE_SCHEDULER', False)
        if enable_scheduler:
            from services.scheduler import start_scheduler
            start_scheduler()
            logger.info("✅ Scheduler enabled and started")
        else:
            logger.info("⚠️  Scheduler disabled (ENABLE_SCHEDULER=false). Automatic monitoring tasks are OFF.")
    except Exception as e:
        logger.warning(f"⚠️  Could not check scheduler status: {e}. Scheduler will be disabled.")
        logger.info("⚠️  Scheduler disabled. Automatic monitoring tasks are OFF.")

    logger.info("📚 API Documentation available at: /docs")
    logger.info("🔄 ReDoc available at: /redoc")


@app.on_event("shutdown")
async def shutdown_event():
    """Действия при остановке приложения"""
    logger.info("🛑 Shutting down OZON Bot Backend API...")

    # Остановка планировщика задач (если был запущен)
    try:
        enable_scheduler = getattr(settings, 'ENABLE_SCHEDULER', False)
        if enable_scheduler:
            from services.scheduler import stop_scheduler
            stop_scheduler()
    except Exception as e:
        logger.warning(f"Could not stop scheduler: {e}")


@app.get("/")
async def root():
    """
    Корневой endpoint
    
    Возвращает информацию о сервисе
    """
    return {
        "service": "OZON Bot Backend API",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    
    Проверяет состояние сервиса и подключения к БД
    Всегда возвращает 200 для Docker healthcheck
    """
    try:
        from database import check_database_connection
        db_healthy = await check_database_connection()
    except Exception as e:
        # Логируем ошибку, но не падаем
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Database health check failed: {e}")
        db_healthy = False
    
    return {
        "status": "healthy" if db_healthy else "degraded",
        "service": "backend-api",
        "database": "connected" if db_healthy else "disconnected",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower(),
    )

