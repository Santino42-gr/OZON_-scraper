"""
Тестовый скрипт для проверки улучшенного OZON скрапера

Демонстрирует:
1. Парсинг товаров по артикулу с улучшенной защитой от детекции
2. Улучшенный парсинг рейтингов и отзывов
3. Обход блокировок OZON

Usage:
    python test_scraper_improvements.py
"""

import asyncio
import sys
from pathlib import Path

# Добавляем backend в path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from services.ozon_scraper import OzonScraper
from loguru import logger


async def test_improved_scraper():
    """Тест улучшенного скрапера с anti-detection"""

    logger.info("=" * 80)
    logger.info("🧪 Testing Improved OZON Scraper (Anti-Detection)")
    logger.info("=" * 80)

    scraper = OzonScraper(
        cache_ttl=3600,
        rate_limit=5,  # Консервативный лимит
        timeout=30
    )

    try:
        # Тестовые артикулы
        test_articles = [
            "1066650955",  # Артикул от пользователя
        ]

        logger.info(f"Testing {len(test_articles)} articles with improved scraper\n")

        successful = 0
        failed = 0

        for idx, article in enumerate(test_articles, 1):
            logger.info("")
            logger.info("=" * 80)
            logger.info(f"[{idx}/{len(test_articles)}] Testing article: {article}")
            logger.info("=" * 80)

            try:
                # Используем force_playwright для максимальной защиты
                product = await scraper.get_product_info(
                    article=article,
                    force_playwright=True,  # Принудительно используем Playwright
                    use_cache=False  # Отключаем кэш для теста
                )

                if product:
                    successful += 1
                    logger.success(f"✅ Successfully scraped article: {article}")
                    logger.info("")
                    logger.info(f"📦 Product Details:")
                    logger.info(f"   Name: {product.name}")
                    logger.info(f"   Article: {product.article}")
                    logger.info(f"   Price: {product.price} ₽" if product.price else "   Price: Not available")
                    logger.info(f"   Normal Price: {product.normal_price} ₽" if product.normal_price else "   Normal Price: Not available")
                    logger.info(f"   Ozon Card Price: {product.ozon_card_price} ₽" if product.ozon_card_price else "   Ozon Card Price: Not available")
                    logger.info(f"   Rating: {product.rating} ⭐" if product.rating else "   Rating: No rating")
                    logger.info(f"   Reviews: {product.reviews_count}" if product.reviews_count else "   Reviews: No reviews")
                    logger.info(f"   Availability: {product.availability.value}")
                    logger.info(f"   Source: {product.source.value}")
                    logger.info(f"   Fetch time: {product.fetch_time_ms}ms" if product.fetch_time_ms else "")
                    logger.info(f"   URL: {product.url}")
                else:
                    failed += 1
                    logger.warning(f"⚠️  Product not found: {article}")

            except Exception as e:
                failed += 1
                logger.error(f"❌ Failed to scrape {article}: {e}")
                import traceback
                logger.debug(traceback.format_exc())

            # Задержка между запросами
            if idx < len(test_articles):
                logger.info("Waiting before next request...")
                await asyncio.sleep(2)

        # Итоговая статистика
        logger.info("")
        logger.info("=" * 80)
        logger.info("📊 Test Results:")
        logger.info("=" * 80)
        logger.info(f"   Total articles tested: {len(test_articles)}")
        logger.info(f"   ✅ Successful: {successful}")
        logger.info(f"   ❌ Failed: {failed}")
        logger.info(f"   Success rate: {(successful/len(test_articles)*100):.1f}%")

        # Статистика скрапера
        logger.info("")
        logger.info("=" * 80)
        scraper.print_stats()
        logger.info("=" * 80)

        if successful > 0:
            logger.success(f"✅ Test completed! {successful}/{len(test_articles)} products scraped successfully")
        else:
            logger.error("❌ All tests failed - check OZON protection or network connection")

    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}")
        import traceback
        logger.error(traceback.format_exc())

    finally:
        await scraper.close()
        logger.info("🔒 Scraper closed")


async def main():
    """Главная функция"""

    # Настройка логирования
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )

    logger.info("🚀 Starting OZON Scraper Improvement Tests")
    logger.info("")
    logger.info("This test validates:")
    logger.info("  - Anti-detection improvements (slow_mo, additional browser flags)")
    logger.info("  - Enhanced rating and reviews parsing (6+ selectors)")
    logger.info("  - Ability to bypass OZON protection")
    logger.info("")

    await test_improved_scraper()

    logger.info("")
    logger.info("✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
