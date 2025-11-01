"""
Простой тест для проверки парсинга одного артикула
"""
import asyncio
import sys
from pathlib import Path

# Добавляем backend в path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))


async def test_article():
    print("=" * 80)
    print("🧪 Testing OZON Scraper with Article: 1066650955")
    print("=" * 80)
    print()

    try:
        from services.ozon_scraper import OzonScraper

        scraper = OzonScraper(
            cache_ttl=3600,
            rate_limit=5,
            timeout=30
        )

        try:
            article = "1066650955"
            print(f"📦 Fetching product info for article: {article}")
            print("⏳ This may take 10-15 seconds...")
            print()

            # Используем Playwright для максимальной защиты
            product = await scraper.get_product_info(
                article=article,
                force_playwright=True,
                use_cache=False
            )

            if product:
                print("✅ SUCCESS! Product found:")
                print("=" * 80)
                print(f"📦 Name: {product.name}")
                print(f"📝 Article: {product.article}")
                print(f"💰 Price: {product.price} ₽" if product.price else "💰 Price: Not available")
                print(f"💳 Normal Price: {product.normal_price} ₽" if product.normal_price else "💳 Normal Price: Not available")
                print(f"💳 Ozon Card Price: {product.ozon_card_price} ₽" if product.ozon_card_price else "💳 Ozon Card Price: Not available")
                print(f"📊 Availability: {product.availability.value}")
                print(f"🔧 Source: {product.source.value}")
                print(f"⏱️  Fetch time: {product.fetch_time_ms}ms" if product.fetch_time_ms else "")
                print(f"🔗 URL: {product.url}")
                print("=" * 80)
                print()

                # Статистика скрапера
                stats = scraper.get_stats()
                print("📊 Scraper Statistics:")
                print(f"   Total requests: {stats['total_requests']}")
                print(f"   Successful: {stats['successful_requests']}")
                print(f"   Failed: {stats['failed_requests']}")
                print(f"   Success rate: {stats['success_rate']}%")
                print(f"   Playwright requests: {stats['playwright_requests']}")
                print()

                print("✅ Test PASSED! Anti-detection improvements are working!")
                return True
            else:
                print("❌ FAILED: Product not found")
                print("   Possible reasons:")
                print("   - Article doesn't exist on OZON")
                print("   - Network connection issues")
                print("   - OZON blocking (despite anti-detection)")
                return False

        finally:
            await scraper.close()
            print("🔒 Scraper closed")

    except ImportError as e:
        print("❌ ERROR: Missing dependencies")
        print(f"   {e}")
        print()
        print("Please install required packages:")
        print("   pip install loguru playwright httpx beautifulsoup4")
        print("   playwright install chromium")
        return False

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(test_article())
    sys.exit(0 if result else 1)
