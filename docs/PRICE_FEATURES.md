# 💰 Детальные функции работы с ценами OZON

## 📋 Обзор

Реализация получения детальной информации о ценах товаров OZON, включая:
- 💳 Цены с/без Ozon Card
- 📊 Историю изменения цен
- 📈 Среднюю цену за 7 дней

**Task:** AIL-305  
**Created:** 2025-10-21  
**Status:** ✅ Completed

---

## 🎯 Основные функции

### 1. Типы цен

| Тип цены | Описание | Поле в БД |
|----------|----------|-----------|
| **Normal Price** | Обычная цена без Ozon Card (черный текст) | `normal_price` |
| **Ozon Card Price** | Специальная цена для держателей карты (фиолетовый текст) | `ozon_card_price` |
| **Old Price** | Перечеркнутая цена (старая цена) | `old_price` |
| **Current Price** | Текущая основная цена (обычно = ozon_card_price) | `price` |
| **Average 7 Days** | Средняя цена за последние 7 дней | `average_price_7days` |

---

## 🛠️ Архитектура решения

### Компоненты

```
┌─────────────────────────────────────────────────────────────┐
│                    OZON Web Scraping                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. OzonScraper (Playwright/httpx)                         │
│     ↓                                                       │
│  2. Parse HTML (BeautifulSoup)                             │
│     → Extract: normal_price, ozon_card_price, old_price    │
│     ↓                                                       │
│  3. Save to DB (ozon_scraper_articles)                     │
│     ↓                                                       │
│  4. Cron Job (каждые 24ч)                                  │
│     → Save to price_history table                          │
│     ↓                                                       │
│  5. Calculate Average (SQL function)                       │
│     → AVG(price) for last 7 days                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 База данных

### Таблица: `ozon_scraper_price_history`

История цен для расчета средней за 7 дней.

```sql
CREATE TABLE ozon_scraper_price_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_number VARCHAR(255) NOT NULL,
    price DECIMAL(10,2),
    normal_price DECIMAL(10,2),
    ozon_card_price DECIMAL(10,2),
    old_price DECIMAL(10,2),
    price_date TIMESTAMP NOT NULL DEFAULT NOW(),
    source VARCHAR(50) DEFAULT 'scraping',
    scraping_success BOOLEAN DEFAULT TRUE,
    product_available BOOLEAN DEFAULT TRUE,
    rating DECIMAL(3,2),
    reviews_count INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Индексы:**
- `idx_ozon_scraper_price_history_article_date` - быстрый поиск по артикулу и дате
- `idx_ozon_scraper_price_history_date` - сортировка по дате
- `idx_ozon_scraper_price_history_article` - поиск по артикулу

### Таблица: `ozon_scraper_articles` (обновлена)

Добавлены новые поля:

```sql
ALTER TABLE ozon_scraper_articles
ADD COLUMN normal_price DECIMAL(10,2),
ADD COLUMN ozon_card_price DECIMAL(10,2),
ADD COLUMN average_price_7days DECIMAL(10,2),
ADD COLUMN price_updated_at TIMESTAMP;
```

---

## 🔧 SQL Функции

### 1. `get_average_price_7days(article_number, days)`

Получить среднюю, минимальную и максимальную цену за период.

**Параметры:**
- `p_article_number` (VARCHAR) - артикул товара
- `p_days` (INTEGER) - количество дней (по умолчанию 7)

**Возвращает:**

| Поле | Тип | Описание |
|------|-----|----------|
| `article_number` | VARCHAR | Артикул |
| `avg_price` | DECIMAL | Средняя цена |
| `avg_normal_price` | DECIMAL | Средняя цена без карты |
| `avg_ozon_card_price` | DECIMAL | Средняя цена с картой |
| `min_price` | DECIMAL | Минимальная цена |
| `max_price` | DECIMAL | Максимальная цена |
| `data_points` | INTEGER | Количество точек данных |
| `first_date` | TIMESTAMP | Первая дата |
| `last_date` | TIMESTAMP | Последняя дата |

**Пример:**

```sql
SELECT * FROM get_average_price_7days('123456789', 7);
```

### 2. `get_price_history(article_number, days, limit)`

Получить историю изменения цен.

**Параметры:**
- `p_article_number` (VARCHAR) - артикул товара
- `p_days` (INTEGER) - количество дней (по умолчанию 30)
- `p_limit` (INTEGER) - максимум записей (по умолчанию 100)

**Пример:**

```sql
SELECT * FROM get_price_history('123456789', 30, 50);
```

### 3. `update_all_average_prices()`

Обновить средние цены для всех активных артикулов.

**Возвращает:** количество обновленных записей (INTEGER)

**Пример:**

```sql
SELECT update_all_average_prices();
```

### 4. `update_article_average_price(article_number)`

Обновить среднюю цену для конкретного артикула.

**Возвращает:** TRUE если обновлено, FALSE если нет данных

**Пример:**

```sql
SELECT update_article_average_price('123456789');
```

---

## 🌐 API Endpoints

### 1. `GET /api/v1/articles/{article_id}/prices`

Получить все цены товара.

**Response:**

```json
{
  "article_id": "550e8400-e29b-41d4-a716-446655440000",
  "article_number": "123456789",
  "price": 1799.00,
  "normal_price": 1999.00,
  "ozon_card_price": 1799.00,
  "old_price": 2499.00,
  "average_price_7days": 1950.00,
  "price_updated_at": "2025-10-21T12:00:00",
  "currency": "RUB"
}
```

### 2. `GET /api/v1/articles/{article_id}/price-history?days=7`

Получить историю изменения цен.

**Query Parameters:**
- `days` (integer, optional) - количество дней (1-30, default: 7)

**Response:**

```json
{
  "article_number": "123456789",
  "days": 7,
  "total_records": 7,
  "history": [
    {
      "price_date": "2025-10-21T00:00:00",
      "price": 1799.00,
      "normal_price": 1999.00,
      "ozon_card_price": 1799.00,
      "old_price": 2499.00,
      "product_available": true
    }
  ]
}
```

### 3. `GET /api/v1/articles/{article_id}/price-average?days=7`

Получить статистику цен за период.

**Query Parameters:**
- `days` (integer, optional) - количество дней (1-30, default: 7)

**Response:**

```json
{
  "article_number": "123456789",
  "days": 7,
  "avg_price": 1950.00,
  "avg_normal_price": 1950.00,
  "avg_ozon_card_price": 1750.00,
  "min_price": 1899.00,
  "max_price": 1999.00,
  "data_points": 7,
  "first_date": "2025-10-14T00:00:00",
  "last_date": "2025-10-21T00:00:00"
}
```

### 4. `POST /api/v1/articles/{article_id}/refresh-prices`

Обновить информацию о ценах товара (выполняет web scraping).

**Response:** обновленные цены (как в endpoint #1)

### 5. `POST /api/v1/articles/update-all-averages`

Обновить средние цены для всех активных артикулов.

**Response:**

```json
{
  "success": true,
  "updated_count": 42,
  "message": "Средние цены обновлены для 42 артикулов"
}
```

---

## 🔄 Cron Job для сбора истории

### Price History Collector

**Файл:** `backend/cron_jobs/price_history_collector.py`

**Расписание:** Каждые 24 часа (рекомендуется 03:00)

**Что делает:**
1. Получает все активные артикулы из БД
2. Для каждого артикула выполняет web scraping
3. Извлекает: `price`, `normal_price`, `ozon_card_price`, `old_price`
4. Сохраняет в таблицу `ozon_scraper_price_history`
5. Логирует результаты

**Запуск вручную:**

```bash
cd backend
python -m cron_jobs.price_history_collector
```

**Через Docker:**

```bash
docker-compose up cron-worker
```

**Конфигурация (ENV):**

```bash
OZON_SCRAPER_BATCH_SIZE=10    # Артикулов в batch
OZON_SCRAPER_DELAY=5          # Задержка между запросами (сек)
```

---

## 🧪 Тестирование

### Тестовый скрипт

```bash
cd backend
python test_price_features.py
```

**Что тестируется:**
1. ✅ Парсинг детальных цен (OzonScraper)
2. ✅ SQL функции (get_average_price_7days, get_price_history)
3. ✅ Обновление средних цен (update_all_average_prices)
4. ✅ Работа API endpoints

---

## 🎨 Селекторы HTML для парсинга

### Цена без Ozon Card

```python
# Основной селектор
soup.find('span', {'data-widget': 'webPrice'})

# Альтернативный
soup.find('span', class_=lambda x: x and 'tsHeadline500Medium' in x)
```

### Цена с Ozon Card

```python
# Основной селектор
soup.find('span', {'data-widget': 'webOzonCardPrice'})

# Альтернативный
soup.find('span', class_=lambda x: x and 'ozonCard' in str(x).lower())
```

### Старая цена (перечеркнутая)

```python
# Основной селектор
soup.find('span', class_=lambda x: x and 'line-through' in str(x))

# Альтернативный
soup.find('s')
```

---

## 📈 Workflow: Как это работает

### 1. Добавление нового артикула

```
User добавляет артикул
   ↓
API: POST /api/v1/articles
   ↓
OzonScraper.get_product_info()
   ↓
Parse HTML → extract prices
   ↓
Save to ozon_scraper_articles
   (price, normal_price, ozon_card_price, old_price)
```

### 2. Сбор истории (Cron Job)

```
Cron Job запускается (каждые 24ч)
   ↓
Получить все активные артикулы
   ↓
For each article:
   ↓
   Scrape current prices
   ↓
   Save to ozon_scraper_price_history
   (article, price, normal_price, ozon_card_price, date)
```

### 3. Расчет средней цены

```
API: GET /articles/{id}/price-average?days=7
   ↓
SQL: get_average_price_7days()
   ↓
SELECT AVG(price), MIN(price), MAX(price)
FROM ozon_scraper_price_history
WHERE article_number = ? AND date >= NOW() - 7 days
   ↓
Return statistics
```

---

## ⚠️ Важные замечания

### Требования к данным

1. **Минимум 7 записей** в `price_history` для корректной средней цены
2. **Cron job должен работать ≥7 дней** для накопления истории
3. **При первом добавлении** артикула `average_price_7days = NULL`

### Rate Limiting

- **10 запросов/минуту** для web scraping
- **Задержка 1-3 сек** между запросами (случайная)
- **Retry логика**: 3 попытки с экспоненциальным backoff

### Кэширование

- **TTL: 1 час** для OzonScraper
- **Кэш обновляется** при `refresh-prices`
- **Cron job не использует кэш** (всегда свежие данные)

---

## 🐛 Troubleshooting

### Проблема: `average_price_7days = NULL`

**Причина:** Недостаточно данных в price_history  
**Решение:**
1. Проверить запущен ли Cron Job: `docker logs cron-worker`
2. Подождать 7 дней для накопления истории
3. Вручную вызвать: `SELECT update_all_average_prices()`

### Проблема: Парсинг возвращает NULL для цен

**Причина:** Изменилась структура HTML на OZON  
**Решение:**
1. Проверить логи scraper
2. Обновить селекторы в `_parse_product_from_html()`
3. Использовать Playwright вместо httpx

### Проблема: Cron Job не собирает цены

**Причина:** Блокировка от OZON (403)  
**Решение:**
1. Увеличить `OZON_SCRAPER_DELAY` до 10 сек
2. Использовать Playwright (headless=True)
3. Добавить proxy/user-agent ротацию

---

## 📚 Миграции

Созданные миграции:
- **004_ozon_scraper_price_history.sql** - таблица истории цен
- **006_add_detailed_prices_to_articles.sql** - новые поля в articles

Применить миграции:

```bash
# Через Supabase Dashboard → SQL Editor
# Или через CLI:
supabase db push
```

---

## 🔗 Связанные документы

- [OZON_INTEGRATION.md](./OZON_INTEGRATION.md) - основная интеграция с OZON
- [CRON_SETUP.md](./CRON_SETUP.md) - настройка Cron Jobs
- [DATABASE.md](./DATABASE.md) - схема базы данных

---

## ✅ Критерии приёмки (Task AIL-305)

- [x] Создана таблица `ozon_scraper_price_history`
- [x] Реализован Cron Job для сбора истории цен
- [x] SQL функции для расчета средней цены работают
- [x] Парсинг цены без Ozon Card реализован
- [x] Парсинг цены с Ozon Card реализован
- [x] API endpoints для работы с ценами созданы
- [x] Добавлена обработка ошибок и логирование
- [x] Обновлена документация
- [x] Все тесты проходят

---

**Последнее обновление:** 2025-10-21  
**Автор:** AI Agent  
**Task:** AIL-305

