# План имплементации функционала сравнения артикулов (свой + конкурент)

> **Создано:** 2025-10-29
> **Статус:** Планирование
> **Приоритет:** Высокий (основной функционал)

---

## 🎯 ЦЕЛЬ

Добавить возможность сравнивать свой артикул с артикулом конкурента с расчетом метрик (цены, рейтинг, СПП) и рекомендациями.

### Бизнес-требования:

1. **Добавление пары артикулов:**
   - Пользователь добавляет СВОЙ артикул (который он продает)
   - Пользователь добавляет артикул КОНКУРЕНТА
   - Эти два артикула связаны и сравниваются друг с другом

2. **Сбор данных:**
   - Для своего артикула: цена, normal_price, ozon_card_price, рейтинг, остатки, СПП
   - Для артикула конкурента: те же параметры
   - История цен для обоих артикулов (каждые 24 часа через Cron)

3. **Расчет метрик:**
   - СПП для своего артикула и конкурента (по существующим формулам)
   - Разница в ценах (абсолютная и процентная)
   - Разница в рейтингах
   - Разница в остатках
   - **Индекс конкурентоспособности** (0-1) с грейдами A-F

4. **Отчеты:**
   - Показывать оба артикула рядом в боте
   - Сравнительная таблица по всем параметрам
   - История изменения разницы в ценах
   - Автоматические рекомендации (например: "Ваша цена выше на 15%")

---

## 📋 АРХИТЕКТУРНЫЕ РЕШЕНИЯ

### Выбранная архитектура БД: **Вариант В - Гибкая группировка через article_groups**

**Обоснование:**
- ✅ **Масштабируемость**: Можно сравнивать 2+ артикулов (не только пары)
- ✅ **Гибкость**: Поддержка N-to-N связей (1 артикул в нескольких группах)
- ✅ **Расширяемость**: Легко добавить типы групп (competitor, variant, similar)
- ✅ **Обратная совместимость**: Существующие артикулы работают без изменений
- ✅ **Чистота архитектуры**: Нормализованная структура БД

**Структура:**

```
ozon_scraper_article_groups
├─ id (UUID)
├─ user_id (UUID)
├─ name (TEXT)
├─ group_type (TEXT: 'comparison', 'variants', 'similar')
├─ created_at
└─ updated_at

ozon_scraper_article_group_members (N-to-N)
├─ id (UUID)
├─ group_id (UUID → article_groups)
├─ article_id (UUID → articles)
├─ role (TEXT: 'own', 'competitor', 'item')
├─ position (INTEGER)
└─ added_at

ozon_scraper_comparison_snapshots
├─ id (UUID)
├─ group_id (UUID → article_groups)
├─ snapshot_date
├─ comparison_data (JSONB)
├─ metrics (JSONB)
├─ competitiveness_index (DECIMAL)
└─ created_at
```

---

## 📋 ФАЗА 1: База данных (День 1)

### Задачи:

- [ ] **1.1. Создать SQL миграцию** `backend/migrations/008_article_comparison.sql`
  - Таблица `ozon_scraper_article_groups` (группы сравнения)
  - Таблица `ozon_scraper_article_group_members` (связь N-to-N артикулов с группами)
  - Таблица `ozon_scraper_comparison_snapshots` (история сравнений)
  - Индексы для производительности
  - RLS policies для безопасности
  - Триггеры для updated_at
  - SQL функции: `get_group_comparison()`, `save_comparison_snapshot()`

- [ ] **1.2. Применить миграцию в Supabase**
  - Development: Применить локально для тестов
  - Production: Применить на сервере после тестирования

### SQL Миграция (детали):

```sql
-- =====================================================
-- Migration 008: Article Comparison Feature
-- =====================================================

BEGIN;

-- 1. Таблица групп артикулов
CREATE TABLE IF NOT EXISTS ozon_scraper_article_groups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES ozon_scraper_users(id) ON DELETE CASCADE,
    name TEXT,
    group_type TEXT DEFAULT 'comparison',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT valid_group_type CHECK (group_type IN ('comparison', 'variants', 'similar'))
);

-- 2. Таблица членов группы (связь многие-ко-многим)
CREATE TABLE IF NOT EXISTS ozon_scraper_article_group_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    group_id UUID NOT NULL REFERENCES ozon_scraper_article_groups(id) ON DELETE CASCADE,
    article_id UUID NOT NULL REFERENCES ozon_scraper_articles(id) ON DELETE CASCADE,
    role TEXT DEFAULT 'item',
    position INTEGER DEFAULT 0,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT valid_role CHECK (role IN ('own', 'competitor', 'item')),
    CONSTRAINT unique_group_article UNIQUE (group_id, article_id)
);

-- 3. Таблица снэпшотов сравнений (для истории)
CREATE TABLE IF NOT EXISTS ozon_scraper_comparison_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    group_id UUID NOT NULL REFERENCES ozon_scraper_article_groups(id) ON DELETE CASCADE,
    snapshot_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    comparison_data JSONB NOT NULL,
    metrics JSONB,
    competitiveness_index DECIMAL(3,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Индексы
CREATE INDEX idx_article_groups_user_id ON ozon_scraper_article_groups(user_id);
CREATE INDEX idx_article_groups_type ON ozon_scraper_article_groups(group_type);
CREATE INDEX idx_group_members_group_id ON ozon_scraper_article_group_members(group_id);
CREATE INDEX idx_group_members_article_id ON ozon_scraper_article_group_members(article_id);
CREATE INDEX idx_group_members_role ON ozon_scraper_article_group_members(role);
CREATE INDEX idx_comparison_snapshots_group_date ON ozon_scraper_comparison_snapshots(group_id, snapshot_date DESC);
CREATE INDEX idx_comparison_snapshots_metrics ON ozon_scraper_comparison_snapshots USING GIN(metrics);
CREATE INDEX idx_comparison_snapshots_index ON ozon_scraper_comparison_snapshots(competitiveness_index);

-- Триггеры
CREATE TRIGGER update_article_groups_updated_at
    BEFORE UPDATE ON ozon_scraper_article_groups
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- RLS Policies
ALTER TABLE ozon_scraper_article_groups ENABLE ROW LEVEL SECURITY;
ALTER TABLE ozon_scraper_article_group_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE ozon_scraper_comparison_snapshots ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own groups"
    ON ozon_scraper_article_groups FOR SELECT
    USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can create own groups"
    ON ozon_scraper_article_groups FOR INSERT
    WITH CHECK (auth.uid()::text = user_id::text);

CREATE POLICY "Users can update own groups"
    ON ozon_scraper_article_groups FOR UPDATE
    USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can delete own groups"
    ON ozon_scraper_article_groups FOR DELETE
    USING (auth.uid()::text = user_id::text);

-- Grants
GRANT SELECT, INSERT, UPDATE, DELETE ON ozon_scraper_article_groups TO authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON ozon_scraper_article_group_members TO authenticated, service_role;
GRANT SELECT, INSERT ON ozon_scraper_comparison_snapshots TO authenticated, service_role;

-- SQL Функции
CREATE OR REPLACE FUNCTION get_group_comparison(p_group_id UUID)
RETURNS TABLE (
    article_id UUID,
    article_number TEXT,
    role TEXT,
    current_price DECIMAL(10,2),
    current_rating DECIMAL(3,2),
    spp_total DECIMAL(5,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        a.id,
        a.article_number,
        m.role,
        a.price,
        a.rating,
        a.spp_total
    FROM ozon_scraper_article_group_members m
    JOIN ozon_scraper_articles a ON m.article_id = a.id
    WHERE m.group_id = p_group_id
    ORDER BY m.position, m.added_at;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION save_comparison_snapshot(
    p_group_id UUID,
    p_comparison_data JSONB,
    p_metrics JSONB,
    p_competitiveness_index DECIMAL(3,2)
)
RETURNS UUID AS $$
DECLARE
    v_snapshot_id UUID;
BEGIN
    INSERT INTO ozon_scraper_comparison_snapshots (
        group_id,
        comparison_data,
        metrics,
        competitiveness_index
    ) VALUES (
        p_group_id,
        p_comparison_data,
        p_metrics,
        p_competitiveness_index
    ) RETURNING id INTO v_snapshot_id;

    RETURN v_snapshot_id;
END;
$$ LANGUAGE plpgsql;

COMMIT;
```

---

## 📋 ФАЗА 2: Backend Models & Service (День 2)

### Задачи:

- [ ] **2.1. Создать `backend/models/comparison.py`:**
  - `ArticleRole` (Enum: own, competitor, item)
  - `GroupType` (Enum: comparison, variants, similar)
  - `ArticleGroupMemberCreate` - добавление артикула в группу
  - `ArticleGroupCreate` - создание группы
  - `ArticleGroupMemberResponse` - член группы
  - `ArticleGroupResponse` - группа артикулов
  - `PriceDifference` - разница в ценах
  - `RatingDifference` - разница в рейтингах
  - `SPPDifference` - разница в СПП
  - `ComparisonMetrics` - все метрики сравнения
  - `ArticleComparisonData` - данные артикула для сравнения
  - `ComparisonResponse` - полное сравнение
  - `ComparisonSnapshotResponse` - снэпшот из истории

- [ ] **2.2. Создать `backend/services/comparison_service.py`:**
  - `ComparisonService` class
  - `create_comparison_group()` - создать группу + scrape оба артикула
  - `get_comparison()` - получить сравнение с метриками
  - `refresh_comparison()` - обновить данные (re-scrape)
  - `get_comparison_history()` - история снэпшотов
  - `delete_group()` - удалить группу
  - `_calculate_comparison_metrics()` - расчет всех метрик
  - `_calculate_competitiveness_index()` - индекс 0-1 (взвешенная формула)
  - `_get_grade()` - грейды A-F
  - `_generate_recommendations()` - автоматические рекомендации
  - `_save_snapshot()` - сохранить снэпшот
  - `_get_or_create_article()` - получить/создать артикул

### Ключевые метрики:

**Разница в ценах:**
```python
PriceDifference:
  - absolute: float (разница в рублях)
  - percentage: float (разница в процентах)
  - who_cheaper: str ('own' или 'competitor')
  - recommendation: str (например: "Снизьте цену на 5-7%")
```

**Индекс конкурентоспособности (0-1):**
```python
# Взвешенная формула:
weights = {
    'price': 0.35,      # 35% - цена
    'rating': 0.25,     # 25% - рейтинг
    'spp': 0.20,        # 20% - СПП
    'reviews': 0.10,    # 10% - количество отзывов
    'availability': 0.10 # 10% - наличие товара
}

# Грейды:
A: 0.85-1.00  (Отличная конкурентоспособность)
B: 0.70-0.84  (Хорошая конкурентоспособность)
C: 0.50-0.69  (Средняя конкурентоспособность)
D: 0.30-0.49  (Низкая конкурентоспособность)
F: 0.00-0.29  (Очень низкая конкурентоспособность)
```

---

## 📋 ФАЗА 3: Backend API (День 2-3)

### Задачи:

- [ ] **3.1. Создать `backend/routers/comparisons.py`:**
  - `POST /api/v1/article-groups` - создать группу сравнения
  - `GET /api/v1/article-groups` - список групп пользователя (с фильтром по типу)
  - `GET /api/v1/article-groups/{id}` - детали группы
  - `GET /api/v1/article-groups/{id}/comparison` - сравнение с метриками
  - `POST /api/v1/article-groups/{id}/refresh` - обновить данные (re-scrape)
  - `GET /api/v1/article-groups/{id}/history` - история снэпшотов за N дней
  - `DELETE /api/v1/article-groups/{id}` - удалить группу
  - `POST /api/v1/article-groups/{id}/members` - добавить артикул в группу
  - `DELETE /api/v1/article-groups/{id}/members/{article_id}` - удалить артикул из группы

- [ ] **3.2. Зарегистрировать router в `backend/main.py`:**
  ```python
  from routers import comparisons

  app.include_router(
      comparisons.router,
      prefix="/api/v1",
      tags=["comparisons"]
  )
  ```

- [ ] **3.3. Исправить существующую ошибку `average_price_7days = None`:**
  - В `backend/routers/articles.py` (create_article endpoint)
  - Добавить fallback: если `average_price_7days` None → использовать `normal_price`
  - Это позволит СПП рассчитываться корректно даже для новых артикулов

### API Schemas (примеры):

**POST /api/v1/article-groups - Request:**
```json
{
  "user_id": "uuid",
  "name": "Мой товар vs Конкурент",
  "group_type": "comparison",
  "articles": [
    {"article_number": "123456789", "role": "own"},
    {"article_number": "987654321", "role": "competitor"}
  ]
}
```

**GET /api/v1/article-groups/{id}/comparison - Response:**
```json
{
  "group_id": "uuid",
  "group_name": "Мой товар vs Конкурент",
  "compared_at": "2025-10-29T12:00:00Z",
  "articles": [
    {
      "article_id": "uuid",
      "article_number": "123456789",
      "role": "own",
      "name": "Товар название",
      "price": 1999.00,
      "ozon_card_price": 1799.00,
      "rating": 4.5,
      "reviews_count": 120,
      "spp_total": 15.2
    },
    {
      "article_id": "uuid",
      "article_number": "987654321",
      "role": "competitor",
      "name": "Конкурент название",
      "price": 1899.00,
      "ozon_card_price": 1699.00,
      "rating": 4.7,
      "reviews_count": 200,
      "spp_total": 18.1
    }
  ],
  "metrics": {
    "price_difference": {
      "absolute": 100.00,
      "percentage": 5.9,
      "who_cheaper": "competitor",
      "recommendation": "Ваша цена выше на 5.9%. Рассмотрите снижение."
    },
    "rating_difference": {
      "absolute": -0.2,
      "percentage": -4.3,
      "who_better": "competitor"
    },
    "spp_difference": {
      "spp_total": -2.9,
      "who_better": "competitor"
    },
    "competitiveness_index": 0.72,
    "competitiveness_grade": "C",
    "recommendations": [
      "Снизьте цену на 5-7% для повышения конкурентоспособности",
      "Ваш рейтинг ниже - работайте над качеством товара/сервиса",
      "Увеличьте СПП до уровня конкурента"
    ]
  }
}
```

---

## 📋 ФАЗА 4: Bot Integration (День 3-4)

### Задачи:

- [ ] **4.1. Создать `bot/handlers/comparisons.py`:**
  - FSM States: `waiting_for_own_article`, `waiting_for_competitor_article`
  - `cmd_compare()` - команда /compare
  - `process_own_article()` - обработка своего артикула
  - `process_competitor_article()` - обработка конкурента + создание сравнения
  - `cmd_list_comparisons()` - список всех сравнений пользователя
  - `callback_refresh_comparison()` - обновить данные (callback кнопки)
  - `callback_show_history()` - показать историю сравнений
  - `callback_delete_comparison()` - удалить группу (с подтверждением)

- [ ] **4.2. Создать `bot/utils/formatters.py` дополнение:**
  - `format_comparison(comparison: Dict) -> str` - красивый вывод сравнения
  - `format_comparison_list(comparisons: List[Dict]) -> str` - список сравнений
  - `format_comparison_history(history: List[Dict]) -> str` - история

- [ ] **4.3. Обновить `bot/keyboards.py`:**
  - `get_comparison_keyboard(group_id: str)` - кнопки [🔄 Обновить] [📊 История] [🗑 Удалить]
  - `get_comparison_list_keyboard(comparisons: List[Dict])` - inline кнопки для списка
  - Добавить "📊 Сравнения" в главное меню `get_main_menu()`

- [ ] **4.4. Обновить `bot/services/api_client.py`:**
  - `create_comparison_group(user_id, own_article, competitor_article)` → ArticleGroupResponse
  - `get_user_comparisons(user_id)` → List[ArticleGroupResponse]
  - `get_comparison(group_id, refresh=False)` → ComparisonResponse
  - `refresh_comparison(group_id)` → ComparisonResponse
  - `get_comparison_history(group_id, days=30)` → List[ComparisonSnapshotResponse]
  - `delete_comparison_group(group_id)` → success/error

- [ ] **4.5. Зарегистрировать router в `bot/main.py`:**
  ```python
  from handlers import comparisons

  dp.include_router(comparisons.router)
  ```

### Bot Flow (детальный):

```
1. Пользователь: /compare
   ↓
   Бот: "➕ Создание сравнения

         Отправьте СВОЙ артикул (который вы продаёте):
         📝 Пример: 123456789

         ❌ Отмена"

2. Пользователь: 123456789
   ↓
   Валидация артикула (5-12 цифр)
   ↓
   FSM State: waiting_for_competitor_article
   ↓
   Бот: "✅ Ваш артикул: 123456789

         Теперь отправьте артикул КОНКУРЕНТА:
         📝 Пример: 987654321

         ❌ Отмена"

3. Пользователь: 987654321
   ↓
   Валидация артикула
   ↓
   API: create_comparison_group(user_id, 123456789, 987654321)
   ↓
   Scraping данных для обоих артикулов (~10-15 сек)
   ↓
   Расчёт метрик сравнения
   ↓
   FSM State: clear
   ↓
   Бот: [Форматированное сравнение с метриками]

        📊 СРАВНЕНИЕ АРТИКУЛОВ

        🟢 ВАШ ТОВАР: 123456789
        ├─ Название: Товар...
        ├─ Цена: 1999 ₽
        ├─ С Ozon Card: 1799 ₽
        ├─ Рейтинг: 4.5 ⭐
        └─ СПП: 15.2%

        🔴 КОНКУРЕНТ: 987654321
        ├─ Название: Конкурент...
        ├─ Цена: 1899 ₽
        ├─ С Ozon Card: 1699 ₽
        ├─ Рейтинг: 4.7 ⭐
        └─ СПП: 18.1%

        📈 РАЗНИЦА:
        ❌ Ваша цена выше на 100₽ (5.9%)
        ❌ Ваш рейтинг ниже на -0.2
        ❌ Ваш СПП ниже на -2.9%

        🎯 ИНДЕКС КОНКУРЕНТОСПОСОБНОСТИ:
        ⚡ 0.72 (Грейд: C - Средняя конкурентоспособность)

        💡 РЕКОМЕНДАЦИИ:
        • Снизьте цену на 5-7%
        • Работайте над рейтингом
        • Увеличьте СПП

        [🔄 Обновить] [📊 История] [🗑 Удалить]
```

**Альтернативные сценарии:**
- Если артикул не найден на OZON → "❌ Товар не найден. Проверьте артикул"
- Если пара уже существует → "⚠️ Такое сравнение уже есть. [Открыть]"
- Если лимит групп достигнут (10) → "❌ Достигнут лимит. Удалите старые"
- Если scraping не удался → "❌ Не удалось получить данные. Попробуйте позже"

---

## 📋 ФАЗА 5: Cron Job для истории (День 5)

### Задачи:

- [ ] **5.1. Обновить `backend/services/scheduler.py`:**
  - Добавить задачу `update_comparison_snapshots()`
  - Для каждой активной группы:
    1. Получить артикулы группы
    2. Scrape данные для каждого артикула
    3. Рассчитать метрики сравнения
    4. Сохранить снэпшот в `comparison_snapshots`
  - Расписание: каждые 24 часа (аналогично `price_history_collector`)
  - Логирование успехов/ошибок

- [ ] **5.2. Обновить `backend/main.py`:**
  - Зарегистрировать новую cron задачу при startup

### Псевдокод Cron Job:

```python
async def update_comparison_snapshots():
    """
    Обновить снэпшоты для всех активных групп сравнения

    Запускается каждые 24 часа через scheduler
    """
    logger.info("Starting comparison snapshots update...")

    supabase = get_supabase_client()
    comparison_service = ComparisonService()

    # Получить все группы
    groups = supabase.table("ozon_scraper_article_groups")\
        .select("*")\
        .execute()

    total = len(groups.data)
    success = 0
    errors = 0

    for group in groups.data:
        try:
            # Обновить данные и получить сравнение
            comparison = await comparison_service.get_comparison(
                group_id=group["id"],
                refresh=True  # Re-scrape
            )

            # Снэпшот уже сохранён внутри get_comparison
            success += 1
            logger.info(f"Snapshot saved for group {group['id']}")

        except Exception as e:
            errors += 1
            logger.error(f"Error for group {group['id']}: {e}")

    logger.success(f"Comparison snapshots updated: {success}/{total} (errors: {errors})")
```

### Польза снэпшотов:

- **История изменений:** "Неделю назад ваша цена была выгоднее"
- **Графики:** Визуализация изменения индекса конкурентоспособности
- **Тренды:** "Конкурент постепенно снижает цены последние 7 дней"
- **Аналитика:** Какие факторы влияли на изменение позиции
- **Алерты:** "Конкурент снизил цену на 10% - пора реагировать!"

---

## 📋 ФАЗА 6: Тестирование (День 6)

### Задачи:

- [ ] **6.1. Backend unit тесты:**
  - `test_create_comparison_group()` - создание группы
  - `test_calculate_comparison_metrics()` - расчет метрик
  - `test_competitiveness_index()` - индекс конкурентоспособности
  - `test_save_snapshot()` - сохранение снэпшота
  - `test_get_comparison_history()` - получение истории
  - `test_delete_group()` - удаление группы

- [ ] **6.2. API integration тесты:**
  - Полный flow: создание → получение → обновление → удаление
  - Проверка метрик и рекомендаций
  - Обработка ошибок (несуществующие артикулы, лимиты)

- [ ] **6.3. Bot integration тесты:**
  - Полный flow через FSM
  - Обработка команд /compare, /comparisons
  - Callback buttons (обновить, история, удалить)

- [ ] **6.4. Manual тестирование:**
  - Реальные артикулы OZON
  - Проверка форматирования сообщений
  - UI/UX бота (читаемость, удобство)
  - Edge cases (недоступные товары, большие разницы в ценах)

- [ ] **6.5. Performance тесты:**
  - Время создания сравнения (должно быть <20 сек)
  - Нагрузка на БД при большом количестве групп
  - Cron job производительность

---

## 📋 ФАЗА 7: Deployment (День 7)

### Задачи:

- [ ] **7.1. Подготовка к деплою:**
  - Проверить все миграции в dev окружении
  - Code review всех изменений
  - Обновить документацию (README, API docs)

- [ ] **7.2. Деплой на сервер:**
  ```bash
  # 1. Применить миграцию в Supabase production
  # (через Supabase Dashboard или SQL Editor)

  # 2. Подтянуть изменения
  git pull origin main

  # 3. Пересобрать backend
  docker-compose -f docker-compose.prod.yml build backend

  # 4. Пересобрать bot
  docker-compose -f docker-compose.prod.yml build bot

  # 5. Перезапустить сервисы
  docker-compose -f docker-compose.prod.yml up -d

  # 6. Проверить логи
  docker-compose -f docker-compose.prod.yml logs -f backend bot
  ```

- [ ] **7.3. Post-deployment проверки:**
  - Проверить создание сравнения через бота
  - Проверить все API endpoints (через /docs)
  - Проверить работу Cron job (в логах через 24 часа)
  - Мониторинг ошибок первые 48 часов

- [ ] **7.4. Документация:**
  - Обновить README.md с информацией о новом функционале
  - Обновить API documentation
  - Добавить примеры использования

---

## 🎯 ПРИОРИТЕТЫ И ОЦЕНКИ

### Критически важно (MVP):

| Задача | Приоритет | Время | Зависимости |
|--------|-----------|-------|-------------|
| Миграция БД | P0 | 2ч | - |
| Backend models (comparison.py) | P0 | 3ч | Миграция |
| ComparisonService | P0 | 6ч | Models |
| API endpoints | P0 | 4ч | Service |
| Bot FSM flow (/compare) | P0 | 4ч | API |
| Форматирование в боте | P0 | 2ч | Bot flow |

**Итого MVP: ~21 час (3 дня)**

### Важно (Phase 2):

| Задача | Приоритет | Время | Зависимости |
|--------|-----------|-------|-------------|
| Список сравнений (/comparisons) | P1 | 2ч | MVP |
| Кнопка "Обновить" | P1 | 1ч | MVP |
| История сравнений | P1 | 3ч | Snapshots |
| Cron job snapshots | P1 | 4ч | Service |
| Тестирование | P1 | 6ч | Всё |

**Итого Phase 2: ~16 часов (2 дня)**

### Nice to have (Future):

- Графики изменений (Chart.js или matplotlib)
- Экспорт в CSV/PDF
- Сравнение 3+ артикулов одновременно
- Алерты "конкурент снизил цену!"
- Автоматические рекомендации по оптимальной цене
- Анализ трендов (ML predictions)

---

## ⚠️ ВАЖНЫЕ ЗАМЕЧАНИЯ

### Обратная совместимость:
- ✅ Существующие артикулы (без групп) продолжат работать
- ✅ Старый функционал `/add`, `/list` не затрагивается
- ✅ Новые таблицы независимы от старых

### Миграция данных:
- ❌ **НЕ требуется** - новые таблицы создаются пустыми
- ✅ Пользователи начнут создавать группы с нуля

### Производительность:
- Scraping 2 артикулов: **~10-15 секунд**
- Расчет метрик: **<1 секунды**
- Cron job для 100 групп: **~30 минут**

### Лимиты:
- **10 групп** на пользователя (предотвращение спама)
- **5 артикулов** в одной группе (для будущего расширения)
- Снэпшоты хранятся **90 дней** (автоматическая очистка)

### Безопасность:
- **RLS policies:** Пользователи видят только свои группы
- **Rate limiting:** Создание группы - 5 раз/минуту
- **Валидация:** Проверка ownership артикулов

### Monitoring:
- Логирование всех операций с группами
- Метрики: количество групп, частота обновлений
- Алерты при ошибках scraping

---

## 📊 ИТОГОВАЯ ОЦЕНКА

### Сроки:
- **MVP (минимальный функционал):** 3 дня
- **Full Feature (со всеми улучшениями):** 7 дней
- **Deployment & Testing:** +1 день

**Итого: 7-8 дней** полной разработки

### Файлы:

**Новые (5 файлов):**
- `backend/migrations/008_article_comparison.sql`
- `backend/models/comparison.py`
- `backend/services/comparison_service.py`
- `backend/routers/comparisons.py`
- `bot/handlers/comparisons.py`

**Изменения (6 файлов):**
- `backend/main.py` (регистрация router)
- `backend/services/scheduler.py` (cron job)
- `bot/main.py` (регистрация handler)
- `bot/services/api_client.py` (новые методы)
- `bot/utils/formatters.py` (format_comparison)
- `bot/keyboards.py` (новые клавиатуры)

### Результат:

Пользователь сможет:
- ✅ Добавить пару артикулов (свой + конкурент)
- ✅ Увидеть детальное сравнение по всем параметрам
- ✅ Получить **Индекс конкурентоспособности** и рекомендации
- ✅ Следить за историей изменений (через снэпшоты)
- ✅ Понимать свою позицию относительно конкурента
- ✅ Принимать решения о ценообразовании на основе данных

---

## 🚀 СЛЕДУЮЩИЕ ШАГИ

### Чтобы начать разработку:

1. **Создать feature branch:**
   ```bash
   git checkout -b feature/article-comparison
   ```

2. **Начать с Фазы 1 (миграция БД):**
   - Создать файл миграции
   - Применить в dev окружении
   - Проверить структуру таблиц

3. **Постепенно двигаться по фазам:**
   - Каждая фаза = отдельный commit
   - Тестировать после каждой фазы
   - Code review критичных частей

4. **Финальный merge:**
   - После полного тестирования
   - Деплой в production
   - Мониторинг первые 48 часов

---

## 📝 ЧЕКЛИСТ ГОТОВНОСТИ К ДЕПЛОЮ

- [ ] Все миграции применены и протестированы
- [ ] Unit тесты покрывают ключевой функционал (>80%)
- [ ] Integration тесты прошли успешно
- [ ] Manual тестирование на реальных артикулах OZON
- [ ] Документация обновлена (README, API docs)
- [ ] Code review пройден
- [ ] Нет критичных багов в трекере
- [ ] Backup БД перед применением миграции
- [ ] Rollback план готов (на случай проблем)
- [ ] Мониторинг настроен (логи, алерты)

---

## 🔗 СВЯЗАННЫЕ ДОКУМЕНТЫ

- [PRD.md](./PRD.md) - Product Requirements Document (обновить после имплементации)
- [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) - технические детали (добавить раздел о сравнении)
- [DEPLOY_CHECKLIST.md](./DEPLOY_CHECKLIST.md) - чеклист деплоя
- [API Documentation](http://backend:8000/docs) - Swagger docs (автоматически обновится)

---

## ❓ ВОПРОСЫ И РЕШЕНИЯ

### Q: Почему article_groups вместо competitor_article_number в articles?
**A:** Гибкость и масштабируемость. Можно будет сравнивать 3+ артикулов, создавать группы "варианты товара", "похожие товары" и т.д.

### Q: Нужно ли хранить снэпшоты или достаточно price_history?
**A:** Снэпшоты нужны, потому что они сохраняют **полное состояние сравнения** в момент времени, включая метрики, индекс, рекомендации. Price_history только для цен.

### Q: Как быть со старыми артикулами без групп?
**A:** Они продолжат работать как есть. Новая функция - опциональная. Можно добавить миграцию старых артикулов в будущем.

### Q: Что если scraping одного из артикулов не удался?
**A:** Показать частичное сравнение с пометкой "Данные не доступны" для проблемного артикула. Или попросить пользователя попробовать позже.

---

**Готов к имплементации!** 🚀

_Создано: 2025-10-29_
_Автор: Claude Code_
_Статус: Планирование завершено_
