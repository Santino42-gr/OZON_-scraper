"""
Integration Tests for Comparison API

Тестирование API endpoints для сравнения артикулов:
- POST /api/v1/comparison/groups - создание группы
- GET /api/v1/comparison/groups/{id} - получение группы
- DELETE /api/v1/comparison/groups/{id} - удаление группы
- POST /api/v1/comparison/groups/{id}/members - добавление артикула
- GET /api/v1/comparison/groups/{id}/compare - получение сравнения
- POST /api/v1/comparison/quick-compare - быстрое сравнение
- GET /api/v1/comparison/groups/{id}/history - история сравнений
- GET /api/v1/comparison/users/{id}/stats - статистика пользователя

Author: AI Agent
Created: 2025-10-31
"""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4
import httpx

# Добавляем backend в путь
sys.path.insert(0, str(Path(__file__).parent))

from services.user_service import UserService
from services.article_service import ArticleService
from models.article import ArticleCreate
from loguru import logger

# ==================== Configuration ====================

# API Base URL
API_BASE_URL = "http://localhost:8000"
COMPARISON_PREFIX = "/api/v1/comparison"

# Test Data
TEST_USER_TELEGRAM_ID = 888777666
TEST_USER_ID = None  # Will be set during setup


# ==================== Helper Functions ====================

async def setup_test_user() -> str:
    """Создать тестового пользователя"""
    user_service = UserService()

    try:
        user = await user_service.register_user(
            telegram_id=TEST_USER_TELEGRAM_ID,
            telegram_username="test_comparison_api_user"
        )
        logger.info(f"✅ Test user created: {user.id}")
        return user.id
    except Exception as e:
        user = await user_service.get_user_by_telegram_id(TEST_USER_TELEGRAM_ID)
        if user:
            logger.info(f"✅ Using existing test user: {user.id}")
            return user.id
        raise e


async def setup_test_articles(user_id: str) -> tuple:
    """Создать тестовые артикулы"""
    article_service = ArticleService()

    own_article = await article_service.create_article(
        user_id=user_id,
        article_number=f"API-OWN-{uuid4().hex[:8]}",
        fetch_data=False
    )

    competitor_article = await article_service.create_article(
        user_id=user_id,
        article_number=f"API-COMP-{uuid4().hex[:8]}",
        fetch_data=False
    )

    return own_article.id, competitor_article.id


# ==================== API Tests ====================

async def test_health_check(client: httpx.AsyncClient):
    """Test 1: Health Check"""
    print("\n" + "="*60)
    print("🧪 Test 1: Health Check")
    print("="*60)

    try:
        response = await client.get(f"{COMPARISON_PREFIX}/health")

        print(f"\n📊 Response:")
        print(f"   Status: {response.status_code}")
        print(f"   Body: {response.json()}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["module"] == "comparison"

        print(f"✅ Test passed!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


async def test_create_group(client: httpx.AsyncClient, user_id: str):
    """Test 2: Create Comparison Group"""
    print("\n" + "="*60)
    print("🧪 Test 2: Create Comparison Group")
    print("="*60)

    try:
        payload = {
            "name": "API Test Group",
            "group_type": "comparison"
        }

        response = await client.post(
            f"{COMPARISON_PREFIX}/groups?user_id={user_id}",
            json=payload
        )

        print(f"\n📊 Response:")
        print(f"   Status: {response.status_code}")
        print(f"   Body: {response.json()}")

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "API Test Group"
        assert data["group_type"] == "comparison"
        assert "id" in data

        print(f"✅ Test passed! Group ID: {data['id']}")
        return data["id"]

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_get_group(client: httpx.AsyncClient, user_id: str, group_id: str):
    """Test 3: Get Comparison Group"""
    print("\n" + "="*60)
    print("🧪 Test 3: Get Comparison Group")
    print("="*60)

    try:
        response = await client.get(
            f"{COMPARISON_PREFIX}/groups/{group_id}?user_id={user_id}"
        )

        print(f"\n📊 Response:")
        print(f"   Status: {response.status_code}")
        print(f"   Body: {response.json()}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == group_id
        assert data["user_id"] == user_id

        print(f"✅ Test passed!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


async def test_add_members(
    client: httpx.AsyncClient,
    group_id: str,
    own_article_id: str,
    competitor_article_id: str
):
    """Test 4: Add Articles to Group"""
    print("\n" + "="*60)
    print("🧪 Test 4: Add Articles to Group")
    print("="*60)

    try:
        # Add own article
        payload1 = {
            "article_id": own_article_id,
            "role": "own",
            "position": 0
        }

        response1 = await client.post(
            f"{COMPARISON_PREFIX}/groups/{group_id}/members",
            json=payload1
        )

        print(f"\n📊 Add Own Article:")
        print(f"   Status: {response1.status_code}")
        print(f"   Body: {response1.json()}")

        assert response1.status_code == 201

        # Add competitor article
        payload2 = {
            "article_id": competitor_article_id,
            "role": "competitor",
            "position": 1
        }

        response2 = await client.post(
            f"{COMPARISON_PREFIX}/groups/{group_id}/members",
            json=payload2
        )

        print(f"\n📊 Add Competitor Article:")
        print(f"   Status: {response2.status_code}")
        print(f"   Body: {response2.json()}")

        assert response2.status_code == 201

        print(f"✅ Test passed!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_get_comparison(client: httpx.AsyncClient, user_id: str, group_id: str):
    """Test 5: Get Comparison"""
    print("\n" + "="*60)
    print("🧪 Test 5: Get Comparison")
    print("="*60)

    try:
        response = await client.get(
            f"{COMPARISON_PREFIX}/groups/{group_id}/compare?user_id={user_id}&refresh=false"
        )

        print(f"\n📊 Response:")
        print(f"   Status: {response.status_code}")

        assert response.status_code == 200
        data = response.json()

        print(f"   Group ID: {data['group_id']}")
        print(f"   Group Name: {data['group_name']}")
        print(f"   Own Product: {data['own_product']['article_number'] if data['own_product'] else 'None'}")
        print(f"   Competitors: {len(data['competitors'])}")

        if data.get('metrics'):
            metrics = data['metrics']
            print(f"\n   📈 Metrics:")
            print(f"      Competitiveness Index: {metrics['competitiveness_index']}")
            print(f"      Grade: {metrics['grade']}")
            print(f"      Recommendation: {metrics['overall_recommendation']}")

        assert data["group_id"] == group_id

        print(f"✅ Test passed!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_quick_comparison(client: httpx.AsyncClient, user_id: str):
    """Test 6: Quick Comparison Create"""
    print("\n" + "="*60)
    print("🧪 Test 6: Quick Comparison Create")
    print("="*60)

    try:
        payload = {
            "own_article_number": f"QUICK-OWN-{uuid4().hex[:6]}",
            "competitor_article_number": f"QUICK-COMP-{uuid4().hex[:6]}",
            "group_name": "Quick API Test",
            "scrape_now": False
        }

        print(f"\n📝 Creating quick comparison:")
        print(f"   Own: {payload['own_article_number']}")
        print(f"   Competitor: {payload['competitor_article_number']}")

        response = await client.post(
            f"{COMPARISON_PREFIX}/quick-compare?user_id={user_id}",
            json=payload
        )

        print(f"\n📊 Response:")
        print(f"   Status: {response.status_code}")

        assert response.status_code == 201
        data = response.json()

        print(f"   Group ID: {data['group_id']}")
        print(f"   Group Name: {data['group_name']}")
        print(f"   Own Product: {data['own_product']['article_number'] if data['own_product'] else 'None'}")
        print(f"   Competitors: {len(data['competitors'])}")

        assert data["group_id"] is not None
        assert data["own_product"] is not None

        print(f"✅ Test passed!")
        return data["group_id"]

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_get_history(client: httpx.AsyncClient, user_id: str, group_id: str):
    """Test 7: Get Comparison History"""
    print("\n" + "="*60)
    print("🧪 Test 7: Get Comparison History")
    print("="*60)

    try:
        response = await client.get(
            f"{COMPARISON_PREFIX}/groups/{group_id}/history?user_id={user_id}&days=30"
        )

        print(f"\n📊 Response:")
        print(f"   Status: {response.status_code}")

        assert response.status_code == 200
        data = response.json()

        print(f"   Group ID: {data['group_id']}")
        print(f"   Snapshots: {data['total_count']}")
        print(f"   Date From: {data['date_from']}")
        print(f"   Date To: {data['date_to']}")

        if data['snapshots']:
            print(f"\n   Latest Snapshot:")
            latest = data['snapshots'][0]
            print(f"      ID: {latest['id']}")
            print(f"      Date: {latest['snapshot_date']}")
            print(f"      Index: {latest['competitiveness_index']}")

        print(f"✅ Test passed!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_get_user_stats(client: httpx.AsyncClient, user_id: str):
    """Test 8: Get User Stats"""
    print("\n" + "="*60)
    print("🧪 Test 8: Get User Comparison Stats")
    print("="*60)

    try:
        response = await client.get(
            f"{COMPARISON_PREFIX}/users/{user_id}/stats"
        )

        print(f"\n📊 Response:")
        print(f"   Status: {response.status_code}")

        assert response.status_code == 200
        data = response.json()

        print(f"   Total Groups: {data['total_groups']}")
        print(f"   Comparison Groups: {data['comparison_groups']}")
        print(f"   Total Articles: {data['total_articles']}")
        print(f"   Avg Competitiveness: {data['avg_competitiveness_index']}")
        print(f"   Last Comparison: {data['last_comparison_date']}")

        print(f"✅ Test passed!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_delete_group(client: httpx.AsyncClient, user_id: str, group_id: str):
    """Test 9: Delete Comparison Group"""
    print("\n" + "="*60)
    print("🧪 Test 9: Delete Comparison Group")
    print("="*60)

    try:
        response = await client.delete(
            f"{COMPARISON_PREFIX}/groups/{group_id}?user_id={user_id}"
        )

        print(f"\n📊 Response:")
        print(f"   Status: {response.status_code}")

        assert response.status_code == 204

        print(f"✅ Test passed!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


async def test_error_cases(client: httpx.AsyncClient, user_id: str):
    """Test 10: Error Handling"""
    print("\n" + "="*60)
    print("🧪 Test 10: Error Handling")
    print("="*60)

    try:
        # Test 1: Get non-existent group
        print("\n  📌 Test: Get non-existent group (should return 404)")
        fake_id = str(uuid4())
        response = await client.get(
            f"{COMPARISON_PREFIX}/groups/{fake_id}?user_id={user_id}"
        )
        print(f"     Status: {response.status_code} (expected 404)")
        assert response.status_code == 404

        # Test 2: Create group without user_id
        print("\n  📌 Test: Create group without user_id (should return 422)")
        response = await client.post(
            f"{COMPARISON_PREFIX}/groups",
            json={"name": "Test", "group_type": "comparison"}
        )
        print(f"     Status: {response.status_code} (expected 422)")
        assert response.status_code == 422

        # Test 3: Get history with invalid days parameter
        print("\n  📌 Test: Get history with invalid days (should return 422)")
        response = await client.get(
            f"{COMPARISON_PREFIX}/groups/{fake_id}/history?user_id={user_id}&days=999"
        )
        print(f"     Status: {response.status_code} (expected 422)")
        assert response.status_code == 422

        print(f"\n✅ All error cases handled correctly!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# ==================== Main Test Runner ====================

async def run_all_tests():
    """Запустить все integration тесты"""
    print("\n" + "="*60)
    print("🚀 COMPARISON API - INTEGRATION TESTS")
    print("="*60)
    print(f"\n🌐 Testing API at: {API_BASE_URL}")
    print(f"⚠️  Make sure the backend server is running!")
    print("="*60)

    results = {
        "passed": 0,
        "failed": 0,
        "total": 10
    }

    # Setup
    try:
        user_id = await setup_test_user()
        own_article_id, competitor_article_id = await setup_test_articles(user_id)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        return results

    # HTTP Client
    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=30.0) as client:
        try:
            # Test 1: Health Check
            if await test_health_check(client):
                results["passed"] += 1
            else:
                results["failed"] += 1

            # Test 2: Create Group
            group_id = await test_create_group(client, user_id)
            if group_id:
                results["passed"] += 1
            else:
                results["failed"] += 1
                print("\n⚠️ Skipping remaining tests due to group creation failure")
                return results

            # Test 3: Get Group
            if await test_get_group(client, user_id, group_id):
                results["passed"] += 1
            else:
                results["failed"] += 1

            # Test 4: Add Members
            if await test_add_members(client, group_id, own_article_id, competitor_article_id):
                results["passed"] += 1
            else:
                results["failed"] += 1

            # Test 5: Get Comparison
            if await test_get_comparison(client, user_id, group_id):
                results["passed"] += 1
            else:
                results["failed"] += 1

            # Test 6: Quick Comparison
            quick_group_id = await test_quick_comparison(client, user_id)
            if quick_group_id:
                results["passed"] += 1
            else:
                results["failed"] += 1

            # Test 7: Get History
            if await test_get_history(client, user_id, group_id):
                results["passed"] += 1
            else:
                results["failed"] += 1

            # Test 8: Get User Stats
            if await test_get_user_stats(client, user_id):
                results["passed"] += 1
            else:
                results["failed"] += 1

            # Test 9: Delete Group
            if await test_delete_group(client, user_id, group_id):
                results["passed"] += 1
            else:
                results["failed"] += 1

            # Test 10: Error Cases
            if await test_error_cases(client, user_id):
                results["passed"] += 1
            else:
                results["failed"] += 1

        except httpx.ConnectError:
            print(f"\n❌ Connection Error: Could not connect to {API_BASE_URL}")
            print("   Make sure the backend server is running!")
            print("   Run: python backend/main.py")
            results["failed"] = results["total"]

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
    print("\n⚠️  IMPORTANT: Make sure the backend server is running before running tests!")
    print("   Start server: python backend/main.py")
    print("   Or: uvicorn main:app --reload")
    print("\n   Press Ctrl+C to cancel, or Enter to continue...")

    try:
        input()
    except KeyboardInterrupt:
        print("\n\nTests cancelled.")
        sys.exit(0)

    asyncio.run(run_all_tests())
