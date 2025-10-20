## Cron Jobs для OZON Scraper

Автоматические задачи для сбора данных и обслуживания системы.

---

## 📋 Список Cron Jobs

### 1. **Price History Collector** (`price_history_collector.py`)

**Назначение:** Автоматический сбор истории цен товаров OZON

**Расписание:** Каждые 24 часа (рекомендуется 03:00 ночи)

**Что делает:**
- Получает все активные артикулы из БД
- Для каждого артикула выполняет web scraping цен
- Сохраняет данные в таблицу `ozon_scraper_price_history`
- Логирует результаты выполнения

**Конфигурация:**
```bash
# .env
OZON_SCRAPER_BATCH_SIZE=10      # Количество артикулов в batch
OZON_SCRAPER_DELAY=5            # Задержка между запросами (сек)
```

---

## 🚀 Запуск

### Вручную (для тестирования)

```bash
cd backend
python -m cron_jobs.price_history_collector
```

### Через Docker Compose

```bash
docker-compose up cron-worker
```

### Через системный Cron (Linux/Mac)

```bash
# Открыть crontab
crontab -e

# Добавить задачу (каждый день в 03:00)
0 3 * * * cd /path/to/project/backend && python -m cron_jobs.price_history_collector >> /var/log/ozon_scraper_cron.log 2>&1
```

### Через GitHub Actions (рекомендуется)

Создать `.github/workflows/price_history_cron.yml`:

```yaml
name: Price History Collection

on:
  schedule:
    - cron: '0 3 * * *'  # Каждый день в 03:00 UTC
  workflow_dispatch:      # Ручной запуск

jobs:
  collect-prices:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      
      - name: Run price history collector
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}
          OZON_SCRAPER_BATCH_SIZE: 10
          OZON_SCRAPER_DELAY: 5
        run: |
          cd backend
          python -m cron_jobs.price_history_collector
```

---

## 📊 Мониторинг

### Просмотр логов

```bash
# Docker logs
docker-compose logs -f cron-worker

# System logs
tail -f /var/log/ozon_scraper_cron.log
```

### Проверка статистики в БД

```sql
-- Последние 10 запусков cron job
SELECT 
    timestamp,
    message,
    metadata->>'stats' as stats
FROM ozon_scraper_logs
WHERE event_type = 'cron_price_history_collection'
ORDER BY timestamp DESC
LIMIT 10;

-- Success rate за последние 7 дней
SELECT 
    DATE(timestamp) as date,
    COUNT(*) as total_runs,
    AVG((metadata->'stats'->>'successful')::int) as avg_successful,
    AVG((metadata->'stats'->>'failed')::int) as avg_failed
FROM ozon_scraper_logs
WHERE event_type = 'cron_price_history_collection'
  AND timestamp >= NOW() - INTERVAL '7 days'
GROUP BY DATE(timestamp)
ORDER BY date DESC;
```

---

## ⚙️ Настройка расписания

### Рекомендуемые расписания

| Cron Job | Расписание | Cron Expression | Описание |
|----------|-----------|-----------------|----------|
| Price History | Каждый день в 03:00 | `0 3 * * *` | Минимальная нагрузка |
| Price History | Каждые 12 часов | `0 */12 * * *` | Более частое обновление |
| Price History | Каждые 6 часов | `0 */6 * * *` | Для популярных товаров |

### Выбор времени

**Рекомендации:**
- ✅ 03:00 - 05:00 (ночь) - минимальная нагрузка на OZON
- ✅ Избегайте пиковых часов (10:00 - 22:00)
- ✅ Учитывайте часовой пояс сервера

---

## 🛠️ Разработка новых Cron Jobs

### Template для нового job

```python
"""
My Custom Cron Job

Description: What this job does
Schedule: When to run
"""

import asyncio
from loguru import logger
from database import get_supabase_client

class MyCustomJob:
    def __init__(self):
        self.supabase = get_supabase_client()
        self.stats = {"start_time": None, "end_time": None}
    
    async def run(self):
        logger.info("Starting My Custom Job...")
        try:
            # Your logic here
            pass
        except Exception as e:
            logger.error(f"Job failed: {e}")
        finally:
            self.log_execution()
    
    def log_execution(self):
        self.supabase.table("ozon_scraper_logs").insert({
            "level": "INFO",
            "event_type": "cron_my_custom_job",
            "message": "Job completed",
            "metadata": self.stats
        }).execute()

async def main():
    job = MyCustomJob()
    await job.run()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🐛 Troubleshooting

### Проблема: Cron job не запускается

**Решение:**
1. Проверить логи: `docker-compose logs cron-worker`
2. Проверить переменные окружения
3. Убедиться что БД доступна

### Проблема: Много ошибок scraping (403, timeout)

**Решение:**
1. Увеличить `OZON_SCRAPER_DELAY` (например, до 10 секунд)
2. Уменьшить `OZON_SCRAPER_BATCH_SIZE`
3. Проверить нет ли блокировки от OZON

### Проблема: Слишком долгое выполнение

**Решение:**
1. Уменьшить `delay_seconds` (осторожно с rate limits!)
2. Увеличить `batch_size`
3. Запускать реже (например, раз в 2 дня)

---

## 📈 Performance

### Примерное время выполнения

| Артикулов | Delay (сек) | Время выполнения |
|-----------|-------------|------------------|
| 100 | 5 | ~8 минут |
| 500 | 5 | ~42 минуты |
| 1000 | 5 | ~1.4 часа |
| 1000 | 2 | ~30 минут |

**Формула:** `время ≈ (количество_артикулов × delay) / 60` минут

---

## 🔒 Безопасность

### Best Practices

1. **Service Role Key:**
   - Используйте `SUPABASE_SERVICE_ROLE_KEY` (не anon key!)
   - Храните в секретах (GitHub Secrets, Docker Secrets)

2. **Rate Limiting:**
   - Не уменьшайте `delay` ниже 2 секунд
   - Мониторьте количество 403 ошибок

3. **Логирование:**
   - Все результаты логируются в БД
   - Настройте алерты на критические ошибки

---

## 📞 Support

Если возникли проблемы с cron jobs:
1. Проверьте логи в БД (таблица `ozon_scraper_logs`)
2. Запустите job вручную для отладки
3. Проверьте документацию OZON API

---

**Последнее обновление:** 2025-10-20

