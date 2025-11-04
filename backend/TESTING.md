# 🧪 Руководство по тестированию

## Быстрый старт

### 1. Проверка конфигурации

Убедитесь что в `.env` файле настроен API ключ:

```bash
PARSER_MARKET_API_KEY=your-actual-api-key-here
PARSER_MARKET_REGION=Москва
PARSER_MARKET_TIMEOUT=120
```

### 2. Базовое тестирование

```bash
# Простой тест
python3 test_parser_market.py 1669668169

# Комплексное тестирование (рекомендуется)
python3 test_parser_market_comprehensive.py 1669668169
```

### 3. Тестирование API endpoints

```bash
# Терминал 1: Запуск backend
uvicorn main:app --reload

# Терминал 2: Запуск тестов API
python3 test_api_integration.py 1669668169
```

### 4. Тестирование cron jobs

```bash
python3 -m cron_jobs.price_history_collector
```

---

## Подробная документация

📄 [Полная документация по тестированию](../docs/TESTING_PARSER_MARKET.md)

---

## Доступные тесты

| Файл | Описание | Время выполнения |
|------|----------|------------------|
| `test_parser_market.py` | Базовые тесты API клиента | 2-5 минут |
| `test_parser_market_comprehensive.py` | Полное покрытие интеграции | 10-15 минут |
| `test_api_integration.py` | Тесты FastAPI endpoints | 5-10 минут |

---

## Что тестируется

✅ Базовая функциональность Parser Market API  
✅ Интеграция с OzonService  
✅ Маппинг данных в ProductInfo  
✅ Обработка ошибок  
✅ API endpoints  
✅ Cron jobs  

---

## Troubleshooting

**Ошибка: "PARSER_MARKET_API_KEY not configured"**
- Добавьте ключ в `.env` файл

**Ошибка: "Cannot connect to API"**
- Проверьте что backend запущен

**Ошибка: "Task timeout"**
- Увеличьте `PARSER_MARKET_TIMEOUT` в `.env`

Подробнее: [TESTING_PARSER_MARKET.md](../docs/TESTING_PARSER_MARKET.md)

