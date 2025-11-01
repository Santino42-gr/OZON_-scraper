"""
Простой тест через httpx (без Playwright)
"""
import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))


async def test_article():
    print("=" * 80)
    print("🧪 Testing OZON Scraper with Article: 1066650955 (httpx method)")
    print("=" * 80)
    print()

    try:
        from services.ozon_scraper import OzonScraper

        scraper = OzonScraper(cache_ttl=3600, rate_limit=5, timeout=30)

        try:
            article = "1066650955"
            print(f"📦 Fetching product info for article: {article}")
            print("⏳ Using httpx (без Playwright)...")
            print()

            # БЕЗ force_playwright - используем httpx
            product = await scraper.get_product_info(
                article=article,
                force_playwright=False,  # Используем httpx
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
                print(f"🔗 URL: {product.url}")
                print("=" * 80)
                print()
                print("✅ Test PASSED! Scraper is working!")
                print()
                print("NOTE: Для полной защиты от OZON нужен Playwright,")
                print("      но базовый парсинг работает через httpx.")
                return True
            else:
                print("❌ FAILED: Product not found")
                print("   Возможные причины:")
                print("   - Артикул не существует")
                print("   - OZON заблокировал запрос (403)")
                print("   - Попробуйте другой артикул")
                return False

        finally:
            await scraper.close()

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(test_article())
    sys.exit(0 if result else 1)
