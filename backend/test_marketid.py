"""
Тестовый скрипт для проверки использования marketid метода

Usage:
    python test_marketid.py [article_number]

Example:
    python test_marketid.py 1066650955
"""

import asyncio
import sys
from pathlib import Path

# Добавляем backend в путь
sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger
from services.parser_market_client import ParserMarketClient
from services.ozon_service import get_ozon_service
from config import settings


async def test_parse_marketid(article: str):
    """Тест парсинга товара через метод marketid"""
    logger.info("=" * 60)
    logger.info(f"TEST: Parse Product using marketid method - {article}")
    logger.info("=" * 60)

    async with ParserMarketClient(
        api_key=settings.PARSER_MARKET_API_KEY,
        region=settings.PARSER_MARKET_REGION,
        timeout=settings.PARSER_MARKET_TIMEOUT
    ) as client:
        try:
            # Тест явного метода parse_marketid
            logger.info(f"Testing parse_marketid() method...")
            product = await client.parse_marketid(article)

            if product:
                logger.info(f"✅ Product parsed successfully:")
                logger.info(f"  • Article: {product.article}")
                logger.info(f"  • Name: {product.name}")
                logger.info(f"  • Brand: {product.brand}")
                logger.info(f"  • Price: {product.price} ₽")
                logger.info(f"  • Old Price: {product.old_price} ₽")
                logger.info(f"  • Ozon Card Price: {product.ozon_card_price} ₽")
                logger.info(f"  • Rating: {product.rating}")
                logger.info(f"  • Reviews: {product.reviews_count}")
                logger.info(f"  • Available: {product.available}")
                logger.info(f"  • URL: {product.url}")
                logger.info(f"  • Fetch time: {product.fetch_time_ms}ms")
                return True
            else:
                logger.error(f"❌ Product not found: {article}")
                return False

        except Exception as e:
            logger.error(f"❌ Parse failed: {e}", exc_info=True)
            return False


async def test_ozon_service(article: str):
    """Тест через OzonService"""
    logger.info("=" * 60)
    logger.info(f"TEST: OzonService.get_product_info() - {article}")
    logger.info("=" * 60)

    try:
        ozon_service = get_ozon_service()
        product = await ozon_service.get_product_info(article)

        if product:
            logger.info(f"✅ Product found via OzonService:")
            logger.info(f"  • Name: {product.name}")
            logger.info(f"  • Price: {product.price} ₽")
            logger.info(f"  • Rating: {product.rating}")
            return True
        else:
            logger.error(f"❌ Product not found via OzonService: {article}")
            return False

    except Exception as e:
        logger.error(f"❌ OzonService test failed: {e}", exc_info=True)
        return False


async def main():
    """Основная функция"""
    article = sys.argv[1] if len(sys.argv) > 1 else "1066650955"

    logger.info("Starting marketid method tests...")
    logger.info(f"Article: {article}")

    # Тест 1: Прямой вызов parse_marketid
    result1 = await test_parse_marketid(article)

    # Небольшая задержка между тестами
    await asyncio.sleep(2)

    # Тест 2: Через OzonService
    result2 = await test_ozon_service(article)

    # Итоги
    logger.info("=" * 60)
    logger.info("TEST RESULTS:")
    logger.info(f"  • parse_marketid(): {'✅ PASSED' if result1 else '❌ FAILED'}")
    logger.info(f"  • OzonService: {'✅ PASSED' if result2 else '❌ FAILED'}")
    logger.info("=" * 60)

    if result1 and result2:
        logger.success("All tests passed! ✅")
        return 0
    else:
        logger.error("Some tests failed! ❌")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

