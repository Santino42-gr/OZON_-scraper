# Руководство по применению миграции 008 - Comparison Feature

> **Статус:** Готово к применению
> **Дата создания:** 2025-10-30
> **Миграция:** 008_article_comparison.sql

---

## 📋 Что добавляет миграция

### Новые таблицы:

1. **`ozon_scraper_article_groups`** - Группы сравнения артикулов
   - Хранит информацию о созданных группах для сравнения
   - Поддержка разных типов: comparison, variants, similar

2. **`ozon_scraper_article_group_members`** - Связь артикулов с группами (N-to-N)
   - Позволяет одному артикулу быть в нескольких группах
   - Роли: own (свой товар), competitor (конкурент), item (обычный)

3. **`ozon_scraper_comparison_snapshots`** - История сравнений
   - Хранит снэпшоты сравнений для отслеживания изменений
   - Индекс конкурентоспособности, метрики, рекомендации

### SQL Функции:

- `get_group_comparison(p_group_id)` - Получить данные для сравнения
- `save_comparison_snapshot(...)` - Сохранить снэпшот
- `get_comparison_history(p_group_id, p_days)` - Получить историю
- `cleanup_old_snapshots(p_retention_days)` - Очистка старых данных
- `get_user_groups_stats(p_user_id)` - Статистика пользователя

### Безопасность:

- ✅ Row Level Security (RLS) для всех таблиц
- ✅ Политики доступа: пользователи видят только свои данные
- ✅ Правильные grants для authenticated и service_role

---

## 🚀 Применение миграции

### Шаг 1: Проверка готовности

Убедитесь, что все предыдущие миграции применены:

```sql
-- Проверьте наличие таблицы articles со всеми полями
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'ozon_scraper_articles'
  AND column_name IN ('spp1', 'spp2', 'spp_total', 'normal_price', 'ozon_card_price')
ORDER BY column_name;
```

Должны быть видны все поля из миграций 006 и 007.

### Шаг 2: Применение в Supabase

#### Вариант A: Через Supabase Dashboard

1. Откройте Supabase Dashboard: https://app.supabase.com
2. Выберите ваш проект
3. Перейдите в раздел **SQL Editor**
4. Создайте новый запрос
5. Скопируйте содержимое файла `docs/migrations/008_article_comparison.sql`
6. Вставьте в редактор и нажмите **Run**

#### Вариант B: Через Supabase CLI (если установлен)

```bash
# 1. Убедитесь что связаны с проектом
supabase link --project-ref YOUR_PROJECT_REF

# 2. Примените миграцию
supabase db push

# Или вручную:
psql "postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres" \
  -f docs/migrations/008_article_comparison.sql
```

### Шаг 3: Проверка применения

После применения миграции выполните следующие проверки:

```sql
-- 1. Проверка создания таблиц
SELECT table_name
FROM information_schema.tables
WHERE table_name IN (
    'ozon_scraper_article_groups',
    'ozon_scraper_article_group_members',
    'ozon_scraper_comparison_snapshots'
)
ORDER BY table_name;

-- 2. Проверка индексов
SELECT tablename, indexname
FROM pg_indexes
WHERE tablename IN (
    'ozon_scraper_article_groups',
    'ozon_scraper_article_group_members',
    'ozon_scraper_comparison_snapshots'
)
ORDER BY tablename, indexname;

-- 3. Проверка функций
SELECT routine_name, routine_type
FROM information_schema.routines
WHERE routine_name IN (
    'get_group_comparison',
    'save_comparison_snapshot',
    'get_comparison_history',
    'cleanup_old_snapshots',
    'get_user_groups_stats'
)
ORDER BY routine_name;

-- 4. Проверка RLS политик
SELECT tablename, policyname, cmd
FROM pg_policies
WHERE tablename IN (
    'ozon_scraper_article_groups',
    'ozon_scraper_article_group_members',
    'ozon_scraper_comparison_snapshots'
)
ORDER BY tablename, policyname;
```

### Ожидаемые результаты:

1. **Таблицы:** 3 новые таблицы созданы
2. **Индексы:** 11 индексов созданы
3. **Функции:** 5 функций созданы
4. **Политики:** 8 RLS политик активированы

---

## 🧪 Тестирование

После применения миграции можно протестировать функционал:

```sql
-- 1. Создать тестовую группу (замените USER_ID на реальный)
INSERT INTO ozon_scraper_article_groups (user_id, name, group_type)
VALUES ('YOUR_USER_UUID', 'Test Comparison', 'comparison')
RETURNING id;

-- 2. Проверить статистику (замените USER_ID)
SELECT * FROM get_user_groups_stats('YOUR_USER_UUID');

-- 3. Удалить тестовую группу
DELETE FROM ozon_scraper_article_groups
WHERE name = 'Test Comparison' AND user_id = 'YOUR_USER_UUID';
```

---

## ⚠️ Откат (Rollback)

Если что-то пошло не так, можно откатить миграцию:

```sql
BEGIN;

-- Удалить функции
DROP FUNCTION IF EXISTS get_user_groups_stats(UUID);
DROP FUNCTION IF EXISTS cleanup_old_snapshots(INTEGER);
DROP FUNCTION IF EXISTS get_comparison_history(UUID, INTEGER);
DROP FUNCTION IF EXISTS save_comparison_snapshot(UUID, JSONB, JSONB, DECIMAL);
DROP FUNCTION IF EXISTS get_group_comparison(UUID);

-- Удалить таблицы (CASCADE удалит все связанные объекты)
DROP TABLE IF EXISTS ozon_scraper_comparison_snapshots CASCADE;
DROP TABLE IF EXISTS ozon_scraper_article_group_members CASCADE;
DROP TABLE IF EXISTS ozon_scraper_article_groups CASCADE;

COMMIT;
```

---

## 📊 Мониторинг

После применения миграции следите за:

- **Размером таблиц:** `SELECT pg_size_pretty(pg_total_relation_size('ozon_scraper_article_groups'));`
- **Количеством записей:** `SELECT COUNT(*) FROM ozon_scraper_article_groups;`
- **Производительностью запросов:** используйте `EXPLAIN ANALYZE`

---

## ✅ Чеклист готовности к production

- [ ] Миграция применена в dev окружении
- [ ] Все проверки пройдены успешно
- [ ] Тестовые запросы работают
- [ ] Производительность в норме
- [ ] Backup базы данных создан перед применением в production
- [ ] Rollback план готов
- [ ] Мониторинг настроен

---

## 📝 Следующие шаги

После успешного применения миграции:

1. ✅ Фаза 1 завершена
2. 🔄 Переходим к **Фазе 2:** Backend Models & Service
   - Создать `backend/models/comparison.py`
   - Создать `backend/services/comparison_service.py`

---

**Статус:** ✅ Миграция готова к применению
