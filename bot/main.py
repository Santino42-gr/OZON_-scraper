"""
OZON Telegram Bot - Main Entry Point

Telegram бот для мониторинга товаров OZON.

Features:
- Отслеживание артикулов OZON
- Мониторинг цен (с/без Ozon Card)
- Статистика и отчеты
- Интеграция с Backend API
"""

import asyncio
import sys
from pathlib import Path

# Добавляем bot в путь
sys.path.insert(0, str(Path(__file__).parent))

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from loguru import logger

from config import settings
from utils import logger as bot_logger  # Инициализируем logger
from services.api_client import get_api_client
from handlers import start, help as help_handler, onboarding, articles, reports, stats, common
from middlewares import ThrottlingMiddleware, LoggingMiddleware, UserActivityMiddleware


async def on_startup():
    """
    Действия при запуске бота
    """
    logger.info("="*60)
    logger.info("🚀 OZON Telegram Bot Starting...")
    logger.info("="*60)
    
    # Проверяем подключение к Backend API
    try:
        api_client = get_api_client()
        health = await api_client.health_check()
        logger.success(f"✅ Backend API connected: {settings.BACKEND_API_URL}")
        logger.info(f"   Status: {health.get('status', 'unknown')}")
    except Exception as e:
        logger.warning(f"⚠️  Backend API not available: {e}")
        logger.warning("   Bot will start, but some features may not work")
    
    logger.info(f"🤖 Bot mode: {'WEBHOOK' if settings.USE_WEBHOOK else 'POLLING'}")
    logger.info(f"🌍 Environment: {settings.ENVIRONMENT}")
    logger.info("="*60)


async def on_shutdown():
    """
    Действия при остановке бота
    """
    logger.info("="*60)
    logger.info("🛑 OZON Telegram Bot Shutting down...")
    logger.info("="*60)
    
    # Закрываем API клиент
    try:
        api_client = get_api_client()
        await api_client.close()
        logger.info("✅ API Client closed")
    except Exception as e:
        logger.error(f"❌ Error closing API client: {e}")
    
    logger.info("👋 Bot stopped")
    logger.info("="*60)


async def main_polling(bot: Bot, dp: Dispatcher):
    """
    Запуск бота в режиме long polling (для разработки)
    
    Args:
        bot: Bot instance
        dp: Dispatcher instance
    """
    logger.info("🔄 Starting bot in POLLING mode...")
    
    try:
        await on_startup()
        
        # Удаляем webhook если был
        await bot.delete_webhook(drop_pending_updates=True)
        
        # Запускаем polling
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types()
        )
        
    except KeyboardInterrupt:
        logger.info("⏸️  Bot interrupted by user")
    except Exception as e:
        logger.error(f"❌ Error in polling: {e}")
        raise
    finally:
        await on_shutdown()


async def main_webhook(bot: Bot, dp: Dispatcher):
    """
    Запуск бота в режиме webhook (для production)
    
    Args:
        bot: Bot instance
        dp: Dispatcher instance
    """
    logger.info("🌐 Starting bot in WEBHOOK mode...")
    
    if not settings.WEBHOOK_URL:
        logger.error("❌ WEBHOOK_URL not configured!")
        sys.exit(1)
    
    try:
        await on_startup()
        
        # Устанавливаем webhook
        webhook_url = f"{settings.WEBHOOK_URL}{settings.WEBHOOK_PATH}"
        await bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True
        )
        
        logger.success(f"✅ Webhook set: {webhook_url}")
        
        # Здесь должен быть код для запуска web сервера (aiohttp, FastAPI)
        # Пример с aiohttp:
        from aiohttp import web
        
        async def handle_webhook(request):
            """Обработчик webhook запросов"""
            update = await request.json()
            await dp.feed_update(bot, update)
            return web.Response()
        
        app = web.Application()
        app.router.add_post(settings.WEBHOOK_PATH, handle_webhook)
        
        runner = web.AppRunner(app)
        await runner.setup()
        
        site = web.TCPSite(runner, "0.0.0.0", 8080)
        await site.start()
        
        logger.info("🌐 Webhook server started on port 8080")
        
        # Держим сервер запущенным
        await asyncio.Event().wait()
        
    except KeyboardInterrupt:
        logger.info("⏸️  Bot interrupted by user")
    except Exception as e:
        logger.error(f"❌ Error in webhook mode: {e}")
        raise
    finally:
        await on_shutdown()


async def main():
    """
    Главная функция запуска бота
    """
    # Создаем Bot instance
    bot = Bot(
        token=settings.TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML
        )
    )
    
    # Создаем Dispatcher
    dp = Dispatcher()
    
    # Регистрируем middlewares
    # Порядок важен: ThrottlingMiddleware должен быть первым
    dp.message.middleware(ThrottlingMiddleware())
    dp.callback_query.middleware(ThrottlingMiddleware())
    
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())
    
    dp.message.middleware(UserActivityMiddleware())
    dp.callback_query.middleware(UserActivityMiddleware())
    
    logger.info("✅ Middlewares registered: Throttling, Logging, UserActivity")
    
    # Регистрируем роутеры
    # Порядок важен: более специфичные handlers должны быть выше
    dp.include_router(start.router)
    dp.include_router(help_handler.router)
    dp.include_router(onboarding.router)
    dp.include_router(articles.router)
    dp.include_router(reports.router)
    dp.include_router(stats.router)
    dp.include_router(common.router)  # common должен быть последним (fallback)
    
    logger.info("✅ Routers registered: 7 total")
    
    # Выбираем режим работы
    if settings.USE_WEBHOOK:
        await main_webhook(bot, dp)
    else:
        await main_polling(bot, dp)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.critical(f"💥 Critical error: {e}")
        sys.exit(1)
