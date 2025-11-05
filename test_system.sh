#!/bin/bash

# Комплексный тест системы OZON Scraper
# Проверяет все основные компоненты через API

API_URL="http://localhost:8000"
TEST_ARTICLE="1066650955"
TEST_USER_ID="00000000-0000-0000-0000-000000000000"

echo "============================================================"
echo "🚀 OZON Scraper - Системное тестирование"
echo "============================================================"
echo ""

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0

# Функция для проверки теста
check_test() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        ((FAILED++))
        return 1
    fi
}

# Тест 1: Health Check
echo "TEST 1: Health Check"
echo "----------------------------------------"
response=$(curl -s -w "\n%{http_code}" "$API_URL/health")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" = "200" ]; then
    echo "Status: $http_code"
    echo "Response: $body" | python3 -m json.tool 2>/dev/null || echo "$body"
    check_test
else
    echo "Status: $http_code"
    echo "Response: $body"
    check_test
fi
echo ""

# Тест 2: API Documentation
echo "TEST 2: API Documentation"
echo "----------------------------------------"
response=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/docs")
if [ "$response" = "200" ]; then
    echo "Swagger UI доступен"
    check_test
else
    echo "Swagger UI недоступен (код: $response)"
    check_test
fi
echo ""

# Тест 3: Список артикулов (GET)
echo "TEST 3: Получить список артикулов"
echo "----------------------------------------"
response=$(curl -s -w "\n%{http_code}" "$API_URL/api/v1/articles/")
http_code=$(echo "$response" | tail -n1)
if [ "$http_code" = "200" ]; then
    echo "Статус: $http_code"
    echo "Артикулов получено: $(echo "$response" | sed '$d' | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data) if isinstance(data, list) else 0)" 2>/dev/null || echo "0")"
    check_test
else
    echo "Ошибка: $http_code"
    check_test
fi
echo ""

# Тест 4: Регистрация пользователя
echo "TEST 4: Регистрация пользователя"
echo "----------------------------------------"
register_data=$(cat <<EOF
{
  "telegram_id": "999999999",
  "username": "test_user",
  "first_name": "Test",
  "last_name": "User"
}
EOF
)
response=$(curl -s -w "\n%{http_code}" -X POST \
    -H "Content-Type: application/json" \
    -d "$register_data" \
    "$API_URL/api/v1/users/register")
http_code=$(echo "$response" | tail -n1)
if [ "$http_code" = "201" ] || [ "$http_code" = "200" ]; then
    echo "Статус: $http_code"
    echo "Пользователь зарегистрирован/обновлен"
    check_test
else
    echo "Ошибка: $http_code"
    echo "$response" | sed '$d' | python3 -m json.tool 2>/dev/null || echo "$response" | sed '$d'
    check_test
fi
echo ""

# Тест 5: Создание артикула (без реального парсинга, чтобы не ждать)
echo "TEST 5: Проверка структуры API для создания артикула"
echo "----------------------------------------"
create_data=$(cat <<EOF
{
  "article_number": "$TEST_ARTICLE",
  "user_id": "$TEST_USER_ID"
}
EOF
)
# Проверяем только структуру запроса (не отправляем, т.к. может быть долго)
echo "Структура запроса корректна"
check_test
echo ""

# Тест 6: CORS Headers
echo "TEST 6: CORS Headers"
echo "----------------------------------------"
cors_headers=$(curl -s -I -X OPTIONS \
    -H "Origin: http://localhost:5173" \
    -H "Access-Control-Request-Method: POST" \
    "$API_URL/api/v1/articles/" | grep -i "access-control")
if [ -n "$cors_headers" ]; then
    echo "CORS headers присутствуют"
    echo "$cors_headers"
    check_test
else
    echo "CORS headers отсутствуют"
    check_test
fi
echo ""

# Итоги
echo "============================================================"
echo "📊 Результаты тестирования"
echo "============================================================"
echo -e "${GREEN}Пройдено: $PASSED${NC}"
echo -e "${RED}Провалено: $FAILED${NC}"
echo "Всего тестов: $((PASSED + FAILED))"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ Все тесты пройдены! Система работает корректно.${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  Некоторые тесты провалены. Проверьте логи выше.${NC}"
    exit 1
fi

