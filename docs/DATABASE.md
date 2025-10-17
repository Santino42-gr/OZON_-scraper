# База данных OZON Bot MVP

## Обзор

Проект использует **PostgreSQL** через **Supabase** для хранения всех данных.

- **СУБД**: PostgreSQL 15+
- **Платформа**: Supabase
- **Расширения**: uuid-ossp

## Схема базы данных

### ER-диаграмма (текстовая)

```
┌─────────────┐         ┌──────────────┐         ┌──────────────────┐
│   users     │◄────────│   articles   │◄────────│ request_history  │
│             │         │              │         │                  │
│ id (PK)     │         │ id (PK)      │         │ id (PK)          │
│ telegram_id │         │ article_num  │         │ user_id (FK)     │
│ username    │         │ user_id (FK) │         │ article_id (FK)  │
│ created_at  │         │ status       │         │ requested_at     │
│ is_blocked  │         │ last_check   │         │ response_data    │
└─────────────┘         └──────────────┘         └──────────────────┘
       ▲                       ▲
       │                       │
       │                       │
       └───────┐       ┌───────┘
               │       │
           ┌───┴───────┴────┐
           │     logs       │
           │                │
           │ id (PK)        │
           │ level          │
           │ event_type     │
           │ message        │
           │ user_id (FK)   │
           │ article_id (FK)│
           │ metadata       │
           └────────────────┘

┌──────────────┐
│   admins     │
│              │
│ id (PK)      │
│ email        │
│ role         │
│ created_at   │
└──────────────┘
```

## Таблицы

### 1. `users` - Пользователи Telegram

Хранит информацию о пользователях Telegram-бота.

| Колонка | Тип | Описание |
|---------|-----|----------|
| `id` | UUID | Первичный ключ |
| `telegram_id` | BIGINT | ID пользователя в Telegram (уникальный) |
| `telegram_username` | TEXT | Username в Telegram (@username) |
| `created_at` | TIMESTAMPTZ | Дата регистрации |
| `is_blocked` | BOOLEAN | Флаг блокировки пользователя |
| `last_active_at` | TIMESTAMPTZ | Последняя активность |

**Индексы:**
- `idx_users_telegram_id` - на telegram_id
- `idx_users_created_at` - на created_at (DESC)
- `idx_users_is_blocked` - частичный на is_blocked

**Constraints:**
- `telegram_id` - UNIQUE, NOT NULL

---

### 2. `admins` - Администраторы панели

Хранит информацию об администраторах веб-панели.

| Колонка | Тип | Описание |
|---------|-----|----------|
| `id` | UUID | Первичный ключ |
| `email` | TEXT | Email администратора (для Supabase Auth) |
| `created_at` | TIMESTAMPTZ | Дата добавления |
| `role` | TEXT | Роль: admin, superadmin, viewer |

**Индексы:**
- `idx_admins_email` - на email

**Constraints:**
- `email` - UNIQUE, NOT NULL, валидация email
- `role` - CHECK (IN 'admin', 'superadmin', 'viewer')

---

### 3. `articles` - Артикулы OZON

Хранит артикулы товаров OZON, отслеживаемые пользователями.

| Колонка | Тип | Описание |
|---------|-----|----------|
| `id` | UUID | Первичный ключ |
| `article_number` | TEXT | Номер артикула OZON |
| `user_id` | UUID | FK на users.id |
| `created_at` | TIMESTAMPTZ | Дата добавления |
| `updated_at` | TIMESTAMPTZ | Последнее обновление |
| `status` | TEXT | Статус: active, inactive, error |
| `last_check_data` | JSONB | Последние полученные данные |
| `is_problematic` | BOOLEAN | Флаг проблемного артикула |

**Индексы:**
- `idx_articles_user_id` - на user_id
- `idx_articles_article_number` - на article_number
- `idx_articles_created_at` - на created_at (DESC)
- `idx_articles_status` - на status
- `idx_articles_is_problematic` - частичный на is_problematic
- `idx_articles_last_check_data` - GIN на last_check_data

**Constraints:**
- `user_id` - FK REFERENCES users(id) ON DELETE CASCADE
- `status` - CHECK (IN 'active', 'inactive', 'error')
- `unique_user_article` - UNIQUE (user_id, article_number)

**Triggers:**
- `update_articles_updated_at` - автообновление updated_at

---

### 4. `request_history` - История запросов

Хранит историю всех запросов к OZON API.

| Колонка | Тип | Описание |
|---------|-----|----------|
| `id` | UUID | Первичный ключ |
| `user_id` | UUID | FK на users.id |
| `article_id` | UUID | FK на articles.id (nullable) |
| `requested_at` | TIMESTAMPTZ | Время запроса |
| `response_data` | JSONB | Данные ответа от OZON |
| `error` | TEXT | Текст ошибки (если была) |
| `execution_time_ms` | INTEGER | Время выполнения в миллисекундах |
| `success` | BOOLEAN | Успешность запроса |

**Индексы:**
- `idx_request_history_user_id` - на user_id
- `idx_request_history_article_id` - на article_id
- `idx_request_history_requested_at` - на requested_at (DESC)
- `idx_request_history_success` - на success
- `idx_request_history_response_data` - GIN на response_data

**Constraints:**
- `user_id` - FK REFERENCES users(id) ON DELETE CASCADE
- `article_id` - FK REFERENCES articles(id) ON DELETE SET NULL

**Triggers:**
- `update_user_activity_on_request` - обновление last_active_at у user

---

### 5. `logs` - Системные логи

Хранит все логи системы для мониторинга и отладки.

| Колонка | Тип | Описание |
|---------|-----|----------|
| `id` | UUID | Первичный ключ |
| `timestamp` | TIMESTAMPTZ | Время события |
| `level` | TEXT | Уровень: DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `event_type` | TEXT | Тип события |
| `message` | TEXT | Сообщение лога |
| `user_id` | UUID | FK на users.id (nullable) |
| `article_id` | UUID | FK на articles.id (nullable) |
| `metadata` | JSONB | Дополнительные данные |

**Индексы:**
- `idx_logs_timestamp` - на timestamp (DESC)
- `idx_logs_level` - на level
- `idx_logs_event_type` - на event_type
- `idx_logs_user_id` - на user_id
- `idx_logs_metadata` - GIN на metadata

**Constraints:**
- `level` - CHECK (IN 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
- `user_id` - FK REFERENCES users(id) ON DELETE SET NULL
- `article_id` - FK REFERENCES articles(id) ON DELETE SET NULL

---

## Row Level Security (RLS)

Все таблицы защищены RLS политиками:

### Политики безопасности

**users:**
- Пользователи видят только свою запись
- Service role видит всех

**admins:**
- Админы видят всех админов
- Только superadmin может создавать новых админов
- Service role имеет полный доступ

**articles:**
- Пользователи видят только свои артикулы
- Админы видят все артикулы
- Service role имеет полный доступ

**request_history:**
- Пользователи видят только свою историю
- Админы видят всю историю
- Service role имеет полный доступ

**logs:**
- Только админы могут читать логи
- Service role имеет полный доступ

## Триггеры и функции

### Триггеры

1. **update_articles_updated_at**
   - Автоматически обновляет `updated_at` при изменении артикула

2. **update_user_activity_on_request**
   - Обновляет `last_active_at` у пользователя при каждом запросе

### Вспомогательные функции

1. **is_admin()** - проверяет, является ли текущий пользователь админом
2. **is_superadmin()** - проверяет, является ли текущий пользователь superadmin

## Миграции

Миграции выполняются в следующем порядке:

1. `001_initial_schema.sql` - создание таблиц и индексов
2. `002_rls_policies.sql` - настройка RLS политик
3. `003_seed_data.sql` - тестовые данные (только для development)

## Производительность

### Оптимизации

- **Индексы**: созданы индексы на все часто используемые колонки
- **GIN индексы**: для JSONB колонок (fast search)
- **Частичные индексы**: для булевых флагов
- **Каскадное удаление**: для связанных записей
- **Автоматические триггеры**: для обновления timestamps

### Рекомендации

- Используйте `last_check_data` JSONB для гибкого хранения данных
- Регулярно очищайте старые логи (>30 дней)
- Используйте партиционирование для `logs` при больших объемах
- Мониторьте размер таблиц через Supabase Dashboard

## Backup и восстановление

Supabase автоматически создает:
- Daily backups (ежедневные)
- Point-in-time recovery (восстановление на момент времени)

Для ручного backup используйте:
```bash
pg_dump -h db.[project-ref].supabase.co -U postgres -d postgres > backup.sql
```

## Мониторинг

Важные метрики для отслеживания:
- Размер таблиц
- Количество записей в `logs` (чистить старые)
- Производительность индексов
- Количество активных подключений
- Размер БД (Supabase Free tier: 500 MB)

Проверка размера таблиц:
```sql
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

