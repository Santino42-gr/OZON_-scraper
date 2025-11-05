"""
Тест для проверки работы OZON API через backend

Проверяет:
1. Работу API endpoints
2. Автоматический парсинг (productid → marketid)
3. Интеграцию с Parser Market API

Usage:
    python test_ozon_api.py [article_number]

Example:
    python test_ozon_api.py 1066650955
"""

import asyncio
import sys
import httpx
from pathlib import Path
from typing import Optional

# Добавляем backend в путь
sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger
from config import settings

# Настройка логирования
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO"
)


API_BASE_URL = "http://localhost:8000"


async def test_api_health():
    """Проверка health endpoint"""
    logger.info("=" * 60)
    logger.info("TEST 1: API Health Check")
    logger.info("=" * 60)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{API_BASE_URL}/health")
            response.raise_for_status()
            data = response.json()

            logger.info(f"✅ API is healthy:")
            logger.info(f"  • Status: {data.get('status')}")
            logger.info(f"  • Service: {data.get('service')}")
            logger.info(f"  • Database: {data.get('database')}")
            logger.info(f"  • Version: {data.get('version')}")

            return True

    except httpx.ConnectError:
        logger.error(f"❌ Cannot connect to API at {API_BASE_URL}")
        logger.error("   Make sure backend is running: uvicorn main:app --reload")
        return False
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return False


async def test_parse_via_api(article: str):
    """Тест парсинга через API endpoint"""
    logger.info("=" * 60)
    logger.info(f"TEST 2: Parse Article via API - {article}")
    logger.info("=" * 60)

    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            # Сначала создаем артикул (это запустит парсинг)
            logger.info(f"Creating article {article} via API...")
            
            # Нужен user_id - используем тестовый
            test_user_id = "00000000-0000-0000-0000-000000000000"
            
            create_data = {
                "article_number": article,
                "user_id": test_user_id
            }

            try:
                response = await client.post(
                    f"{API_BASE_URL}/api/v1/articles/",
                    json=create_data
                )

                if response.status_code == 201:
                    data = response.json()
                    logger.info(f"✅ Article created and parsed successfully:")
                    logger.info(f"  • Article ID: {data.get('id')}")
                    logger.info(f"  • Article Number: {data.get('article_number')}")
                    logger.info(f"  • Name: {data.get('name')}")
                    logger.info(f"  • Price: {data.get('price')} руб")
                    logger.info(f"  • Normal Price: {data.get('normal_price')} руб")
                    logger.info(f"  • Ozon Card Price: {data.get('ozon_card_price')} руб")
                    logger.info(f"  • Old Price: {data.get('old_price')} руб")
                    logger.info(f"  • Rating: {data.get('rating')}")
                    logger.info(f"  • Reviews: {data.get('reviews_count')}")
                    logger.info(f"  • Available: {data.get('available')}")
                    
                    article_id = data.get('id')
                    
                    # Тест проверки артикула
                    logger.info(f"\nTesting check endpoint for article {article_id}...")
                    check_response = await client.post(
                        f"{API_BASE_URL}/api/v1/articles/{article_id}/check"
                    )
                    
                    if check_response.status_code == 200:
                        check_data = check_response.json()
                        logger.info(f"✅ Article check successful:")
                        logger.info(f"  • Checked at: {check_data.get('checked_at')}")
                        logger.info(f"  • Success: {check_data.get('success')}")
                        if check_data.get('data'):
                            logger.info(f"  • Updated price: {check_data['data'].get('price')} руб")
                    
                    return True, article_id

                elif response.status_code == 409:
                    logger.warning(f"⚠️  Article already exists, getting existing...")
                    # Получаем существующий артикул
                    list_response = await client.get(
                        f"{API_BASE_URL}/api/v1/articles/?user_id={test_user_id}"
                    )
                    if list_response.status_code == 200:
                        articles = list_response.json()
                        for art in articles:
                            if art.get('article_number') == article:
                                logger.info(f"✅ Found existing article:")
                                logger.info(f"  • Article ID: {art.get('id')}")
                                logger.info(f"  • Name: {art.get('name')}")
                                logger.info(f"  • Price: {art.get('price')} руб")
                                return True, art.get('id')
                    
                    logger.error(f"❌ Article exists but cannot retrieve it")
                    return False, None

                elif response.status_code == 404:
                    logger.error(f"❌ Product not found in OZON: {article}")
                    logger.error("   This means parsing failed - product doesn't exist")
                    return False, None

                else:
                    error_data = response.json() if response.content else {}
                    logger.error(f"❌ Failed to create article: {response.status_code}")
                    logger.error(f"   Error: {error_data.get('detail', 'Unknown error')}")
                    return False, None

            except httpx.TimeoutException:
                logger.error(f"❌ Request timeout - parsing took too long")
                logger.error("   This is normal for first-time parsing (can take 1-2 minutes)")
                return False, None

    except Exception as e:
        logger.error(f"❌ API test failed: {e}", exc_info=True)
        return False, None


async def test_direct_parsing(article: str):
    """Тест прямого парсинга через ParserMarketClient"""
    logger.info("=" * 60)
    logger.info(f"TEST 3: Direct Parsing (ParserMarketClient) - {article}")
    logger.info("=" * 60)

    try:
        from services.parser_market_client import get_parser_market_client

        client = get_parser_market_client()
        
        logger.info("Testing automatic parsing (productid → marketid)...")
        product = await client.parse_auto(article)

        if product:
            logger.info(f"✅ Product parsed successfully:")
            logger.info(f"  • Article: {product.article}")
            logger.info(f"  • Name: {product.name}")
            logger.info(f"  • Price: {product.price} руб")
            logger.info(f"  • Normal Price: {product.normal_price} руб")
            logger.info(f"  • Ozon Card Price: {product.ozon_card_price} руб")
            logger.info(f"  • Old Price: {product.old_price} руб")
            logger.info(f"  • Rating: {product.rating}")
            logger.info(f"  • Reviews: {product.reviews_count}")
            logger.info(f"  • Available: {product.available}")
            logger.info(f"  • Fetch time: {product.fetch_time_ms}ms")
            logger.info(f"  • Source: {product.source}")
            return True
        else:
            logger.warning(f"⚠️  Product not found: {article}")
            return False

    except Exception as e:
        logger.error(f"❌ Direct parsing failed: {e}", exc_info=True)
        return False


async def main():
    """Главная функция тестирования"""
    logger.info("\n" + "=" * 60)
    logger.info("OZON API Integration Test")
    logger.info("=" * 60 + "\n")

    # Проверяем наличие API ключа
    if not settings.PARSER_MARKET_API_KEY or settings.PARSER_MARKET_API_KEY == "your-parser-market-api-key-here":
        logger.error("❌ PARSER_MARKET_API_KEY not configured in .env")
        logger.error("Please add your Parser Market API key to .env file")
        return

    # Получаем артикул из аргументов или используем тестовый
    if len(sys.argv) > 1:
        article = sys.argv[1]
    else:
        article = "1066650955"  # Тестовый артикул
        logger.info(f"No article provided, using test article: {article}")

    # Тест 1: Health check
    health_ok = await test_api_health()
    print()

    if not health_ok:
        logger.error("❌ API is not available. Please start backend first:")
        logger.error("   cd backend && uvicorn main:app --reload")
        return

    # Тест 2: Парсинг через API
    api_ok, article_id = await test_parse_via_api(article)
    print()

    # Тест 3: Прямой парсинг
    direct_ok = await test_direct_parsing(article)
    print()

    # Итоговый результат
    logger.info("=" * 60)
    logger.info("Test Results:")
    logger.info("=" * 60)
    logger.info(f"  API Health:     {'✅ PASS' if health_ok else '❌ FAIL'}")
    logger.info(f"  API Parsing:    {'✅ PASS' if api_ok else '❌ FAIL'}")
    logger.info(f"  Direct Parsing: {'✅ PASS' if direct_ok else '❌ FAIL'}")
    logger.info("=" * 60)

    if health_ok and api_ok and direct_ok:
        logger.info("\n✅ All tests passed! OZON API integration is working!")
    elif health_ok and (api_ok or direct_ok):
        logger.warning("\n⚠️  Some tests passed, but there are issues")
    else:
        logger.error("\n❌ Tests failed - check configuration and API key")


if __name__ == "__main__":
    asyncio.run(main())

