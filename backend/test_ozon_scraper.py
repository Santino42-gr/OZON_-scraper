"""
Test script for OZON Scraper

Проверка всей функциональности OzonScraper с реальными запросами.
"""

import asyncio
import sys
from pathlib import Path

# Добавляем backend в путь
sys.path.insert(0, str(Path(__file__).parent))

from services.ozon_scraper import OzonScraper
from loguru import logger


async def test_basic_scraping():
    """Тест базового scraping"""
    print("\n" + "="*60)
    print("🧪 Test 1: Basic Product Scraping")
    print("="*60)
    
    scraper = OzonScraper(cache_ttl=0)  # Отключаем кэш для теста
    
    try:
        # Тестовый артикул (можно заменить на реальный)
        test_article = "123456789"
        
        print(f"\n📦 Scraping product: {test_article}")
        
        product = await scraper.get_product_info(test_article, use_cache=False)
        
        if product:
            print(f"\n✅ Product found:")
            print(f"   Article: {product.article}")
            print(f"   Name: {product.name}")
            print(f"   Price: {product.price} ₽")
            print(f"   Availability: {product.availability}")
            print(f"   Source: {product.source}")
            print(f"   Fetch time: {product.fetch_time_ms}ms")
        else:
            print(f"\n⚠️  Product not found: {test_article}")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await scraper.close()


async def test_cache():
    """Тест кэширования"""
    print("\n" + "="*60)
    print("🧪 Test 2: Caching")
    print("="*60)
    
    scraper = OzonScraper(cache_ttl=300)  # 5 минут
    
    try:
        test_article = "123456789"
        
        # Первый запрос (без кэша)
        print(f"\n1️⃣  First request (no cache)...")
        from datetime import datetime
        start1 = datetime.now()
        product1 = await scraper.get_product_info(test_article)
        time1 = (datetime.now() - start1).total_seconds()
        print(f"   Time: {time1:.3f}s")
        
        # Второй запрос (из кэша)
        print(f"\n2️⃣  Second request (from cache)...")
        start2 = datetime.now()
        product2 = await scraper.get_product_info(test_article)
        time2 = (datetime.now() - start2).total_seconds()
        print(f"   Time: {time2:.3f}s")
        
        # Проверка
        if time2 < time1 * 0.1:  # Кэш должен быть намного быстрее
            print(f"\n✅ Cache test PASSED! Cache is {time1/time2:.1f}x faster")
        else:
            print(f"\n⚠️  Cache might not be working properly")
        
        # Статистика
        stats = scraper.get_stats()
        print(f"\n📊 Stats:")
        print(f"   Cache hits: {stats['cache_hits']}")
        print(f"   Cache misses: {stats['cache_misses']}")
        print(f"   Cache hit rate: {stats['cache_hit_rate']}%")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    finally:
        await scraper.close()


async def test_rate_limiter():
    """Тест Rate Limiter"""
    print("\n" + "="*60)
    print("🧪 Test 3: Rate Limiter")
    print("="*60)
    
    from services.ozon_scraper import RateLimiter
    from datetime import datetime
    
    limiter = RateLimiter(max_requests=5, time_window=10)
    
    print(f"\n⏱️  Making 7 requests (limit: 5 req / 10s)...")
    
    start_time = datetime.now()
    
    for i in range(7):
        await limiter.acquire()
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"   Request {i+1}/7 at {elapsed:.2f}s")
    
    total_time = (datetime.now() - start_time).total_seconds()
    
    print(f"\n✅ Rate Limiter test completed!")
    print(f"   Total time: {total_time:.2f}s")
    print(f"   Expected: ~10s+ for 7 requests")


async def test_detailed_prices():
    """Тест получения детальных цен"""
    print("\n" + "="*60)
    print("🧪 Test 4: Detailed Prices")
    print("="*60)
    
    scraper = OzonScraper()
    
    try:
        test_article = "123456789"
        
        print(f"\n💰 Getting detailed prices for: {test_article}")
        
        prices = await scraper.get_product_prices_detailed(test_article)
        
        if prices:
            print(f"\n✅ Prices found:")
            print(f"   Article: {prices.article}")
            print(f"   Current price: {prices.price} ₽")
            print(f"   Normal price (no card): {prices.normal_price} ₽")
            print(f"   Ozon Card price: {prices.ozon_card_price} ₽")
            print(f"   Old price: {prices.old_price} ₽")
            print(f"   Average 7 days: {prices.average_price_7days} ₽")
        else:
            print(f"\n⚠️  Prices not found")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    finally:
        await scraper.close()


async def test_batch_scraping():
    """Тест batch scraping"""
    print("\n" + "="*60)
    print("🧪 Test 5: Batch Scraping")
    print("="*60)
    
    scraper = OzonScraper()
    
    try:
        # Список тестовых артикулов
        articles = ["123456789", "987654321", "111222333"]
        
        print(f"\n📦 Batch scraping {len(articles)} products...")
        
        results = await scraper.scrape_multiple_products(articles)
        
        print(f"\n✅ Results:")
        for article, product in results.items():
            status = "✅ Found" if product else "❌ Not found"
            print(f"   {article}: {status}")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    finally:
        await scraper.close()


async def test_statistics():
    """Тест статистики"""
    print("\n" + "="*60)
    print("🧪 Test 6: Statistics")
    print("="*60)
    
    scraper = OzonScraper()
    
    try:
        # Делаем несколько запросов
        articles = ["123456789", "987654321"]
        
        for article in articles:
            await scraper.get_product_info(article)
        
        # Показываем статистику
        print("\n")
        scraper.print_stats()
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    finally:
        await scraper.close()


async def main():
    """Главная функция тестирования"""
    print("\n" + "="*80)
    print("🚀 OZON Scraper - Complete Test Suite")
    print("="*80)
    
    try:
        # Тест 1: Базовый scraping
        await test_basic_scraping()
        
        # Тест 2: Кэширование
        await test_cache()
        
        # Тест 3: Rate Limiter
        await test_rate_limiter()
        
        # Тест 4: Детальные цены
        await test_detailed_prices()
        
        # Тест 5: Batch scraping
        await test_batch_scraping()
        
        # Тест 6: Статистика
        await test_statistics()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS COMPLETED!")
        print("="*80)
        print("\n⚠️  NOTE: Some tests may fail if test articles don't exist on OZON")
        print("⚠️  Replace test articles with real OZON product IDs for accurate testing")
        print("\n")
        
    except KeyboardInterrupt:
        print("\n\n⏸️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Запуск тестов
    asyncio.run(main())

