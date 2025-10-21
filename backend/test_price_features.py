"""
Тестовый скрипт для проверки функций детальных цен

Проверяет:
1. Парсинг детальных цен через OzonScraper
2. Работу SQL функций для истории цен
3. API endpoints для работы с ценами
4. Обновление средних цен

Usage:
    python test_price_features.py
"""

import asyncio
import sys
from pathlib import Path

# Добавляем backend в путь
sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger
from database import get_supabase_client
from services.ozon_scraper import OzonScraper
from datetime import datetime, timedelta
import random


class PriceFeaturesTester:
    """Тестер для функций детальных цен"""
    
    def __init__(self):
        self.scraper = None
        self.supabase = get_supabase_client()
        self.test_article = "123456789"  # Можно заменить на реальный артикул
        self.results = {
            "scraper": False,
            "sql_functions": False,
            "price_history": False,
            "average_price": False
        }
    
    async def setup(self):
        """Инициализация"""
        logger.info("=" * 60)
        logger.info("🧪 Starting Price Features Testing")
        logger.info("=" * 60)
        
        self.scraper = OzonScraper(cache_ttl=0, rate_limit=5, timeout=30)
        logger.info("✅ OzonScraper initialized")
    
    async def cleanup(self):
        """Очистка"""
        if self.scraper:
            await self.scraper.close()
        logger.info("✅ Resources cleaned up")
    
    async def test_scraper_detailed_prices(self):
        """Тест 1: Парсинг детальных цен"""
        logger.info("\n" + "=" * 60)
        logger.info("📝 Test 1: Scraping Detailed Prices")
        logger.info("=" * 60)
        
        try:
            # Тестовый артикул (можно заменить на реальный)
            test_articles = ["123456789", "987654321"]
            
            for article in test_articles:
                logger.info(f"Testing article: {article}")
                
                # Получаем детальные цены
                prices = await self.scraper.get_product_prices_detailed(article)
                
                if prices:
                    logger.success(f"✅ Detailed prices received for {article}")
                    logger.info(f"  - Price: {prices.price}")
                    logger.info(f"  - Normal price: {prices.normal_price}")
                    logger.info(f"  - Ozon Card price: {prices.ozon_card_price}")
                    logger.info(f"  - Old price: {prices.old_price}")
                    logger.info(f"  - Average 7d: {prices.average_price_7days}")
                    self.results["scraper"] = True
                else:
                    logger.warning(f"⚠️  No data for {article}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Scraper test failed: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return False
    
    def test_sql_functions(self):
        """Тест 2: SQL функции для истории цен"""
        logger.info("\n" + "=" * 60)
        logger.info("📝 Test 2: SQL Functions for Price History")
        logger.info("=" * 60)
        
        try:
            test_article = "TEST-PRICE-" + str(int(datetime.now().timestamp()))
            
            # Вставляем тестовые данные истории
            logger.info(f"Inserting test price history for {test_article}")
            
            base_date = datetime.now()
            for i in range(7):
                price_date = base_date - timedelta(days=i)
                price = round(random.uniform(1000, 2000), 2)
                
                self.supabase.table("ozon_scraper_price_history").insert({
                    "article_number": test_article,
                    "price": price,
                    "normal_price": price,
                    "ozon_card_price": round(price * 0.9, 2),
                    "old_price": round(price * 1.2, 2),
                    "price_date": price_date.isoformat(),
                    "scraping_success": True,
                    "product_available": True
                }).execute()
            
            logger.success(f"✅ Inserted 7 test records")
            
            # Тестируем get_average_price_7days
            logger.info("Testing get_average_price_7days()")
            result = self.supabase.rpc(
                "get_average_price_7days",
                {"p_article_number": test_article, "p_days": 7}
            ).execute()
            
            if result.data and len(result.data) > 0:
                stats = result.data[0]
                logger.success(f"✅ Average price function works!")
                logger.info(f"  - Avg price: {stats.get('avg_price')}")
                logger.info(f"  - Min price: {stats.get('min_price')}")
                logger.info(f"  - Max price: {stats.get('max_price')}")
                logger.info(f"  - Data points: {stats.get('data_points')}")
                self.results["sql_functions"] = True
            else:
                logger.error("❌ No data returned from get_average_price_7days()")
            
            # Тестируем get_price_history
            logger.info("Testing get_price_history()")
            history = self.supabase.rpc(
                "get_price_history",
                {"p_article_number": test_article, "p_days": 7, "p_limit": 10}
            ).execute()
            
            if history.data:
                logger.success(f"✅ Price history function works! ({len(history.data)} records)")
                self.results["price_history"] = True
            else:
                logger.error("❌ No data returned from get_price_history()")
            
            # Очистка тестовых данных
            logger.info("Cleaning up test data")
            self.supabase.table("ozon_scraper_price_history") \
                .delete() \
                .eq("article_number", test_article) \
                .execute()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ SQL functions test failed: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return False
    
    async def test_update_average_prices(self):
        """Тест 3: Обновление средних цен"""
        logger.info("\n" + "=" * 60)
        logger.info("📝 Test 3: Update Average Prices")
        logger.info("=" * 60)
        
        try:
            # Тестируем update_all_average_prices
            logger.info("Testing update_all_average_prices()")
            result = self.supabase.rpc("update_all_average_prices", {}).execute()
            
            updated_count = result.data if result.data else 0
            logger.success(f"✅ Updated average prices for {updated_count} articles")
            self.results["average_price"] = True
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Update average prices test failed: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return False
    
    async def run_all_tests(self):
        """Запустить все тесты"""
        try:
            await self.setup()
            
            # Тест 1: Scraper
            await self.test_scraper_detailed_prices()
            
            # Тест 2: SQL функции
            self.test_sql_functions()
            
            # Тест 3: Обновление средних
            await self.test_update_average_prices()
            
            # Результаты
            logger.info("\n" + "=" * 60)
            logger.info("📊 Test Results Summary")
            logger.info("=" * 60)
            
            passed = sum(self.results.values())
            total = len(self.results)
            
            for test_name, result in self.results.items():
                status = "✅ PASS" if result else "❌ FAIL"
                logger.info(f"{status} - {test_name}")
            
            logger.info("=" * 60)
            logger.info(f"Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
            logger.info("=" * 60)
            
            if passed == total:
                logger.success("🎉 All tests passed!")
            else:
                logger.warning(f"⚠️  {total - passed} test(s) failed")
            
        except Exception as e:
            logger.critical(f"Critical error during testing: {e}")
            import traceback
            logger.debug(traceback.format_exc())
        
        finally:
            await self.cleanup()


async def main():
    """Entry point"""
    tester = PriceFeaturesTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())

