"""
OZON Telegram Bot
Бот для взаимодействия с пользователями на основе aiogram 3.x
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

# Импорты будут добавлены позже
# from config import settings
# from handlers import start, articles, help, errors
# from middlewares.auth import AuthMiddleware

# Временная конфигурация (заменится на config.py)
import os
from dotenv import load_dotenv

load_dotenv("../.env")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    """Главная функция запуска бота"""
    
    # Инициализация бота и диспетчера
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Регистрация middleware (будет позже)
    # dp.message.middleware(AuthMiddleware())
    
    # Регистрация handlers (будет позже)
    # dp.include_router(start.router)
    # dp.include_router(articles.router)
    # dp.include_router(help.router)
    # dp.include_router(errors.router)
    
    logger.info("🤖 OZON Bot запущен!")
    logger.info(f"Bot ID: {(await bot.get_me()).id}")
    logger.info(f"Bot Username: @{(await bot.get_me()).username}")
    
    try:
        # Удаление webhook (если был установлен)
        await bot.delete_webhook(drop_pending_updates=True)
        
        # Запуск polling
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен")

