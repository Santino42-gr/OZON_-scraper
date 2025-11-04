"""
Тестирование интеграции Parser Market API с FastAPI endpoints

Этот скрипт проверяет работу API endpoints с Parser Market API:
- POST /api/v1/articles/ - добавление артикула
- GET /api/v1/articles/{id} - получение артикула
- POST /api/v1/articles/{id}/check - проверка артикула

Usage:
    # Запуск backend должен быть активен: uvicorn main:app --reload
    python test_api_integration.py [article_number]
"""

import asyncio
import sys
import httpx
from pathlib import Path
from typing import Optional, Dict, Any

# Добавляем backend в путь
sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger
from config import settings


# ==================== Test Configuration ====================

API_BASE_URL = settings.BACKEND_API_URL or "http://localhost:8000"
API_PREFIX = "/api/v1"


# ==================== Test Functions ====================

async def test_api_health():
    """Проверка health check endpoint"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST: API Health Check")
    logger.info("=" * 80)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{API_BASE_URL}/health")
            
            if response.status_code == 200:
                logger.info(f"✅ API is healthy: {response.json()}")
                return True
            else:
                logger.error(f"❌ API health check failed: {response.status_code}")
                return False
                
    except httpx.ConnectError:
        logger.error(f"❌ Cannot connect to API at {API_BASE_URL}")
        logger.error("   Make sure backend is running: uvicorn main:app --reload")
        return False
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return False


async def test_create_article(article: str, user_id: str = "test-user-123"):
    """Тест создания артикула через API"""
    logger.info("\n" + "=" * 80)
    logger.info(f"TEST: Create Article via API (Article: {article})")
    logger.info("=" * 80)
    
    try:
        async with httpx.AsyncClient(timeout=180.0) as client:  # Увеличенный timeout для парсинга
            payload = {
                "article_number": article,
                "user_id": user_id
            }
            
            logger.info(f"Sending POST {API_BASE_URL}{API_PREFIX}/articles/")
            logger.info(f"Payload: {payload}")
            
            response = await client.post(
                f"{API_BASE_URL}{API_PREFIX}/articles/",
                json=payload
            )
            
            if response.status_code == 201:
                data = response.json()
                logger.info(f"✅ Article created successfully:")
                logger.info(f"   • ID: {data.get('id')}")
                logger.info(f"   • Article: {data.get('article_number')}")
                logger.info(f"   • Name: {data.get('name', 'N/A')}")
                logger.info(f"   • Price: {data.get('price', 'N/A')} руб")
                logger.info(f"   • Status: {data.get('status')}")
                return data.get('id')
            elif response.status_code == 409:
                logger.warning(f"⚠️  Article already exists (this is OK)")
                # Пробуем получить существующий артикул
                return await test_get_existing_article(article, user_id)
            elif response.status_code == 404:
                logger.error(f"❌ Product not found in OZON: {article}")
                logger.error(f"   Response: {response.text}")
                return None
            else:
                logger.error(f"❌ Failed to create article: {response.status_code}")
                logger.error(f"   Response: {response.text}")
                return None
                
    except httpx.TimeoutException:
        logger.error(f"❌ Request timeout (parsing took too long)")
        return None
    except Exception as e:
        logger.error(f"❌ Create article failed: {e}", exc_info=True)
        return None


async def test_get_existing_article(article: str, user_id: str):
    """Получить существующий артикул"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Пробуем найти артикул через список
            response = await client.get(
                f"{API_BASE_URL}{API_PREFIX}/articles/",
                params={"article_number": article, "user_id": user_id}
            )
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                if items:
                    return items[0].get("id")
            
            return None
    except Exception:
        return None


async def test_get_article(article_id: str):
    """Тест получения артикула через API"""
    logger.info("\n" + "=" * 80)
    logger.info(f"TEST: Get Article via API (ID: {article_id})")
    logger.info("=" * 80)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{API_BASE_URL}{API_PREFIX}/articles/{article_id}"
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Article retrieved successfully:")
                logger.info(f"   • Article: {data.get('article_number')}")
                logger.info(f"   • Name: {data.get('name', 'N/A')}")
                logger.info(f"   • Price: {data.get('price', 'N/A')} руб")
                logger.info(f"   • SPP Total: {data.get('spp_total', 'N/A')}")
                return True
            else:
                logger.error(f"❌ Failed to get article: {response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Get article failed: {e}")
        return False


async def test_check_article(article_id: str):
    """Тест проверки артикула через API"""
    logger.info("\n" + "=" * 80)
    logger.info(f"TEST: Check Article via API (ID: {article_id})")
    logger.info("=" * 80)
    
    try:
        async with httpx.AsyncClient(timeout=180.0) as client:  # Увеличенный timeout
            logger.info(f"Sending POST {API_BASE_URL}{API_PREFIX}/articles/{article_id}/check")
            
            response = await client.post(
                f"{API_BASE_URL}{API_PREFIX}/articles/{article_id}/check"
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Article checked successfully:")
                logger.info(f"   • Article: {data.get('article_number')}")
                logger.info(f"   • Price: {data.get('price', 'N/A')} руб")
                logger.info(f"   • Price changed: {data.get('price_changed', False)}")
                logger.info(f"   • Last check: {data.get('last_check', 'N/A')}")
                return True
            else:
                logger.error(f"❌ Failed to check article: {response.status_code}")
                logger.error(f"   Response: {response.text}")
                return False
                
    except httpx.TimeoutException:
        logger.error(f"❌ Request timeout (parsing took too long)")
        return False
    except Exception as e:
        logger.error(f"❌ Check article failed: {e}", exc_info=True)
        return False


async def test_price_endpoint(article: str):
    """Тест endpoint для получения цен"""
    logger.info("\n" + "=" * 80)
    logger.info(f"TEST: Price Endpoint (Article: {article})")
    logger.info("=" * 80)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{API_BASE_URL}{API_PREFIX}/prices/article/{article}"
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Price data retrieved:")
                logger.info(f"   • Current price: {data.get('current_price', 'N/A')} руб")
                logger.info(f"   • Average 7 days: {data.get('average_price_7days', 'N/A')} руб")
                return True
            elif response.status_code == 404:
                logger.warning(f"⚠️  No price data found (article may not be tracked)")
                return True  # Это нормально для новых артикулов
            else:
                logger.error(f"❌ Failed to get price: {response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Price endpoint failed: {e}")
        return False


# ==================== Main Test Runner ====================

async def main():
    """Главная функция тестирования"""
    logger.info("\n" + "=" * 80)
    logger.info("🧪 API INTEGRATION TEST SUITE")
    logger.info("=" * 80 + "\n")
    
    # Проверка что API доступен
    if not await test_api_health():
        logger.error("\n❌ API is not available. Please start backend:")
        logger.error("   cd backend && uvicorn main:app --reload")
        return
    
    # Получаем артикул для тестирования
    if len(sys.argv) > 1:
        article = sys.argv[1]
    else:
        article = "1669668169"  # Тестовый артикул
        logger.info(f"No article provided, using default: {article}")
    
    logger.info(f"\n📋 Running API integration tests with article: {article}\n")
    
    # Test 1: Create Article
    article_id = await test_create_article(article)
    
    if not article_id:
        logger.error("\n❌ Cannot proceed without article ID")
        return
    
    # Test 2: Get Article
    await test_get_article(article_id)
    
    # Test 3: Check Article (может занять время из-за парсинга)
    logger.info("\n⏳ This may take 30-120 seconds due to parsing...")
    await test_check_article(article_id)
    
    # Test 4: Price Endpoint
    await test_price_endpoint(article)
    
    logger.info("\n" + "=" * 80)
    logger.info("✅ API Integration Tests Completed")
    logger.info("=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Tests interrupted by user")
    except Exception as e:
        logger.critical(f"\n❌ Test suite crashed: {e}", exc_info=True)

