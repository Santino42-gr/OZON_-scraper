# Настройка Cron Jobs для OZON Scraper

Полное руководство по настройке автоматического сбора истории цен.

---

## 📋 Обзор

Cron jobs необходимы для:
- ✅ **Автоматического сбора истории цен** (раз в 24 часа)
- ✅ **Расчета средней цены за 7 дней** (из собранной истории)
- ✅ **Очистки старых данных** (еженедельно)

**Почему это важно:**
- Seller API не подходит для многопользовательского бота
- Каждому пользователю нужны свои credentials
- Решение: собирать историю через web scraping автоматически

---

## 🚀 Быстрый старт

### 1. Проверка миграций БД

Убедитесь что выполнена миграция `004_ozon_scraper_price_history.sql`:

```bash
# Подключитесь к Supabase SQL Editor
# Выполните содержимое файла:
docs/migrations/004_ozon_scraper_price_history.sql
```

Проверка:

```sql
-- Таблица должна существовать
SELECT * FROM ozon_scraper_price_history LIMIT 1;

-- Функции должны работать
SELECT * FROM get_average_price_7days('TEST-ARTICLE', 7);
```

### 2. Настройка ENV переменных

Добавьте в `.env`:

```bash
# === Cron Job Configuration ===
OZON_SCRAPER_BATCH_SIZE=10      # Количество артикулов в batch
OZON_SCRAPER_DELAY=5            # Задержка между запросами (сек)

# === Playwright Configuration (для scraping) ===
PLAYWRIGHT_HEADLESS=true
PLAYWRIGHT_TIMEOUT=30000

# === Rate Limiting (для scraping) ===
OZON_RATE_LIMIT=10             # Макс запросов в минуту
OZON_TIMEOUT=30                # Timeout запроса (сек)
OZON_CACHE_TTL=3600            # TTL кэша (1 час)
```

### 3. Запуск через Docker Compose

```bash
# Запустить cron worker
docker-compose -f docker-compose.yml -f docker-compose.cron.yml up -d

# Проверить статус
docker-compose logs -f cron-worker

# Проверить расписание cron
docker exec ozon-scraper-cron cat /etc/crontabs/root
```

**Расписание по умолчанию:**
- `0 3 * * *` - Price History Collection (каждый день в 03:00)
- `0 4 * * 0` - Data Cleanup (каждое воскресенье в 04:00)

---

## 🛠️ Альтернативные способы запуска

### Способ 1: GitHub Actions (Рекомендуется)

**Преимущества:**
- ✅ Не требует выделенного сервера
- ✅ Бесплатно (GitHub Actions)
- ✅ Автоматическое логирование
- ✅ Легко настроить расписание

**Настройка:**

1. Создайте файл `.github/workflows/price_history_cron.yml`:

```yaml
name: Price History Collection

on:
  schedule:
    # Каждый день в 03:00 UTC
    - cron: '0 3 * * *'
  
  # Ручной запуск
  workflow_dispatch:

jobs:
  collect-prices:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Python 3.11
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install playwright
          playwright install chromium
      
      - name: Run Price History Collector
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}
          OZON_SCRAPER_BATCH_SIZE: 10
          OZON_SCRAPER_DELAY: 5
          PLAYWRIGHT_HEADLESS: true
        run: |
          cd backend
          python -m cron_jobs.price_history_collector
      
      - name: Upload logs
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: cron-logs
          path: backend/*.log
```

2. Добавьте секреты в GitHub:
   - Settings → Secrets and variables → Actions
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`

3. Проверьте работу:
   - Actions → Price History Collection → Run workflow

---

### Способ 2: Системный Cron (Linux/Mac)

**Для production сервера:**

```bash
# 1. Установить зависимости
cd /path/to/ozon-scraper/backend
pip install -r requirements.txt

# 2. Создать wrapper скрипт
cat > /usr/local/bin/ozon-price-collector.sh << 'EOF'
#!/bin/bash
set -e

# Переменные окружения
export SUPABASE_URL="your-supabase-url"
export SUPABASE_SERVICE_ROLE_KEY="your-service-key"
export OZON_SCRAPER_BATCH_SIZE=10
export OZON_SCRAPER_DELAY=5

# Запуск
cd /path/to/ozon-scraper/backend
python -m cron_jobs.price_history_collector
EOF

# 3. Сделать исполняемым
chmod +x /usr/local/bin/ozon-price-collector.sh

# 4. Добавить в crontab
crontab -e

# Добавить строку:
0 3 * * * /usr/local/bin/ozon-price-collector.sh >> /var/log/ozon_scraper_cron.log 2>&1
```

---

### Способ 3: Вручную (для тестирования)

```bash
cd backend

# Установить зависимости
pip install -r requirements.txt

# Запустить сборщик
python -m cron_jobs.price_history_collector

# Запустить очистку данных
python -m cron_jobs.cleanup_old_data
```

---

## 📊 Мониторинг и проверка

### 1. Проверка логов в БД

```sql
-- Последние запуски cron job
SELECT 
    timestamp,
    level,
    message,
    metadata->'stats' as stats
FROM ozon_scraper_logs
WHERE event_type = 'cron_price_history_collection'
ORDER BY timestamp DESC
LIMIT 10;

-- Статистика за последние 7 дней
SELECT 
    DATE(timestamp) as date,
    COUNT(*) as total_runs,
    AVG((metadata->'stats'->>'successful')::int) as avg_successful,
    AVG((metadata->'stats'->>'total_articles')::int) as avg_total,
    ROUND(AVG((metadata->'stats'->>'successful')::float / NULLIF((metadata->'stats'->>'total_articles')::float, 0)) * 100, 2) as success_rate_pct
FROM ozon_scraper_logs
WHERE event_type = 'cron_price_history_collection'
  AND timestamp >= NOW() - INTERVAL '7 days'
GROUP BY DATE(timestamp)
ORDER BY date DESC;
```

### 2. Проверка собранной истории

```sql
-- Сколько записей в истории
SELECT COUNT(*) as total_records FROM ozon_scraper_price_history;

-- По артикулам
SELECT 
    article_number,
    COUNT(*) as data_points,
    MIN(price_date) as first_record,
    MAX(price_date) as last_record,
    AVG(price) as avg_price
FROM ozon_scraper_price_history
GROUP BY article_number
ORDER BY data_points DESC
LIMIT 10;

-- Средняя цена за 7 дней (тест функции)
SELECT * FROM get_average_price_7days('YOUR-ARTICLE-NUMBER', 7);
```

### 3. Алерты на ошибки

Создайте SQL функцию для алертов:

```sql
CREATE OR REPLACE FUNCTION check_cron_health()
RETURNS TABLE (
    status TEXT,
    last_run TIMESTAMP,
    hours_since_run NUMERIC,
    last_success_rate NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        CASE 
            WHEN MAX(timestamp) < NOW() - INTERVAL '26 hours' THEN 'CRITICAL'
            WHEN AVG((metadata->'stats'->>'successful')::float / NULLIF((metadata->'stats'->>'total_articles')::float, 0)) < 0.7 THEN 'WARNING'
            ELSE 'OK'
        END as status,
        MAX(timestamp) as last_run,
        EXTRACT(EPOCH FROM (NOW() - MAX(timestamp))) / 3600 as hours_since_run,
        ROUND(AVG((metadata->'stats'->>'successful')::float / NULLIF((metadata->'stats'->>'total_articles')::float, 0)) * 100, 2) as last_success_rate
    FROM ozon_scraper_logs
    WHERE event_type = 'cron_price_history_collection'
      AND timestamp >= NOW() - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql;

-- Проверка здоровья
SELECT * FROM check_cron_health();
```

---

## ⚙️ Настройка расписания

### Рекомендации по частоте

| Сценарий | Частота | Cron Expression | Причина |
|----------|---------|-----------------|---------|
| **Стандартный** | 1 раз в день | `0 3 * * *` | Минимальная нагрузка, достаточно для средней за 7 дней |
| **Активный мониторинг** | 2 раза в день | `0 3,15 * * *` | Более актуальные данные |
| **Интенсивный** | 4 раза в день | `0 */6 * * *` | Для быстро меняющихся цен |
| **Разработка/Тест** | Каждый час | `0 * * * *` | Только для тестирования! |

### Калькулятор времени выполнения

```
Время выполнения ≈ (Количество артикулов × Delay) / 60 минут

Примеры:
- 100 артикулов × 5 сек = ~8 минут
- 500 артикулов × 5 сек = ~42 минуты
- 1000 артикулов × 5 сек = ~1.4 часа
```

**Рекомендации:**
- ✅ Запускайте ночью (03:00 - 05:00) для минимальной нагрузки
- ✅ Если >500 артикулов - уменьшите `delay` до 2-3 сек
- ✅ Мониторьте Success Rate (должен быть >80%)

---

## 🐛 Troubleshooting

### Проблема: Cron не запускается

**Проверка:**
```bash
# Docker
docker ps | grep cron
docker logs ozon-scraper-cron

# GitHub Actions
# Actions → Price History Collection → Последний запуск
```

**Решение:**
1. Проверьте ENV переменные
2. Убедитесь что БД доступна
3. Проверьте логи

### Проблема: Много ошибок (Success Rate < 80%)

**Причины:**
- 403 ошибки (блокировка OZON)
- Timeout errors
- Неверные артикулы

**Решение:**
```bash
# Увеличить delay между запросами
OZON_SCRAPER_DELAY=10

# Уменьшить batch size
OZON_SCRAPER_BATCH_SIZE=5

# Проверить неверные артикулы
SELECT article_number 
FROM ozon_scraper_price_history 
WHERE scraping_success = FALSE
GROUP BY article_number
HAVING COUNT(*) > 3;
```

### Проблема: Cron не выполнился вовремя

**Проверка:**
```sql
SELECT 
    timestamp,
    NOW() - timestamp as time_since_last_run
FROM ozon_scraper_logs
WHERE event_type = 'cron_price_history_collection'
ORDER BY timestamp DESC
LIMIT 1;
```

**Решение:**
1. Проверить GitHub Actions quota (если используется)
2. Проверить статус Docker контейнера
3. Проверить системный cron: `systemctl status cron`

---

## 📈 Оптимизация

### Для больших объемов (>1000 артикулов)

```python
# Параллельный scraping (НЕ рекомендуется, risk of ban)
OZON_SCRAPER_BATCH_SIZE=20
OZON_SCRAPER_DELAY=2

# Или: Запускать чаще, но меньшими порциями
# Утром: первые 500 артикулов
# Вечером: следующие 500 артикулов
```

### Приоритизация артикулов

Добавьте поле `priority` в таблицу `ozon_scraper_articles`:

```sql
ALTER TABLE ozon_scraper_articles 
ADD COLUMN scraping_priority INTEGER DEFAULT 1;

-- Популярные товары = высокий приоритет
UPDATE ozon_scraper_articles 
SET scraping_priority = 5 
WHERE id IN (SELECT TOP 100 по популярности);
```

Обновите cron job для приоритетной обработки.

---

## ✅ Checklist установки

- [ ] Выполнена миграция `004_ozon_scraper_price_history.sql`
- [ ] Проверена работа SQL функций (`get_average_price_7days`)
- [ ] Настроены ENV переменные
- [ ] Запущен cron worker (Docker / GitHub Actions / System Cron)
- [ ] Проверены первые запуски (вручную)
- [ ] Настроен мониторинг логов
- [ ] Созданы алерты на критические ошибки
- [ ] Документировано расписание

---

**Дата создания:** 2025-10-20  
**Последнее обновление:** 2025-10-20

Для вопросов см. `backend/cron_jobs/README.md`

