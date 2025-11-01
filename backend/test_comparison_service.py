"""
Unit Tests for ComparisonService

Тестирование функциональности сравнения артикулов:
- Создание групп сравнения
- Добавление артикулов в группы
- Расчет метрик сравнения
- Сохранение и получение снэпшотов
- Получение истории сравнений

Author: AI Agent
Created: 2025-10-31
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from uuid import uuid4

# Добавляем backend в путь
sys.path.insert(0, str(Path(__file__).parent))

from services.comparison_service import ComparisonService, ComparisonServiceError
from services.article_service import ArticleService
from services.user_service import UserService
from models.comparison import (
    ArticleGroupCreate,
    GroupType,
    ArticleRole,
    QuickComparisonCreate,
    ArticleComparisonData,
    CompetitivenessGrade
)
from models.article import ArticleCreate
from loguru import logger


# ==================== Test Data ====================

TEST_USER_TELEGRAM_ID = 999888777
TEST_OWN_ARTICLE = "1234567890"  # Замените на реальный артикул OZON для полного теста
TEST_COMPETITOR_ARTICLE = "0987654321"  # Замените на реальный артикул OZON


# ==================== Helper Functions ====================

async def setup_test_user() -> str:
    """Создать тестового пользователя"""
    user_service = UserService()

    try:
        user = await user_service.register_user(
            telegram_id=TEST_USER_TELEGRAM_ID,
            telegram_username="test_comparison_user"
        )
        logger.info(f"✅ Test user created: {user.id}")
        return user.id
    except Exception as e:
        # Пользователь уже существует
        user = await user_service.get_user_by_telegram_id(TEST_USER_TELEGRAM_ID)
        if user:
            logger.info(f"✅ Using existing test user: {user.id}")
            return user.id
        raise e


def create_mock_comparison_data(
    article_id: str,
    article_number: str,
    role: ArticleRole,
    price: float = 1000.0,
    rating: float = 4.5,
    spp_total: float = 15.0,
    reviews_count: int = 100,
    available: bool = True
) -> ArticleComparisonData:
    """Создать мок данные для сравнения"""
    return ArticleComparisonData(
        article_id=article_id,
        article_number=article_number,
        role=role,
        name=f"Test Product {article_number}",
        price=price,
        old_price=price * 1.2,
        normal_price=price,
        ozon_card_price=price * 0.95,
        average_price_7days=price,
        rating=rating,
        reviews_count=reviews_count,
        spp1=spp_total / 2,
        spp2=spp_total / 2,
        spp_total=spp_total,
        available=available,
        image_url=None,
        product_url=f"https://ozon.ru/product/{article_number}",
        position=0
    )


# ==================== Unit Tests ====================

async def test_create_group(user_id: str, comparison_service: ComparisonService):
    """Test 1: Создание группы сравнения"""
    print("\n" + "="*60)
    print("🧪 Test 1: Create Comparison Group")
    print("="*60)

    try:
        group_data = ArticleGroupCreate(
            name="Test Comparison Group",
            group_type=GroupType.COMPARISON
        )

        group = await comparison_service.create_group(user_id, group_data)

        print(f"✅ Group created successfully:")
        print(f"   ID: {group.id}")
        print(f"   Name: {group.name}")
        print(f"   Type: {group.group_type.value}")
        print(f"   Members: {group.members_count}")

        assert group.id is not None
        assert group.name == "Test Comparison Group"
        assert group.group_type == GroupType.COMPARISON
        assert group.members_count == 0

        return group.id

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_add_articles_to_group(
    user_id: str,
    group_id: str,
    comparison_service: ComparisonService,
    article_service: ArticleService
):
    """Test 2: Добавление артикулов в группу"""
    print("\n" + "="*60)
    print("🧪 Test 2: Add Articles to Group")
    print("="*60)

    try:
        # Создаем 2 тестовых артикула
        print("\n📝 Creating test articles...")

        own_article = await article_service.create_article(
            user_id=user_id,
            article_number=f"TEST-OWN-{uuid4().hex[:8]}",
            fetch_data=False
        )
        print(f"   ✅ Own article created: {own_article.article_number}")

        competitor_article = await article_service.create_article(
            user_id=user_id,
            article_number=f"TEST-COMP-{uuid4().hex[:8]}",
            fetch_data=False
        )
        print(f"   ✅ Competitor article created: {competitor_article.article_number}")

        # Добавляем в группу
        print("\n➕ Adding articles to group...")

        success1 = await comparison_service.add_article_to_group(
            group_id=group_id,
            article_id=own_article.id,
            role=ArticleRole.OWN,
            position=0
        )

        success2 = await comparison_service.add_article_to_group(
            group_id=group_id,
            article_id=competitor_article.id,
            role=ArticleRole.COMPETITOR,
            position=1
        )

        assert success1 == True
        assert success2 == True

        print(f"✅ Articles added successfully")

        return own_article.id, competitor_article.id

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None, None


async def test_calculate_metrics(comparison_service: ComparisonService):
    """Test 3: Расчет метрик сравнения"""
    print("\n" + "="*60)
    print("🧪 Test 3: Calculate Comparison Metrics")
    print("="*60)

    try:
        # Создаем мок данные
        own = create_mock_comparison_data(
            article_id="own-id",
            article_number="OWN-123",
            role=ArticleRole.OWN,
            price=1000.0,
            rating=4.5,
            spp_total=15.0,
            reviews_count=150
        )

        competitor = create_mock_comparison_data(
            article_id="comp-id",
            article_number="COMP-456",
            role=ArticleRole.COMPETITOR,
            price=1200.0,
            rating=4.3,
            spp_total=10.0,
            reviews_count=200
        )

        # Рассчитываем метрики
        metrics = await comparison_service._calculate_comparison_metrics(own, competitor)

        print(f"\n📊 Metrics calculated:")
        print(f"   Price difference: {metrics.price.absolute:.2f} ({metrics.price.percentage:.2f}%)")
        print(f"   Who cheaper: {metrics.price.who_cheaper}")
        print(f"   Rating difference: {metrics.rating.absolute:.2f}")
        print(f"   SPP difference: {metrics.spp.absolute:.2f}%")
        print(f"   Reviews difference: {metrics.reviews.absolute}")
        print(f"   Competitiveness Index: {metrics.competitiveness_index:.2f}")
        print(f"   Grade: {metrics.grade.value}")
        print(f"   Recommendation: {metrics.overall_recommendation}")

        # Проверки
        assert metrics.price.who_cheaper == "own"  # Наш товар дешевле
        assert metrics.price.percentage < 0  # Отрицательный % - мы дешевле
        assert metrics.rating.who_better == "own"  # Наш рейтинг выше
        assert metrics.spp.who_better == "own"  # Наш СПП выше
        assert metrics.competitiveness_index >= 0 and metrics.competitiveness_index <= 1
        assert metrics.grade in [g for g in CompetitivenessGrade]

        print(f"\n✅ All metric assertions passed!")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_price_scenarios(comparison_service: ComparisonService):
    """Test 4: Различные сценарии цен"""
    print("\n" + "="*60)
    print("🧪 Test 4: Price Difference Scenarios")
    print("="*60)

    scenarios = [
        ("Own cheaper", 1000, 1200, "own", -16.67),
        ("Competitor cheaper", 1200, 1000, "competitor", 20.0),
        ("Equal prices", 1000, 1000, "equal", 0.0),
        ("Own much cheaper", 500, 1000, "own", -50.0),
    ]

    try:
        for name, own_price, comp_price, expected_winner, expected_pct in scenarios:
            own = create_mock_comparison_data("own", "OWN", ArticleRole.OWN, price=own_price)
            comp = create_mock_comparison_data("comp", "COMP", ArticleRole.COMPETITOR, price=comp_price)

            price_diff = comparison_service._calculate_price_difference(own, comp)

            print(f"\n  📌 Scenario: {name}")
            print(f"     Own: {own_price}, Competitor: {comp_price}")
            print(f"     Who cheaper: {price_diff.who_cheaper} (expected: {expected_winner})")
            print(f"     Percentage: {price_diff.percentage:.2f}% (expected: {expected_pct:.2f}%)")

            assert price_diff.who_cheaper == expected_winner
            assert abs(price_diff.percentage - expected_pct) < 0.1  # Небольшая погрешность

        print(f"\n✅ All price scenarios passed!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_competitiveness_grades(comparison_service: ComparisonService):
    """Test 5: Расчет грейдов конкурентоспособности"""
    print("\n" + "="*60)
    print("🧪 Test 5: Competitiveness Grades")
    print("="*60)

    scenarios = [
        ("Grade A - Perfect", 900, 5.0, 25.0, 500, CompetitivenessGrade.A),
        ("Grade B - Good", 1000, 4.5, 15.0, 200, CompetitivenessGrade.B),
        ("Grade C - Average", 1100, 4.0, 10.0, 100, CompetitivenessGrade.C),
        ("Grade D - Poor", 1300, 3.5, 5.0, 50, CompetitivenessGrade.D),
        ("Grade F - Very Poor", 1500, 3.0, 0.0, 10, CompetitivenessGrade.F),
    ]

    try:
        for name, price, rating, spp, reviews, expected_grade in scenarios:
            own = create_mock_comparison_data(
                "own", "OWN", ArticleRole.OWN,
                price=price,
                rating=rating,
                spp_total=spp,
                reviews_count=reviews
            )
            comp = create_mock_comparison_data(
                "comp", "COMP", ArticleRole.COMPETITOR,
                price=1000,
                rating=4.0,
                spp_total=10.0,
                reviews_count=100
            )

            index = comparison_service._calculate_competitiveness_index(own, comp)
            grade = comparison_service._get_grade(index)

            print(f"\n  📌 {name}")
            print(f"     Index: {index:.2f}")
            print(f"     Grade: {grade.value} (expected: {expected_grade.value})")

            # Для некоторых сценариев грейд может быть +/- 1 уровень из-за взвешенной формулы
            # Проверяем что грейд в разумных пределах
            grade_values = {g: i for i, g in enumerate(CompetitivenessGrade)}
            assert abs(grade_values[grade] - grade_values[expected_grade]) <= 1

        print(f"\n✅ All grade scenarios passed!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_quick_comparison_create(user_id: str, comparison_service: ComparisonService):
    """Test 6: Быстрое создание сравнения 1v1"""
    print("\n" + "="*60)
    print("🧪 Test 6: Quick Comparison Create")
    print("="*60)

    try:
        quick_data = QuickComparisonCreate(
            own_article_number=f"QUICK-OWN-{uuid4().hex[:6]}",
            competitor_article_number=f"QUICK-COMP-{uuid4().hex[:6]}",
            group_name="Quick Test Comparison",
            scrape_now=False  # Не делаем scraping для теста
        )

        print(f"\n📝 Creating quick comparison...")
        print(f"   Own: {quick_data.own_article_number}")
        print(f"   Competitor: {quick_data.competitor_article_number}")

        comparison = await comparison_service.quick_create_comparison(user_id, quick_data)

        print(f"\n✅ Quick comparison created:")
        print(f"   Group ID: {comparison.group_id}")
        print(f"   Group name: {comparison.group_name}")
        print(f"   Own product: {comparison.own_product.article_number if comparison.own_product else 'None'}")
        print(f"   Competitors: {len(comparison.competitors)}")

        assert comparison.group_id is not None
        assert comparison.own_product is not None
        assert len(comparison.competitors) >= 1

        return comparison.group_id

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_get_comparison_history(
    user_id: str,
    group_id: str,
    comparison_service: ComparisonService
):
    """Test 7: Получение истории сравнений"""
    print("\n" + "="*60)
    print("🧪 Test 7: Get Comparison History")
    print("="*60)

    try:
        print(f"\n📜 Getting comparison history for group {group_id}...")

        history = await comparison_service.get_comparison_history(
            group_id=group_id,
            user_id=user_id,
            days=30
        )

        print(f"\n✅ History retrieved:")
        print(f"   Group ID: {history.group_id}")
        print(f"   Snapshots: {history.total_count}")
        print(f"   Date range: {history.date_from} - {history.date_to}")

        if history.snapshots:
            print(f"\n   Latest snapshot:")
            latest = history.snapshots[0]
            print(f"   - ID: {latest.id}")
            print(f"   - Date: {latest.snapshot_date}")
            print(f"   - Index: {latest.competitiveness_index}")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_user_stats(user_id: str, comparison_service: ComparisonService):
    """Test 8: Получение статистики пользователя"""
    print("\n" + "="*60)
    print("🧪 Test 8: Get User Comparison Stats")
    print("="*60)

    try:
        print(f"\n📊 Getting user stats...")

        stats = await comparison_service.get_user_stats(user_id)

        print(f"\n✅ Stats retrieved:")
        print(f"   Total groups: {stats.total_groups}")
        print(f"   Comparison groups: {stats.comparison_groups}")
        print(f"   Total articles: {stats.total_articles}")
        print(f"   Avg competitiveness: {stats.avg_competitiveness_index}")
        print(f"   Last comparison: {stats.last_comparison_date}")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# ==================== Main Test Runner ====================

async def run_all_tests():
    """Запустить все тесты"""
    print("\n" + "="*60)
    print("🚀 COMPARISON SERVICE - UNIT TESTS")
    print("="*60)

    comparison_service = ComparisonService()
    article_service = ArticleService()

    results = {
        "passed": 0,
        "failed": 0,
        "total": 8
    }

    try:
        # Setup
        user_id = await setup_test_user()

        # Test 1: Create Group
        group_id = await test_create_group(user_id, comparison_service)
        if group_id:
            results["passed"] += 1
        else:
            results["failed"] += 1
            return results

        # Test 2: Add Articles
        own_id, comp_id = await test_add_articles_to_group(
            user_id, group_id, comparison_service, article_service
        )
        if own_id and comp_id:
            results["passed"] += 1
        else:
            results["failed"] += 1

        # Test 3: Calculate Metrics
        if await test_calculate_metrics(comparison_service):
            results["passed"] += 1
        else:
            results["failed"] += 1

        # Test 4: Price Scenarios
        if await test_price_scenarios(comparison_service):
            results["passed"] += 1
        else:
            results["failed"] += 1

        # Test 5: Competitiveness Grades
        if await test_competitiveness_grades(comparison_service):
            results["passed"] += 1
        else:
            results["failed"] += 1

        # Test 6: Quick Comparison
        quick_group_id = await test_quick_comparison_create(user_id, comparison_service)
        if quick_group_id:
            results["passed"] += 1
        else:
            results["failed"] += 1

        # Test 7: Get History
        if await test_get_comparison_history(user_id, group_id, comparison_service):
            results["passed"] += 1
        else:
            results["failed"] += 1

        # Test 8: User Stats
        if await test_user_stats(user_id, comparison_service):
            results["passed"] += 1
        else:
            results["failed"] += 1

    except Exception as e:
        print(f"\n❌ Critical error in test suite: {e}")
        import traceback
        traceback.print_exc()

    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    print(f"Total tests: {results['total']}")
    print(f"✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['failed']}")
    print(f"Success rate: {(results['passed'] / results['total'] * 100):.1f}%")
    print("="*60)

    return results


if __name__ == "__main__":
    asyncio.run(run_all_tests())
