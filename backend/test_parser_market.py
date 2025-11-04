"""
Тестовый скрипт для проверки Parser Market API клиента

Usage:
    python test_parser_market.py [article_number]

Example:
    python test_parser_market.py 123456789
"""

import asyncio
import sys
from pathlib import Path

# Добавляем backend в путь
sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger
from services.parser_market_client import ParserMarketClient
from config import settings


async def test_balance():
    """Тест проверки баланса"""
    logger.info("=" * 60)
    logger.info("TEST: Get Balance")
    logger.info("=" * 60)

    async with ParserMarketClient(api_key=settings.PARSER_MARKET_API_KEY) as client:
        try:
            balance = await client.get_balance()

            logger.info(f"✅ Balance check successful:")
            logger.info(f"  • Login: {balance.get('your_login')}")
            logger.info(f"  • Email: {balance.get('your_email')}")
            logger.info(f"  • Free checks: {balance.get('checks_free')}")
            logger.info(f"  • Paid checks: {balance.get('checks_paid')}")
            logger.info(f"  • Pending: {balance.get('checks_pending')}")
            logger.info(f"  • Total available: {balance.get('checks_total')}")

            return True

        except Exception as e:
            logger.error(f"❌ Balance check failed: {e}")
            return False


async def test_parse_product(article: str):
    """Тест парсинга товара"""
    logger.info("=" * 60)
    logger.info(f"TEST: Parse Product {article}")
    logger.info("=" * 60)

    async with ParserMarketClient(
        api_key=settings.PARSER_MARKET_API_KEY,
        region=settings.PARSER_MARKET_REGION,
        timeout=settings.PARSER_MARKET_TIMEOUT
    ) as client:
        try:
            # Тест синхронного парсинга
            logger.info(f"Starting synchronous parse for article: {article}")
            product = await client.parse_sync(article)

            if product:
                logger.info(f"✅ Product parsed successfully:")
                logger.info(f"  • Article: {product.article}")
                logger.info(f"  • Name: {product.name}")
                logger.info(f"  • Price: {product.price} руб")
                logger.info(f"  • Normal price: {product.normal_price} руб")
                logger.info(f"  • Ozon Card price: {product.ozon_card_price} руб")
                logger.info(f"  • Old price: {product.old_price} руб")
                logger.info(f"  • Rating: {product.rating}")
                logger.info(f"  • Reviews: {product.reviews_count}")
                logger.info(f"  • Available: {product.available}")
                logger.info(f"  • Fetch time: {product.fetch_time_ms}ms")
                logger.info(f"  • Source: {product.source}")

                return True
            else:
                logger.warning(f"⚠️  No product data returned for {article}")
                return False

        except Exception as e:
            logger.error(f"❌ Product parsing failed: {e}", exc_info=True)
            return False


async def test_batch_parse(articles: list[str]):
    """Тест пакетного парсинга"""
    logger.info("=" * 60)
    logger.info(f"TEST: Batch Parse {len(articles)} products")
    logger.info("=" * 60)

    async with ParserMarketClient(
        api_key=settings.PARSER_MARKET_API_KEY,
        region=settings.PARSER_MARKET_REGION
    ) as client:
        try:
            results = await client.parse_batch(articles, timeout=150)

            success_count = sum(1 for r in results if r is not None)

            logger.info(f"✅ Batch parsing completed:")
            logger.info(f"  • Total: {len(articles)}")
            logger.info(f"  • Success: {success_count}")
            logger.info(f"  • Failed: {len(articles) - success_count}")

            for i, (article, result) in enumerate(zip(articles, results), 1):
                if result:
                    logger.info(f"  {i}. {article}: {result.name} - {result.price} руб")
                else:
                    logger.warning(f"  {i}. {article}: FAILED")

            return success_count > 0

        except Exception as e:
            logger.error(f"❌ Batch parsing failed: {e}")
            return False


async def main():
    """Главная функция тестирования"""
    logger.info("\n" + "=" * 60)
    logger.info("Parser Market API Client Test Suite")
    logger.info("=" * 60 + "\n")

    # Проверяем наличие API ключа
    if not settings.PARSER_MARKET_API_KEY or settings.PARSER_MARKET_API_KEY == "your-parser-market-api-key-here":
        logger.error("❌ PARSER_MARKET_API_KEY not configured in .env")
        logger.error("Please add your Parser Market API key to .env file")
        return

    # Тест 1: Проверка баланса
    balance_ok = await test_balance()
    print()

    if not balance_ok:
        logger.warning("⚠️  Balance check failed, but continuing with other tests...")
        print()

    # Тест 2: Парсинг одного товара
    if len(sys.argv) > 1:
        article = sys.argv[1]
    else:
        # Тестовый артикул Ozon (замените на реальный)
        article = "1669668169"  # Пример артикула
        logger.info(f"No article provided, using default: {article}")

    product_ok = await test_parse_product(article)
    print()

    # Тест 3: Пакетный парсинг (опционально)
    if len(sys.argv) > 2:
        articles = sys.argv[1:]
        batch_ok = await test_batch_parse(articles)
    else:
        logger.info("Skipping batch test (provide multiple articles to test)")
        batch_ok = None

    # Итоговый результат
    print()
    logger.info("=" * 60)
    logger.info("Test Results:")
    logger.info("=" * 60)
    logger.info(f"  Balance check: {'✅ PASS' if balance_ok else '❌ FAIL'}")
    logger.info(f"  Product parse: {'✅ PASS' if product_ok else '❌ FAIL'}")
    if batch_ok is not None:
        logger.info(f"  Batch parse:   {'✅ PASS' if batch_ok else '❌ FAIL'}")
    logger.info("=" * 60)

    if product_ok:
        logger.info("\n✅ Parser Market API client is working!")
    else:
        logger.warning("\n⚠️  Parser Market API client has issues")


if __name__ == "__main__":
    asyncio.run(main())
