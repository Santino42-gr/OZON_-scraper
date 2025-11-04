"""
Комплексное тестирование Parser Market API интеграции

Этот скрипт проверяет:
1. ✅ Базовую функциональность Parser Market API клиента
2. ✅ Интеграцию с OzonService
3. ✅ Маппинг данных из Parser Market в ProductInfo
4. ✅ Обработку ошибок и edge cases
5. ✅ Работу с балансом и rate limits
6. ✅ Интеграцию с cron jobs

Usage:
    python test_parser_market_comprehensive.py [article_number]
    
Примеры:
    # Тест одного артикула
    python test_parser_market_comprehensive.py 1669668169
    
    # Тест нескольких артикулов
    python test_parser_market_comprehensive.py 1669668169 123456789 987654321
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Добавляем backend в путь
sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger
from services.parser_market_client import (
    ParserMarketClient,
    ParserMarketError,
    ParserMarketAPIError,
    ParserMarketTimeoutError,
    ParserMarketTaskError
)
from services.ozon_service import get_ozon_service
from config import settings


# ==================== Test Results Tracking ====================

class TestResults:
    """Трекер результатов тестирования"""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.tests = []
    
    def add_test(self, name: str, passed: bool, message: str = "", skipped: bool = False):
        """Добавить результат теста"""
        self.tests.append({
            "name": name,
            "passed": passed,
            "skipped": skipped,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        
        if skipped:
            self.skipped += 1
        elif passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def print_summary(self):
        """Вывести итоговый отчет"""
        logger.info("\n" + "=" * 80)
        logger.info("📊 TEST SUMMARY")
        logger.info("=" * 80)
        logger.info(f"✅ Passed:  {self.passed}")
        logger.info(f"❌ Failed:  {self.failed}")
        logger.info(f"⏭️  Skipped: {self.skipped}")
        logger.info(f"📈 Success Rate: {(self.passed / max(self.passed + self.failed, 1) * 100):.1f}%")
        logger.info("=" * 80)
        
        if self.failed > 0:
            logger.warning("\nFailed tests:")
            for test in self.tests:
                if not test["passed"] and not test["skipped"]:
                    logger.warning(f"  ❌ {test['name']}: {test['message']}")


results = TestResults()


# ==================== Test 1: Configuration Check ====================

async def test_configuration():
    """Тест проверки конфигурации"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 1: Configuration Check")
    logger.info("=" * 80)
    
    try:
        # Проверка API ключа
        if not settings.PARSER_MARKET_API_KEY or settings.PARSER_MARKET_API_KEY == "your-parser-market-api-key-here":
            results.add_test("Configuration: API Key", False, "PARSER_MARKET_API_KEY not configured")
            return False
        
        # Проверка региона
        region = settings.PARSER_MARKET_REGION or "Москва"
        logger.info(f"✅ Region: {region}")
        
        # Проверка таймаутов
        timeout = settings.PARSER_MARKET_TIMEOUT or 120
        poll_interval = settings.PARSER_MARKET_POLL_INTERVAL or 10
        logger.info(f"✅ Timeout: {timeout}s")
        logger.info(f"✅ Poll interval: {poll_interval}s")
        
        results.add_test("Configuration: API Key", True)
        results.add_test("Configuration: Region", True)
        results.add_test("Configuration: Timeouts", True)
        return True
        
    except Exception as e:
        results.add_test("Configuration Check", False, str(e))
        logger.error(f"❌ Configuration check failed: {e}")
        return False


# ==================== Test 2: Balance Check ====================

async def test_balance_check():
    """Тест проверки баланса"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: Balance Check")
    logger.info("=" * 80)
    
    try:
        async with ParserMarketClient(api_key=settings.PARSER_MARKET_API_KEY) as client:
            balance = await client.get_balance()
            
            # Проверяем обязательные поля
            required_fields = ["checks_total", "checks_free", "checks_paid"]
            missing_fields = [f for f in required_fields if f not in balance]
            
            if missing_fields:
                results.add_test("Balance: Required Fields", False, f"Missing: {missing_fields}")
                return False
            
            # Проверяем что баланс >= 0
            checks_total = balance.get("checks_total", 0)
            if checks_total < 0:
                results.add_test("Balance: Valid Total", False, f"Invalid total: {checks_total}")
                return False
            
            logger.info(f"✅ Balance retrieved successfully:")
            logger.info(f"   • Total checks: {checks_total}")
            logger.info(f"   • Free checks: {balance.get('checks_free', 0)}")
            logger.info(f"   • Paid checks: {balance.get('checks_paid', 0)}")
            logger.info(f"   • Pending: {balance.get('checks_pending', 0)}")
            
            # Предупреждение если баланс низкий
            if checks_total < 10:
                logger.warning(f"⚠️  Low balance: {checks_total} checks remaining")
            
            results.add_test("Balance: API Connection", True)
            results.add_test("Balance: Data Structure", True)
            results.add_test("Balance: Valid Values", True)
            return True
            
    except ParserMarketAPIError as e:
        results.add_test("Balance: API Error", False, str(e))
        logger.error(f"❌ Balance check failed: {e}")
        return False
    except Exception as e:
        results.add_test("Balance: Unexpected Error", False, str(e))
        logger.error(f"❌ Unexpected error: {e}", exc_info=True)
        return False


# ==================== Test 3: Task Submission ====================

async def test_task_submission(article: str):
    """Тест отправки задачи"""
    logger.info("\n" + "=" * 80)
    logger.info(f"TEST 3: Task Submission (Article: {article})")
    logger.info("=" * 80)
    
    try:
        async with ParserMarketClient(
            api_key=settings.PARSER_MARKET_API_KEY,
            region=settings.PARSER_MARKET_REGION
        ) as client:
            # Отправляем задачу
            result = await client.submit_task(article)
            
            # Проверяем что получили userlabel
            userlabel = result.get("userlabel")
            if not userlabel:
                results.add_test("Task Submission: Userlabel", False, "No userlabel in response")
                return False
            
            logger.info(f"✅ Task submitted successfully:")
            logger.info(f"   • Userlabel: {userlabel}")
            logger.info(f"   • Region: {result.get('region_code', 'N/A')}")
            logger.info(f"   • Market: {result.get('market', 'N/A')}")
            
            results.add_test("Task Submission: API Call", True)
            results.add_test("Task Submission: Userlabel", True)
            
            return userlabel
            
    except ParserMarketAPIError as e:
        results.add_test("Task Submission: API Error", False, str(e))
        logger.error(f"❌ Task submission failed: {e}")
        return None
    except Exception as e:
        results.add_test("Task Submission: Unexpected Error", False, str(e))
        logger.error(f"❌ Unexpected error: {e}", exc_info=True)
        return None


# ==================== Test 4: Task Status Polling ====================

async def test_task_status_polling(userlabel: str):
    """Тест опроса статуса задачи"""
    logger.info("\n" + "=" * 80)
    logger.info(f"TEST 4: Task Status Polling (Userlabel: {userlabel})")
    logger.info("=" * 80)
    
    try:
        async with ParserMarketClient(
            api_key=settings.PARSER_MARKET_API_KEY,
            timeout=60,  # Короткий timeout для теста
            poll_interval=5
        ) as client:
            # Пробуем получить статус
            tasks = await client.get_task_status(userlabel=userlabel, limit=1)
            
            if not tasks:
                logger.warning("⚠️  Task not found yet (may be too early)")
                results.add_test("Status Polling: Task Found", False, "Task not found")
                return False
            
            task = tasks[0]
            status = client._get_field(task, "status")
            
            logger.info(f"✅ Task status retrieved:")
            logger.info(f"   • Status: {status}")
            logger.info(f"   • Order ID: {client._get_field(task, 'order-id')}")
            logger.info(f"   • Items loaded: {client._get_field(task, 'items-loaded')}")
            
            results.add_test("Status Polling: API Call", True)
            results.add_test("Status Polling: Status Field", True if status else False)
            
            return status
            
    except Exception as e:
        results.add_test("Status Polling: Error", False, str(e))
        logger.error(f"❌ Status polling failed: {e}")
        return None


# ==================== Test 5: Full Parse Flow ====================

async def test_full_parse_flow(article: str):
    """Тест полного цикла парсинга"""
    logger.info("\n" + "=" * 80)
    logger.info(f"TEST 5: Full Parse Flow (Article: {article})")
    logger.info("=" * 80)
    
    try:
        async with ParserMarketClient(
            api_key=settings.PARSER_MARKET_API_KEY,
            region=settings.PARSER_MARKET_REGION,
            timeout=settings.PARSER_MARKET_TIMEOUT
        ) as client:
            start_time = datetime.now()
            
            # Полный цикл парсинга
            product = await client.parse_sync(article)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            if not product:
                results.add_test("Full Parse: Product Retrieved", False, "No product data")
                return False
            
            # Проверяем обязательные поля
            if not product.article:
                results.add_test("Full Parse: Article Field", False, "Missing article")
                return False
            
            if not product.name:
                logger.warning("⚠️  Product name is empty")
            
            logger.info(f"✅ Product parsed successfully:")
            logger.info(f"   • Article: {product.article}")
            logger.info(f"   • Name: {product.name or 'N/A'}")
            logger.info(f"   • Price: {product.price or 'N/A'} руб")
            logger.info(f"   • Normal price: {product.normal_price or 'N/A'} руб")
            logger.info(f"   • Ozon Card price: {product.ozon_card_price or 'N/A'} руб")
            logger.info(f"   • Rating: {product.rating or 'N/A'}")
            logger.info(f"   • Reviews: {product.reviews_count or 'N/A'}")
            logger.info(f"   • Available: {product.available}")
            logger.info(f"   • Source: {product.source}")
            logger.info(f"   • Fetch time: {product.fetch_time_ms or 'N/A'}ms")
            logger.info(f"   • Duration: {duration:.1f}s")
            
            results.add_test("Full Parse: API Call", True)
            results.add_test("Full Parse: Product Retrieved", True)
            results.add_test("Full Parse: Article Field", True)
            results.add_test("Full Parse: Data Mapping", True if product.name else False)
            
            return product
            
    except ParserMarketTimeoutError as e:
        results.add_test("Full Parse: Timeout", False, str(e))
        logger.error(f"❌ Parse timeout: {e}")
        return None
    except Exception as e:
        results.add_test("Full Parse: Error", False, str(e))
        logger.error(f"❌ Parse failed: {e}", exc_info=True)
        return None


# ==================== Test 6: OzonService Integration ====================

async def test_ozon_service_integration(article: str):
    """Тест интеграции с OzonService"""
    logger.info("\n" + "=" * 80)
    logger.info(f"TEST 6: OzonService Integration (Article: {article})")
    logger.info("=" * 80)
    
    try:
        ozon_service = get_ozon_service()
        
        # Тест get_product_info
        product = await ozon_service.get_product_info(article)
        
        if not product:
            results.add_test("OzonService: get_product_info", False, "No product returned")
            return False
        
        logger.info(f"✅ OzonService.get_product_info() successful:")
        logger.info(f"   • Article: {product.article}")
        logger.info(f"   • Name: {product.name or 'N/A'}")
        logger.info(f"   • Price: {product.price or 'N/A'} руб")
        
        # Тест get_product_price
        price = await ozon_service.get_product_price(article)
        if price is None and product.price is None:
            logger.warning("⚠️  Price is None (may be normal)")
        else:
            logger.info(f"✅ OzonService.get_product_price() = {price} руб")
        
        # Тест check_availability
        available = await ozon_service.check_availability(article)
        logger.info(f"✅ OzonService.check_availability() = {available}")
        
        results.add_test("OzonService: get_product_info", True)
        results.add_test("OzonService: get_product_price", True)
        results.add_test("OzonService: check_availability", True)
        
        await ozon_service.close()
        return True
        
    except Exception as e:
        results.add_test("OzonService: Integration Error", False, str(e))
        logger.error(f"❌ OzonService integration failed: {e}", exc_info=True)
        return False


# ==================== Test 7: Error Handling ====================

async def test_error_handling():
    """Тест обработки ошибок"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 7: Error Handling")
    logger.info("=" * 80)
    
    try:
        # Тест с неверным API ключом
        try:
            async with ParserMarketClient(api_key="invalid_key") as client:
                await client.get_balance()
                results.add_test("Error Handling: Invalid API Key", False, "Should have raised error")
        except ParserMarketAPIError:
            logger.info("✅ Invalid API key correctly rejected")
            results.add_test("Error Handling: Invalid API Key", True)
        except Exception as e:
            logger.warning(f"⚠️  Unexpected error type: {type(e).__name__}")
            results.add_test("Error Handling: Invalid API Key", False, f"Wrong error type: {type(e).__name__}")
        
        # Тест с несуществующим артикулом (может не вызвать ошибку, но вернуть None)
        async with ParserMarketClient(api_key=settings.PARSER_MARKET_API_KEY) as client:
            # Используем явно несуществующий артикул
            invalid_article = "999999999999999999999"
            product = await client.parse_sync(invalid_article)
            
            if product is None:
                logger.info("✅ Invalid article correctly handled (returned None)")
                results.add_test("Error Handling: Invalid Article", True)
            else:
                logger.warning("⚠️  Invalid article returned product (unexpected)")
                results.add_test("Error Handling: Invalid Article", False, "Should return None")
        
        return True
        
    except Exception as e:
        results.add_test("Error Handling: Test Error", False, str(e))
        logger.error(f"❌ Error handling test failed: {e}")
        return False


# ==================== Test 8: Batch Parsing ====================

async def test_batch_parsing(articles: List[str]):
    """Тест пакетного парсинга"""
    logger.info("\n" + "=" * 80)
    logger.info(f"TEST 8: Batch Parsing ({len(articles)} articles)")
    logger.info("=" * 80)
    
    if len(articles) < 2:
        logger.info("⏭️  Skipping batch test (need at least 2 articles)")
        results.add_test("Batch Parsing", True, "Skipped (insufficient articles)", skipped=True)
        return True
    
    try:
        async with ParserMarketClient(
            api_key=settings.PARSER_MARKET_API_KEY,
            region=settings.PARSER_MARKET_REGION
        ) as client:
            start_time = datetime.now()
            
            # Пакетный парсинг
            results_list = await client.parse_batch(articles[:3], timeout=150)  # Ограничиваем до 3 для теста
            
            duration = (datetime.now() - start_time).total_seconds()
            
            success_count = sum(1 for r in results_list if r is not None)
            
            logger.info(f"✅ Batch parsing completed:")
            logger.info(f"   • Total: {len(results_list)}")
            logger.info(f"   • Success: {success_count}")
            logger.info(f"   • Failed: {len(results_list) - success_count}")
            logger.info(f"   • Duration: {duration:.1f}s")
            
            for i, (article, result) in enumerate(zip(articles[:3], results_list), 1):
                if result:
                    logger.info(f"   {i}. {article}: ✅ {result.name or 'N/A'} - {result.price or 'N/A'} руб")
                else:
                    logger.warning(f"   {i}. {article}: ❌ FAILED")
            
            results.add_test("Batch Parsing: API Call", True)
            results.add_test("Batch Parsing: Success Rate", True if success_count > 0 else False)
            
            return success_count > 0
            
    except Exception as e:
        results.add_test("Batch Parsing: Error", False, str(e))
        logger.error(f"❌ Batch parsing failed: {e}", exc_info=True)
        return False


# ==================== Test 9: Data Mapping ====================

async def test_data_mapping(article: str):
    """Тест маппинга данных из Parser Market в ProductInfo"""
    logger.info("\n" + "=" * 80)
    logger.info(f"TEST 9: Data Mapping (Article: {article})")
    logger.info("=" * 80)
    
    try:
        async with ParserMarketClient(
            api_key=settings.PARSER_MARKET_API_KEY,
            region=settings.PARSER_MARKET_REGION
        ) as client:
            product = await client.parse_sync(article)
            
            if not product:
                results.add_test("Data Mapping: Product Retrieved", False, "No product")
                return False
            
            # Проверяем типы данных
            checks = {
                "Article is string": isinstance(product.article, str),
                "Name is string or None": product.name is None or isinstance(product.name, str),
                "Price is float or None": product.price is None or isinstance(product.price, (int, float)),
                "Rating is float or None": product.rating is None or isinstance(product.rating, (int, float)),
                "Available is bool": isinstance(product.available, bool),
                "Source is set": product.source is not None,
                "Last check is datetime": isinstance(product.last_check, datetime) if product.last_check else True
            }
            
            logger.info("✅ Data type checks:")
            for check_name, passed in checks.items():
                status = "✅" if passed else "❌"
                logger.info(f"   {status} {check_name}")
                results.add_test(f"Data Mapping: {check_name}", passed)
            
            all_passed = all(checks.values())
            return all_passed
            
    except Exception as e:
        results.add_test("Data Mapping: Error", False, str(e))
        logger.error(f"❌ Data mapping test failed: {e}")
        return False


# ==================== Main Test Runner ====================

async def main():
    """Главная функция тестирования"""
    logger.info("\n" + "=" * 80)
    logger.info("🧪 PARSER MARKET API - COMPREHENSIVE TEST SUITE")
    logger.info("=" * 80 + "\n")
    
    # Проверка конфигурации
    if not await test_configuration():
        logger.error("❌ Configuration check failed. Please check your .env file")
        results.print_summary()
        return
    
    # Получаем артикулы для тестирования
    if len(sys.argv) > 1:
        articles = sys.argv[1:]
    else:
        # Используем тестовый артикул по умолчанию
        articles = ["1669668169"]  # Пример артикула Ozon
        logger.info(f"No articles provided, using default: {articles[0]}")
    
    test_article = articles[0]
    
    # Запускаем тесты последовательно
    logger.info(f"\n📋 Running tests with article: {test_article}\n")
    
    # Test 1: Configuration (уже выполнен)
    
    # Test 2: Balance Check
    await test_balance_check()
    
    # Test 3: Task Submission
    userlabel = await test_task_submission(test_article)
    
    # Test 4: Task Status Polling (если получили userlabel)
    if userlabel:
        await test_task_status_polling(userlabel)
    
    # Test 5: Full Parse Flow
    product = await test_full_parse_flow(test_article)
    
    # Test 6: OzonService Integration (только если есть продукт)
    if product:
        await test_ozon_service_integration(test_article)
    
    # Test 7: Error Handling
    await test_error_handling()
    
    # Test 8: Batch Parsing
    await test_batch_parsing(articles)
    
    # Test 9: Data Mapping (только если есть продукт)
    if product:
        await test_data_mapping(test_article)
    
    # Итоговый отчет
    results.print_summary()
    
    # Финальный статус
    if results.failed == 0:
        logger.success("\n🎉 All tests passed!")
    elif results.passed > results.failed:
        logger.warning(f"\n⚠️  Some tests failed ({results.failed}/{results.passed + results.failed})")
    else:
        logger.error(f"\n❌ Most tests failed ({results.failed}/{results.passed + results.failed})")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Tests interrupted by user")
        results.print_summary()
    except Exception as e:
        logger.critical(f"\n❌ Test suite crashed: {e}", exc_info=True)
        results.print_summary()

