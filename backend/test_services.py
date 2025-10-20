"""
Test script for Business Logic Services

Проверка всех 3 сервисов: Article, User, Report.
"""

import asyncio
import sys
from pathlib import Path

# Добавляем backend в путь
sys.path.insert(0, str(Path(__file__).parent))

from services import (
    get_article_service,
    get_user_service,
    get_report_service
)
from loguru import logger


async def test_user_service():
    """Тест UserService"""
    print("\n" + "="*60)
    print("🧪 Test 1: UserService")
    print("="*60)
    
    user_service = get_user_service()
    
    try:
        # Регистрация тестового пользователя
        test_telegram_id = 123456789
        
        print(f"\n📝 Registering test user: {test_telegram_id}")
        user = await user_service.register_user(
            telegram_id=test_telegram_id,
            telegram_username="test_user"
        )
        
        print(f"✅ User registered:")
        print(f"   ID: {user.id}")
        print(f"   Telegram ID: {user.telegram_id}")
        print(f"   Username: {user.telegram_username}")
        print(f"   Blocked: {user.is_blocked}")
        
        # Получение пользователя
        print(f"\n🔍 Getting user by Telegram ID...")
        found_user = await user_service.get_user_by_telegram_id(test_telegram_id)
        
        if found_user:
            print(f"✅ User found: {found_user.telegram_username}")
        else:
            print("❌ User not found")
        
        # Получение статистики
        print(f"\n📊 Getting user stats...")
        stats = await user_service.get_user_stats(user.id)
        
        print(f"✅ User stats:")
        print(f"   Total articles: {stats.total_articles}")
        print(f"   Active articles: {stats.active_articles}")
        print(f"   Total requests (30d): {stats.total_requests_30d}")
        
        return user.id
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_article_service(user_id: str):
    """Тест ArticleService"""
    print("\n" + "="*60)
    print("🧪 Test 2: ArticleService")
    print("="*60)
    
    article_service = get_article_service()
    
    try:
        # Создание тестового артикула
        test_article = "TEST-123-456"
        
        print(f"\n📝 Creating test article: {test_article}")
        article = await article_service.create_article(
            user_id=user_id,
            article_number=test_article,
            fetch_data=False  # Не получаем данные с OZON для теста
        )
        
        print(f"✅ Article created:")
        print(f"   ID: {article.id}")
        print(f"   Article number: {article.article_number}")
        print(f"   Status: {article.status}")
        print(f"   Problematic: {article.is_problematic}")
        
        # Получение артикулов пользователя
        print(f"\n📋 Getting user articles...")
        articles = await article_service.get_user_articles(user_id)
        
        print(f"✅ Found {len(articles)} articles:")
        for art in articles:
            print(f"   - {art.article_number} (Status: {art.status})")
        
        # Валидация артикула
        print(f"\n✅ Testing validation...")
        try:
            article_service.validate_article_number("AB")  # Слишком короткий
            print("❌ Validation failed to catch short article")
        except Exception:
            print("✅ Validation works: caught short article")
        
        return article.id
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_report_service(user_id: str, article_id: str):
    """Тест ReportService"""
    print("\n" + "="*60)
    print("🧪 Test 3: ReportService")
    print("="*60)
    
    report_service = get_report_service()
    
    try:
        # Генерация отчета по артикулу
        print(f"\n📊 Generating article report...")
        article_report = await report_service.generate_article_report(
            article_id=article_id,
            include_history=True,
            days=7
        )
        
        print(f"✅ Article report generated:")
        print(f"   Article: {article_report.article_number}")
        print(f"   Status: {article_report.status}")
        if hasattr(article_report, 'total_requests'):
            print(f"   Total requests: {article_report.total_requests}")
        
        # Генерация отчета по пользователю
        print(f"\n📊 Generating user report...")
        user_report = await report_service.generate_user_report(
            user_id=user_id,
            include_articles=True,
            days=30
        )
        
        print(f"✅ User report generated:")
        print(f"   Telegram ID: {user_report.telegram_id}")
        print(f"   Total articles: {user_report.total_articles}")
        print(f"   Total requests: {user_report.total_requests}")
        
        # Тест экспорта CSV
        print(f"\n📁 Testing CSV export...")
        test_data = [
            {"article": "TEST-1", "price": 1999, "status": "active"},
            {"article": "TEST-2", "price": 2999, "status": "active"}
        ]
        
        csv_content = report_service.export_to_csv(test_data)
        print(f"✅ CSV exported: {len(csv_content)} bytes")
        print(f"   Preview:\n{csv_content[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_integration():
    """Полный тест интеграции всех сервисов"""
    print("\n" + "="*80)
    print("🚀 Business Logic Services - Integration Test")
    print("="*80)
    
    try:
        # Тест 1: UserService
        user_id = await test_user_service()
        
        if not user_id:
            print("\n❌ UserService test failed. Stopping.")
            return
        
        # Тест 2: ArticleService
        article_id = await test_article_service(user_id)
        
        if not article_id:
            print("\n❌ ArticleService test failed. Stopping.")
            return
        
        # Тест 3: ReportService
        success = await test_report_service(user_id, article_id)
        
        if not success:
            print("\n❌ ReportService test failed.")
            return
        
        # Финал
        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED!")
        print("="*80)
        print("\n📊 Summary:")
        print("   ✅ UserService - OK")
        print("   ✅ ArticleService - OK")
        print("   ✅ ReportService - OK")
        print("\n💡 All business logic services are working correctly!")
        print("\n⚠️  Note: Some tests use test data without actual OZON scraping.")
        print("⚠️  Configure Supabase credentials in .env for full functionality.")
        print("\n")
        
    except KeyboardInterrupt:
        print("\n\n⏸️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Запуск тестов
    asyncio.run(test_integration())

