#!/usr/bin/env python3
"""
Comprehensive Testing Script for OZON Scraper System
Тестирует все компоненты системы: Backend API, Bot, Data Fetching, Admin Panel
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from typing import Dict, List, Any
import sys

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER_ID = "test-qa-user-" + datetime.now().strftime("%Y%m%d%H%M%S")
TEST_TELEGRAM_ID = 999888777
TEST_ARTICLE = "1066650955"  # Real OZON article for testing

# Test results storage
test_results = {
    "passed": 0,
    "failed": 0,
    "errors": [],
    "details": []
}


def log_test(test_name: str, status: str, details: str = ""):
    """Log test result"""
    symbol = "✅" if status == "PASS" else "❌"
    print(f"{symbol} {test_name}: {status}")
    if details:
        print(f"   {details}")

    if status == "PASS":
        test_results["passed"] += 1
    else:
        test_results["failed"] += 1
        test_results["errors"].append({"test": test_name, "details": details})

    test_results["details"].append({
        "test": test_name,
        "status": status,
        "details": details,
        "timestamp": datetime.now().isoformat()
    })


async def test_backend_health(session: aiohttp.ClientSession):
    """Test 1: Backend Health Check"""
    test_name = "Backend API Health Check"
    try:
        async with session.get(f"{BASE_URL}/health") as response:
            if response.status == 200:
                data = await response.json()
                if data.get("status") == "healthy" and data.get("database") == "connected":
                    log_test(test_name, "PASS", f"Service: {data.get('service')}, Version: {data.get('version')}")
                else:
                    log_test(test_name, "FAIL", f"Unexpected health status: {data}")
            else:
                log_test(test_name, "FAIL", f"HTTP {response.status}")
    except Exception as e:
        log_test(test_name, "FAIL", f"Exception: {str(e)}")


async def test_api_documentation(session: aiohttp.ClientSession):
    """Test 2: API Documentation Availability"""
    test_name = "API Documentation (Swagger)"
    try:
        async with session.get(f"{BASE_URL}/docs") as response:
            if response.status == 200:
                log_test(test_name, "PASS", "Swagger UI accessible")
            else:
                log_test(test_name, "FAIL", f"HTTP {response.status}")
    except Exception as e:
        log_test(test_name, "FAIL", f"Exception: {str(e)}")


async def test_user_registration(session: aiohttp.ClientSession) -> str:
    """Test 3: User Registration"""
    test_name = "User Registration Endpoint"
    try:
        payload = {
            "telegram_id": TEST_TELEGRAM_ID,
            "username": "qa_test_user",
            "first_name": "QA",
            "last_name": "Test"
        }
        async with session.post(
            f"{BASE_URL}/api/v1/users/register",
            json=payload
        ) as response:
            if response.status in [200, 201]:
                data = await response.json()
                user_id = data.get("id")
                log_test(test_name, "PASS", f"User ID: {user_id}")
                return user_id
            else:
                log_test(test_name, "FAIL", f"HTTP {response.status}")
                return None
    except Exception as e:
        log_test(test_name, "FAIL", f"Exception: {str(e)}")
        return None


async def test_get_articles(session: aiohttp.ClientSession):
    """Test 4: Get Articles List"""
    test_name = "Get Articles Endpoint"
    try:
        async with session.get(f"{BASE_URL}/api/v1/articles/") as response:
            if response.status == 200:
                data = await response.json()
                log_test(test_name, "PASS", f"Retrieved {len(data)} articles")
            else:
                log_test(test_name, "FAIL", f"HTTP {response.status}")
    except Exception as e:
        log_test(test_name, "FAIL", f"Exception: {str(e)}")


async def test_create_article(session: aiohttp.ClientSession, user_id: str) -> str:
    """Test 5: Create Article"""
    test_name = "Create Article Endpoint"
    try:
        payload = {
            "article_number": TEST_ARTICLE,
            "user_id": user_id
        }
        async with session.post(
            f"{BASE_URL}/api/v1/articles/",
            json=payload
        ) as response:
            if response.status in [200, 201]:
                data = await response.json()
                article_id = data.get("id")
                log_test(test_name, "PASS", f"Article ID: {article_id}, Article: {TEST_ARTICLE}")
                return article_id
            else:
                text = await response.text()
                log_test(test_name, "FAIL", f"HTTP {response.status}: {text}")
                return None
    except Exception as e:
        log_test(test_name, "FAIL", f"Exception: {str(e)}")
        return None


async def test_get_article_details(session: aiohttp.ClientSession, article_id: str):
    """Test 6: Get Article Details"""
    test_name = "Get Article Details"
    try:
        async with session.get(f"{BASE_URL}/api/v1/articles/{article_id}") as response:
            if response.status == 200:
                data = await response.json()
                log_test(test_name, "PASS", f"Article: {data.get('article_number')}")
            else:
                log_test(test_name, "FAIL", f"HTTP {response.status}")
    except Exception as e:
        log_test(test_name, "FAIL", f"Exception: {str(e)}")


async def test_fetch_article_data(session: aiohttp.ClientSession, article_number: str):
    """Test 7: Fetch Article Data from OZON"""
    test_name = "Fetch Article Data (OZON API)"
    try:
        async with session.post(
            f"{BASE_URL}/api/v1/articles/fetch",
            json={"article_number": article_number}
        ) as response:
            if response.status == 200:
                data = await response.json()
                # Check if we got data
                if data.get("name") or data.get("price"):
                    log_test(test_name, "PASS",
                             f"Name: {data.get('name', 'N/A')}, "
                             f"Price: {data.get('price', 'N/A')}, "
                             f"Rating: {data.get('rating', 'N/A')}")
                else:
                    log_test(test_name, "PARTIAL", "Data fetched but some fields missing")
            else:
                text = await response.text()
                log_test(test_name, "FAIL", f"HTTP {response.status}: {text}")
    except Exception as e:
        log_test(test_name, "FAIL", f"Exception: {str(e)}")


async def test_price_calculation(session: aiohttp.ClientSession, article_number: str):
    """Test 8: Price Calculation (with/without Ozon Card)"""
    test_name = "Price Calculation Logic"
    try:
        async with session.post(
            f"{BASE_URL}/api/v1/articles/fetch",
            json={"article_number": article_number}
        ) as response:
            if response.status == 200:
                data = await response.json()
                price = data.get("price")
                ozon_card_price = data.get("ozon_card_price")
                normal_price = data.get("normal_price")

                if price is not None:
                    details = f"Price: {price}"
                    if ozon_card_price:
                        details += f", Ozon Card: {ozon_card_price}"
                    if normal_price:
                        details += f", Normal: {normal_price}"
                    log_test(test_name, "PASS", details)
                else:
                    log_test(test_name, "FAIL", "Price data not available")
            else:
                log_test(test_name, "FAIL", f"HTTP {response.status}")
    except Exception as e:
        log_test(test_name, "FAIL", f"Exception: {str(e)}")


async def test_spp_calculation(session: aiohttp.ClientSession, article_number: str):
    """Test 9: SPP (Discount) Calculation"""
    test_name = "SPP Calculation"
    try:
        async with session.post(
            f"{BASE_URL}/api/v1/articles/fetch",
            json={"article_number": article_number}
        ) as response:
            if response.status == 200:
                data = await response.json()
                spp1 = data.get("spp1")
                spp2 = data.get("spp2")
                spp_total = data.get("spp_total")

                if spp_total is not None or spp1 is not None:
                    details = []
                    if spp1: details.append(f"SPP1: {spp1}%")
                    if spp2: details.append(f"SPP2: {spp2}%")
                    if spp_total: details.append(f"Total: {spp_total}%")
                    log_test(test_name, "PASS", ", ".join(details))
                else:
                    log_test(test_name, "PARTIAL", "SPP data not available for this article")
            else:
                log_test(test_name, "FAIL", f"HTTP {response.status}")
    except Exception as e:
        log_test(test_name, "FAIL", f"Exception: {str(e)}")


async def test_average_price_7days(session: aiohttp.ClientSession, article_id: str):
    """Test 10: Average Price 7 Days Calculation"""
    test_name = "Average Price (7 days)"
    try:
        async with session.get(f"{BASE_URL}/api/v1/articles/{article_id}") as response:
            if response.status == 200:
                data = await response.json()
                avg_price = data.get("average_price_7days")

                if avg_price is not None:
                    log_test(test_name, "PASS", f"Avg Price: {avg_price}")
                else:
                    log_test(test_name, "PARTIAL", "Not enough historical data for 7-day average")
            else:
                log_test(test_name, "FAIL", f"HTTP {response.status}")
    except Exception as e:
        log_test(test_name, "FAIL", f"Exception: {str(e)}")


async def test_cors_headers(session: aiohttp.ClientSession):
    """Test 11: CORS Headers"""
    test_name = "CORS Headers Configuration"
    try:
        async with session.options(f"{BASE_URL}/api/v1/articles/") as response:
            headers = response.headers
            allow_origin = headers.get("Access-Control-Allow-Origin")
            allow_methods = headers.get("Access-Control-Allow-Methods")

            if allow_origin and allow_methods:
                log_test(test_name, "PASS",
                         f"Origin: {allow_origin}, Methods: {allow_methods}")
            else:
                log_test(test_name, "FAIL", "CORS headers not properly configured")
    except Exception as e:
        log_test(test_name, "FAIL", f"Exception: {str(e)}")


async def test_error_handling(session: aiohttp.ClientSession):
    """Test 12: Error Handling for Invalid Article"""
    test_name = "Error Handling (Invalid Article)"
    try:
        async with session.post(
            f"{BASE_URL}/api/v1/articles/fetch",
            json={"article_number": "99999999999"}
        ) as response:
            # We expect this to fail gracefully
            if response.status >= 400:
                data = await response.json()
                if "detail" in data or "error" in data:
                    log_test(test_name, "PASS", "Error handled gracefully")
                else:
                    log_test(test_name, "PARTIAL", "Error returned but message unclear")
            else:
                log_test(test_name, "FAIL", "Invalid article should return error")
    except Exception as e:
        log_test(test_name, "FAIL", f"Exception: {str(e)}")


async def test_database_connection(session: aiohttp.ClientSession):
    """Test 13: Database Connection"""
    test_name = "Database Connection (via Health)"
    try:
        async with session.get(f"{BASE_URL}/health") as response:
            if response.status == 200:
                data = await response.json()
                if data.get("database") == "connected":
                    log_test(test_name, "PASS", "Database connected")
                else:
                    log_test(test_name, "FAIL", "Database not connected")
            else:
                log_test(test_name, "FAIL", f"HTTP {response.status}")
    except Exception as e:
        log_test(test_name, "FAIL", f"Exception: {str(e)}")


async def run_all_tests():
    """Run all tests sequentially"""
    print("\n" + "="*80)
    print("🧪 COMPREHENSIVE TESTING - OZON SCRAPER SYSTEM")
    print("="*80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")

    async with aiohttp.ClientSession() as session:
        # Phase 1: Backend API Tests
        print("📋 PHASE 1: BACKEND API TESTS")
        print("-" * 80)
        await test_backend_health(session)
        await test_api_documentation(session)
        await test_database_connection(session)
        await test_cors_headers(session)

        # Phase 2: User Management Tests
        print("\n📋 PHASE 2: USER MANAGEMENT TESTS")
        print("-" * 80)
        user_id = await test_user_registration(session)

        # Phase 3: Article Management Tests
        print("\n📋 PHASE 3: ARTICLE MANAGEMENT TESTS")
        print("-" * 80)
        await test_get_articles(session)

        if user_id:
            article_id = await test_create_article(session, user_id)
            if article_id:
                await test_get_article_details(session, article_id)
                await test_average_price_7days(session, article_id)

        # Phase 4: Data Fetching & Calculation Tests
        print("\n📋 PHASE 4: DATA FETCHING & CALCULATIONS")
        print("-" * 80)
        await test_fetch_article_data(session, TEST_ARTICLE)
        await test_price_calculation(session, TEST_ARTICLE)
        await test_spp_calculation(session, TEST_ARTICLE)

        # Phase 5: Error Handling Tests
        print("\n📋 PHASE 5: ERROR HANDLING TESTS")
        print("-" * 80)
        await test_error_handling(session)

    # Print summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    print(f"✅ Passed: {test_results['passed']}")
    print(f"❌ Failed: {test_results['failed']}")
    print(f"📈 Success Rate: {(test_results['passed']/(test_results['passed']+test_results['failed'])*100):.1f}%")

    if test_results['errors']:
        print("\n❌ FAILED TESTS:")
        for error in test_results['errors']:
            print(f"  - {error['test']}: {error['details']}")

    print("\n" + "="*80)
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")

    # Save results to file
    report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(test_results, f, indent=2, ensure_ascii=False)
    print(f"📄 Detailed report saved to: {report_file}\n")

    return test_results['failed'] == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
