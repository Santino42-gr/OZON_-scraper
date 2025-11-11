"""
Price Updater - Cron Job

Автоматическое обновление цен товаров OZON через Parser Market API и отправка уведомлений.

Запуск: 09:00 и 15:00 (настраивается)
Логика:
- 09:00 - обрабатывает артикулы с report_frequency IN ('once', 'twice')
- 15:00 - обрабатывает только артикулы с report_frequency = 'twice'
- Обновляет цены в таблице ozon_scraper_articles
- Сохраняет историю в ozon_scraper_price_history
- Отправляет уведомления в Telegram при изменении цен

Usage:
    python -m cron_jobs.price_updater

Environment Variables:
    SUPABASE_URL - URL Supabase проекта
    SUPABASE_SERVICE_ROLE_KEY - Service role ключ для записи в БД
    PARSER_MARKET_API_KEY - API ключ Parser Market
    TELEGRAM_BOT_TOKEN - Токен Telegram бота для уведомлений
    OZON_SCRAPER_BATCH_SIZE - Размер batch для scraping (default: 10)
    OZON_SCRAPER_DELAY - Задержка между артикулами в секундах (default: 2)
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

# Добавляем backend в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from database import get_supabase_client
from services.parser_market_client import ParserMarketClient
from services.telegram_notifier import get_telegram_notifier
from config import settings


class PriceUpdater:
    """
    Обновление цен и отправка уведомлений
    
    Алгоритм:
    1. Определить текущее время (09:00 или 15:00)
    2. Получить артикулы с соответствующей частотой отчетов
    3. Для каждого артикула: получить новые данные через Parser Market
    4. Сравнить новые цены со старыми
    5. Обновить данные в БД
    6. Отправить уведомление если цены изменились
    """
    
    def __init__(self, batch_size: int = 10, delay_seconds: int = 2):
        """
        Args:
            batch_size: Количество артикулов в одном batch
            delay_seconds: Задержка между артикулами (для rate limiting)
        """
        self.batch_size = batch_size
        self.delay_seconds = delay_seconds
        self.client = None
        self.supabase = get_supabase_client()
        self.notifier = None

        # Статистика выполнения
        self.stats = {
            "total_articles": 0,
            "successful": 0,
            "failed": 0,
            "notifications_sent": 0,
            "start_time": None,
            "end_time": None,
            "errors": []
        }
    
    def get_current_hour(self) -> int:
        """Получить текущий час (0-23)"""
        return datetime.now().hour
    
    def get_articles_by_frequency(self, hour: int) -> List[Dict[str, Any]]:
        """
        Получить артикулы для обработки в зависимости от времени
        
        Args:
            hour: Текущий час (9 для 09:00, 15 для 15:00)
            
        Returns:
            Список артикулов с информацией о пользователе
        """
        try:
            query = self.supabase.table("ozon_scraper_articles") \
                .select("id, article_number, user_id, report_frequency, normal_price, ozon_card_price, name") \
                .eq("status", "active")
            
            # Фильтруем по частоте отчетов
            if hour == 9:
                # 09:00 - обрабатываем все артикулы с once или twice
                query = query.in_("report_frequency", ["once", "twice"])
            elif hour == 15:
                # 15:00 - только twice
                query = query.eq("report_frequency", "twice")
            else:
                # Для других часов возвращаем пустой список
                logger.warning(f"Unexpected hour: {hour}. Expected 9 or 15.")
                return []
            
            response = query.execute()
            
            # Получаем telegram_id для каждого пользователя
            # Оптимизируем: получаем всех пользователей одним запросом
            user_ids = [article.get("user_id") for article in response.data if article.get("user_id")]
            unique_user_ids = list(set(user_ids))
            
            # Получаем telegram_id для всех пользователей
            users_map = {}
            if unique_user_ids:
                users_response = self.supabase.table("ozon_scraper_users") \
                    .select("id, telegram_id") \
                    .in_("id", unique_user_ids) \
                    .execute()
                
                for user in users_response.data:
                    users_map[user["id"]] = user.get("telegram_id")
            
            # Добавляем telegram_id к артикулам
            articles_with_users = []
            for article in response.data:
                user_id = article.get("user_id")
                if user_id and user_id in users_map:
                    article["telegram_id"] = users_map[user_id]
                    articles_with_users.append(article)
            
            logger.info(f"Found {len(articles_with_users)} articles to process for hour {hour}")
            return articles_with_users
            
        except Exception as e:
            logger.error(f"Failed to fetch articles from DB: {e}")
            return []
    
    async def initialize(self):
        """Инициализация клиентов"""
        self.client = ParserMarketClient(
            api_key=settings.PARSER_MARKET_API_KEY,
            region=settings.PARSER_MARKET_REGION,
            timeout=settings.PARSER_MARKET_TIMEOUT,
            poll_interval=settings.PARSER_MARKET_POLL_INTERVAL
        )
        
        # Инициализируем notifier
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not bot_token:
            logger.warning("TELEGRAM_BOT_TOKEN not set, notifications will be disabled")
        else:
            self.notifier = get_telegram_notifier(bot_token=bot_token)
        
        logger.info("Clients initialized for price updater")

    async def cleanup(self):
        """Очистка ресурсов"""
        if self.client:
            await self.client.close()
        logger.info("Resources cleaned up")
    
    async def update_article_price(
        self,
        article: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Обновить цену артикула и отправить уведомление при изменении
        
        Args:
            article: Данные артикула из БД
            
        Returns:
            Новые данные о ценах или None при ошибке
        """
        try:
            article_number = article["article_number"]
            article_id = article["id"]
            
            # Получаем новые данные через Parser Market
            product_info = await self.client.parse_sync(article_number)

            if not product_info:
                logger.warning(f"No data found for article: {article_number}")
                return None

            # Старые цены для сравнения
            old_prices = {
                "normal_price": article.get("normal_price"),
                "ozon_card_price": article.get("ozon_card_price")
            }
            
            # Новые цены
            new_prices = {
                "normal_price": product_info.normal_price,
                "ozon_card_price": product_info.ozon_card_price
            }
            
            # Обновляем данные в таблице articles
            update_data = {
                "price": product_info.price,
                "normal_price": product_info.normal_price,
                "ozon_card_price": product_info.ozon_card_price,
                "old_price": product_info.old_price,
                "name": product_info.name,
                "rating": product_info.rating,
                "reviews_count": product_info.reviews_count,
                "available": product_info.available,
                "last_check": datetime.now().isoformat(),
                "price_updated_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            self.supabase.table("ozon_scraper_articles") \
                .update(update_data) \
                .eq("id", article_id) \
                .execute()
            
            # Сохраняем в историю цен
            price_history_data = {
                "article_number": article_number,
                "price": product_info.price,
                "normal_price": product_info.normal_price,
                "ozon_card_price": product_info.ozon_card_price,
                "old_price": product_info.old_price,
                "product_available": product_info.available,
                "rating": product_info.rating,
                "reviews_count": product_info.reviews_count,
                "source": "parser_market_api",
                "scraping_success": True,
                "scraping_duration_ms": product_info.fetch_time_ms,
                "price_date": datetime.now().isoformat()
            }
            
            self.supabase.table("ozon_scraper_price_history") \
                .insert(price_history_data) \
                .execute()
            
            # Отправляем уведомление если цены изменились
            if self.notifier and article.get("telegram_id"):
                telegram_id = article["telegram_id"]
                article_name = article.get("name") or product_info.name
                
                try:
                    success = await self.notifier.send_price_update_notification(
                        telegram_id=telegram_id,
                        article_number=article_number,
                        article_name=article_name,
                        old_prices=old_prices,
                        new_prices=new_prices
                    )
                    
                    if success:
                        self.stats["notifications_sent"] += 1
                except Exception as e:
                    logger.warning(f"Failed to send notification for {article_number}: {e}")
            
            logger.info(
                f"✅ Updated {article_number}: "
                f"normal={new_prices['normal_price']}, "
                f"card={new_prices['ozon_card_price']}"
            )
            
            return {
                "article_number": article_number,
                "old_prices": old_prices,
                "new_prices": new_prices
            }

        except Exception as e:
            logger.error(f"❌ Failed to update article {article.get('article_number', 'unknown')}: {e}")
            self.stats["errors"].append({
                "article": article.get("article_number", "unknown"),
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return None
    
    async def process_batch(self, articles: List[Dict[str, Any]]):
        """
        Обработать batch артикулов
        
        Args:
            articles: Список артикулов с данными пользователей
        """
        for article in articles:
            result = await self.update_article_price(article)
            
            if result:
                self.stats["successful"] += 1
            else:
                self.stats["failed"] += 1
            
            # Задержка между запросами (rate limiting)
            await asyncio.sleep(self.delay_seconds)
    
    async def run(self):
        """
        Главный метод: запуск обновления цен
        """
        self.stats["start_time"] = datetime.now()
        current_hour = self.get_current_hour()
        
        logger.info("="*60)
        logger.info(f"🚀 Starting Price Updater Cron Job (Hour: {current_hour:02d}:00)")
        logger.info("="*60)
        
        try:
            # Инициализация
            await self.initialize()
            
            # Получить артикулы для текущего времени
            articles = self.get_articles_by_frequency(current_hour)
            self.stats["total_articles"] = len(articles)
            
            if not articles:
                logger.warning(f"No articles found to process for hour {current_hour}")
                return
            
            logger.info(f"Processing {len(articles)} articles in batches of {self.batch_size}")
            
            # Обработать артикулы batch-ами
            for i in range(0, len(articles), self.batch_size):
                batch = articles[i:i + self.batch_size]
                batch_num = (i // self.batch_size) + 1
                total_batches = (len(articles) + self.batch_size - 1) // self.batch_size
                
                logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} articles)")
                await self.process_batch(batch)
            
            # Финализация
            self.stats["end_time"] = datetime.now()
            duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
            
            logger.info("="*60)
            logger.info("✅ Price Updater Completed")
            logger.info("="*60)
            logger.info(f"Total articles: {self.stats['total_articles']}")
            logger.info(f"Successful: {self.stats['successful']}")
            logger.info(f"Failed: {self.stats['failed']}")
            logger.info(f"Notifications sent: {self.stats['notifications_sent']}")
            logger.info(f"Duration: {duration:.2f}s")
            logger.info(f"Success rate: {(self.stats['successful'] / max(self.stats['total_articles'], 1) * 100):.1f}%")
            
            if self.stats["errors"]:
                logger.warning(f"Errors encountered: {len(self.stats['errors'])}")
                for error in self.stats["errors"][:5]:  # Показываем первые 5 ошибок
                    logger.warning(f"  - {error['article']}: {error['error']}")
            
            # Логируем в БД
            self.log_cron_execution()
            
        except Exception as e:
            logger.critical(f"Cron job failed with critical error: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            await self.cleanup()
    
    def log_cron_execution(self):
        """Логировать результат выполнения cron job в БД"""
        try:
            log_entry = {
                "level": "INFO" if self.stats["failed"] == 0 else "WARNING",
                "event_type": "cron_price_update",
                "message": f"Price update completed: {self.stats['successful']}/{self.stats['total_articles']} successful, {self.stats['notifications_sent']} notifications sent",
                "metadata": {
                    "stats": self.stats,
                    "batch_size": self.batch_size,
                    "delay_seconds": self.delay_seconds,
                    "hour": self.get_current_hour()
                }
            }
            
            self.supabase.table("ozon_scraper_logs") \
                .insert(log_entry) \
                .execute()
            
            logger.info("Cron execution logged to database")
            
        except Exception as e:
            logger.error(f"Failed to log cron execution: {e}")


async def main():
    """
    Entry point для cron job
    """
    # Конфигурация из environment variables
    batch_size = int(os.getenv("OZON_SCRAPER_BATCH_SIZE", "10"))
    delay = int(os.getenv("OZON_SCRAPER_DELAY", "5"))
    
    updater = PriceUpdater(batch_size=batch_size, delay_seconds=delay)
    await updater.run()


if __name__ == "__main__":
    # Запуск cron job
    asyncio.run(main())

