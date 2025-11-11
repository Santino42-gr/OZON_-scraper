"""
Price History Collector - Cron Job

Автоматический сбор истории цен товаров OZON через Parser Market API.

Запуск: Каждые 24 часа (настраивается)
Цель: Собрать цены всех отслеживаемых артикулов и сохранить в БД
Использование: Для расчета средней цены за 7 дней

Usage:
    python -m cron_jobs.price_history_collector

Environment Variables:
    SUPABASE_URL - URL Supabase проекта
    SUPABASE_SERVICE_ROLE_KEY - Service role ключ для записи в БД
    PARSER_MARKET_API_KEY - API ключ Parser Market
    OZON_SCRAPER_BATCH_SIZE - Размер batch для scraping (default: 10)
    OZON_SCRAPER_DELAY - Задержка между артикулами в секундах (default: 2)
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

# Добавляем backend в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from database import get_supabase_client
from services.parser_market_client import ParserMarketClient
from config import settings


class PriceHistoryCollector:
    """
    Сборщик истории цен для всех отслеживаемых артикулов
    
    Алгоритм:
    1. Получить все уникальные артикулы из БД
    2. Для каждого артикула: scrape текущую цену
    3. Сохранить результат в ozon_scraper_price_history
    4. Логировать результаты и ошибки
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

        # Статистика выполнения
        self.stats = {
            "total_articles": 0,
            "successful": 0,
            "failed": 0,
            "skipped": 0,
            "start_time": None,
            "end_time": None,
            "errors": []
        }

    async def initialize(self):
        """Инициализация Parser Market client"""
        self.client = ParserMarketClient(
            api_key=settings.PARSER_MARKET_API_KEY,
            region=settings.PARSER_MARKET_REGION,
            timeout=settings.PARSER_MARKET_TIMEOUT,
            poll_interval=settings.PARSER_MARKET_POLL_INTERVAL
        )
        logger.info("Parser Market client initialized for cron job")

    async def cleanup(self):
        """Очистка ресурсов"""
        if self.client:
            await self.client.close()
        logger.info("Resources cleaned up")
    
    def get_all_articles(self) -> List[str]:
        """
        Получить все уникальные артикулы из БД
        
        Returns:
            Список артикулов
        """
        try:
            response = self.supabase.table("ozon_scraper_articles") \
                .select("article_number") \
                .eq("status", "active") \
                .execute()
            
            articles = [row["article_number"] for row in response.data]
            unique_articles = list(set(articles))  # Убираем дубликаты
            
            logger.info(f"Found {len(unique_articles)} unique articles to scrape")
            return unique_articles
            
        except Exception as e:
            logger.error(f"Failed to fetch articles from DB: {e}")
            return []
    
    async def scrape_article_price(self, article: str) -> Dict[str, Any]:
        """
        Получить цену товара через Parser Market API

        Args:
            article: Артикул товара

        Returns:
            Словарь с данными о ценах или None при ошибке
        """
        try:
            # Используем Parser Market API для получения данных
            product_info = await self.client.parse_sync(article)

            if not product_info:
                logger.warning(f"No data found for article: {article}")
                return None

            # Формируем данные для записи в БД
            price_data = {
                "article_number": article,
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

            logger.info(
                f"✅ Successfully parsed {article}: price={price_data['price']}"
            )
            return price_data

        except Exception as e:
            logger.error(f"❌ Failed to parse {article}: {e}")
            self.stats["errors"].append({
                "article": article,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return None
    
    def save_to_database(self, price_data: Dict[str, Any]) -> bool:
        """
        Сохранить данные о цене в БД
        
        Args:
            price_data: Данные о цене
            
        Returns:
            True если успешно сохранено
        """
        try:
            self.supabase.table("ozon_scraper_price_history") \
                .insert(price_data) \
                .execute()
            
            logger.debug(f"Saved price history for {price_data['article_number']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save to DB: {e}")
            return False
    
    async def process_batch(self, articles: List[str]):
        """
        Обработать batch артикулов
        
        Args:
            articles: Список артикулов
        """
        for article in articles:
            # Scrape цену
            price_data = await self.scrape_article_price(article)
            
            if price_data:
                # Сохранить в БД
                if self.save_to_database(price_data):
                    self.stats["successful"] += 1
                else:
                    self.stats["failed"] += 1
            else:
                self.stats["failed"] += 1
            
            # Задержка между запросами (rate limiting)
            await asyncio.sleep(self.delay_seconds)
    
    async def run(self):
        """
        Главный метод: запуск сбора истории цен
        """
        self.stats["start_time"] = datetime.now()
        
        logger.info("="*60)
        logger.info("🚀 Starting Price History Collection Cron Job")
        logger.info("="*60)
        
        try:
            # Инициализация
            await self.initialize()
            
            # Получить все артикулы
            articles = self.get_all_articles()
            self.stats["total_articles"] = len(articles)
            
            if not articles:
                logger.warning("No articles found to process")
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
            logger.info("✅ Price History Collection Completed")
            logger.info("="*60)
            logger.info(f"Total articles: {self.stats['total_articles']}")
            logger.info(f"Successful: {self.stats['successful']}")
            logger.info(f"Failed: {self.stats['failed']}")
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
                "event_type": "cron_price_history_collection",
                "message": f"Price history collection completed: {self.stats['successful']}/{self.stats['total_articles']} successful",
                "metadata": {
                    "stats": self.stats,
                    "batch_size": self.batch_size,
                    "delay_seconds": self.delay_seconds
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
    
    collector = PriceHistoryCollector(batch_size=batch_size, delay_seconds=delay)
    await collector.run()


if __name__ == "__main__":
    # Запуск cron job
    asyncio.run(main())

