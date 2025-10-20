"""
Logger Configuration

Настройка логирования для Telegram бота с использованием loguru.
"""

import sys
from pathlib import Path
from loguru import logger
from config import settings


def setup_logger():
    """
    Настроить логирование для бота
    
    - Console output с цветным форматированием
    - File output (опционально)
    - Ротация файлов
    - Уровень логирования из настроек
    """
    # Удаляем дефолтный handler
    logger.remove()
    
    # Формат логов
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # Console handler
    logger.add(
        sys.stdout,
        format=log_format,
        level=settings.LOG_LEVEL,
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # File handler (если указан файл)
    if settings.LOG_FILE:
        log_file_path = Path(settings.LOG_FILE)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            settings.LOG_FILE,
            format=log_format,
            level=settings.LOG_LEVEL,
            rotation="10 MB",  # Ротация при 10MB
            retention="7 days",  # Хранить 7 дней
            compression="zip",  # Сжимать старые логи
            backtrace=True,
            diagnose=True
        )
        
        logger.info(f"📝 File logging enabled: {settings.LOG_FILE}")
    
    logger.info(f"✅ Logger configured (level: {settings.LOG_LEVEL})")
    
    return logger


# Экспортируем настроенный logger
setup_logger()

