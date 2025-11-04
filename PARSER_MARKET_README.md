# Parser Market API - Краткая документация

## 🌐 Обзор

Parser Market - облачный сервис для парсинга российских маркетплейсов (Ozon, Wildberries, Yandex.Market).

**Официальная документация:** https://parser.market/parser-cen-json-api/

---

## 🔑 Аутентификация

Все запросы требуют API ключ в теле запроса:

```json
{
  "apikey": "YOUR-API-KEY"
}
```

---

## 📡 API Endpoints

### Base URL
```
https://parser.market/wp-json/client-api/v1/
```

### 1. Проверка баланса

**Endpoint:** `POST /get-balanse`

**Request:**
```json
{
  "apikey": "YOUR-API-KEY"
}
```

**Response:**
```json
[
  {"result": "success"},
  {"your_login": "username"},
  {"your_email": "email@example.com"},
  {"checks_free": 800},
  {"checks_paid": 5000},
  {"checks_pending": 200},
  {"checks_total": 5600}
]
```

---

### 2. Отправка задачи на парсинг

**Endpoint:** `POST /send-order`

**Request:**
```json
{
  "apikey": "YOUR-API-KEY",
  "regionid": "Москва",
  "market": "ozon",
  "userlabel": "MY_TASK_001",
  "products": [
    {
      "category": "",
      "code": 0.0,
      "productid": "123456789",
      "brand": "",
      "name": "Product Name",
      "linkset": ["https://www.ozon.ru/product/123456789/"],
      "marketid": "",
      "price": 0.0,
      "donotsearch": "",
      "textsearch": ""
    }
  ]
}
```

**Response:**
```json
[
  {"result": "success"},
  {"user_id": "3"},
  {"user_login": "username"},
  {"userlabel": "MY_TASK_001"},
  {"market": "ozon"},
  {"region_code": "Москва"}
]
```

**Важно:**
- `"result": "success"` означает что задача принята, НЕ завершена
- Поле `name` обязательно даже если есть URL
- Используйте `userlabel` для отслеживания задачи

---

### 3. Получение статуса и результатов

**Endpoint:** `POST /get-last50`

**Request (по userlabel):**
```json
{
  "apikey": "YOUR-API-KEY",
  "userlabels": ["MY_TASK_001"],
  "limit": 5
}
```

**Request (последние N задач):**
```json
{
  "apikey": "YOUR-API-KEY",
  "limit": 10
}
```

**Response:**
```json
[
  {"result": "success"},
  {"userid": "3"},
  {"userlogin": "username"},
  {"data": [
    [
      {"order-id": 122797},
      {"received": "2024-04-13 12:57:16"},
      {"market": "ozon"},
      {"region-code": "Санкт-Петербург"},
      {"userlabel": "MY_TASK_001"},
      {"items-in-price": 1},
      {"items-loaded": 1},
      {"status": "completed"},
      {"report_csv": "https://files.parser.market/.../report.csv"},
      {"report_xlsx": "https://files.parser.market/.../report.xlsx"},
      {"report_xml": "https://files.parser.market/.../report.xlsm"},
      {"report_json": "https://files.parser.market/.../report.json"}
    ]
  ]}
]
```

**Статусы задачи:**
- `waiting` - в очереди
- `processing` - выполняется
- `completed` - завершена (отчёты доступны)
- `error` - ошибка

---

## 🎯 Типичный workflow

### 1. Отправить задачу
```python
result = await client.submit_task(article="123456789")
userlabel = result.get("userlabel")
```

### 2. Опрашивать статус каждые 10 секунд
```python
while True:
    tasks = await client.get_task_status(userlabel=userlabel)
    status = tasks[0]["status"]

    if status == "completed":
        break

    await asyncio.sleep(10)
```

### 3. Скачать JSON отчёт
```python
report_url = tasks[0]["report_json"]
data = await client.download_json_report(report_url)
```

---

## 🛠️ Поддерживаемые маркетплейсы

| Код | Маркетплейс |
|-----|-------------|
| `ozon` | Ozon (полные страницы товаров) |
| `ozons` | Ozon (результаты поиска) |
| `wbs` | Wildberries |
| `yam` | Yandex.Market |

---

## 🌍 Поддерживаемые регионы

- Москва
- Санкт-Петербург
- Другие города России (см. документацию)

**Важно:** Регион влияет на цены и наличие товаров!

---

## 💰 Тарификация

- **Бесплатные checks:** Бонусные проверки (обычно 800)
- **Оплаченные checks:** Купленные проверки
- **Pending checks:** Проверки в процессе

**Стоимость:** Уточняйте у Parser Market:
- 📞 +7-915-128-98-08
- 📧 Email (см. на сайте)

---

## ⚠️ Ограничения и особенности

### Rate Limits
Не указаны в документации. Рекомендуется:
- Задержка между запросами: 2-5 секунд
- Batch size: 10-50 товаров

### Таймауты
- Среднее время обработки: 30-120 секунд
- Рекомендуемый timeout: 120 секунд
- Интервал polling: 10 секунд

### Данные
- Все поля должны присутствовать в JSON (используйте `""` для пустых)
- Числа должны быть float (например, `0.0`)
- Массивы должны быть пустыми `[]` если нет данных

---

## 🔗 Полезные ссылки

- 🌐 Официальный сайт: https://parser.market/
- 📄 API документация: https://parser.market/parser-cen-json-api/
- 📞 Поддержка: +7-915-128-98-08

---

## 💡 Примеры использования

### Пример 1: Простой парсинг

```python
from services.parser_market_client import ParserMarketClient

async def parse_product(article: str):
    async with ParserMarketClient(api_key="YOUR_KEY") as client:
        product = await client.parse_sync(article)
        print(f"{product.name}: {product.price} руб")
```

### Пример 2: Batch парсинг

```python
async def parse_multiple(articles: list):
    async with ParserMarketClient(api_key="YOUR_KEY") as client:
        results = await client.parse_batch(articles)

        for article, product in zip(articles, results):
            if product:
                print(f"{article}: {product.price} руб")
            else:
                print(f"{article}: FAILED")
```

### Пример 3: Проверка баланса

```python
async def check_balance():
    async with ParserMarketClient(api_key="YOUR_KEY") as client:
        balance = await client.get_balance()
        print(f"Total checks: {balance['checks_total']}")
```

---

## 🐛 Troubleshooting

### Ошибка: "result": "error"
**Причина:** Неверный API ключ или проблема с запросом
**Решение:** Проверьте API ключ и формат запроса

### Задача зависла в статусе "processing"
**Причина:** Задача может занять до 5 минут
**Решение:** Увеличьте timeout или подождите

### Пустой отчёт
**Причина:** Товар не найден на маркетплейсе
**Решение:** Проверьте артикул и регион

### Быстро закончились checks
**Причина:** Каждый товар = 1 check
**Решение:** Пополните баланс или оптимизируйте запросы

---

**Последнее обновление:** 2025-11-04
