# Настройка Supabase для проекта OZON Bot

## Шаг 1: Создание проекта

1. Перейдите на [supabase.com](https://supabase.com)
2. Войдите или зарегистрируйтесь
3. Нажмите "New Project"
4. Заполните форму:
   - **Name**: `ozon-bot-mvp`
   - **Database Password**: создайте надежный пароль (сохраните его!)
   - **Region**: выберите ближайший регион (Europe West или Europe Central)
   - **Pricing Plan**: Free tier для начала

5. Нажмите "Create new project" и дождитесь завершения (~2 минуты)

## Шаг 2: Получение credentials

После создания проекта, перейдите в **Settings → API**:

### URL проекта
```
https://[your-project-ref].supabase.co
```

### API Keys
- **anon (public)**: для клиентских запросов
- **service_role (secret)**: для серверных операций (НЕ ПУБЛИКУЙТЕ!)

### Database Connection String
```
postgresql://postgres:[YOUR-PASSWORD]@db.[your-project-ref].supabase.co:5432/postgres
```

## Шаг 3: Выполнение миграции

1. В Supabase Dashboard перейдите в **SQL Editor**
2. Создайте новый запрос
3. Скопируйте содержимое файла `docs/migrations/001_initial_schema.sql`
4. Вставьте в редактор и нажмите **Run**
5. Проверьте, что все таблицы созданы в **Table Editor**

## Шаг 4: Настройка Auth

1. Перейдите в **Authentication → Providers**
2. Email provider должен быть включен по умолчанию
3. Настройте Email Templates (опционально)
4. В **Authentication → Policies** убедитесь, что RLS политики активны

## Шаг 5: Создание первого админа

В **SQL Editor** выполните:

```sql
-- Создайте первого администратора
INSERT INTO admins (email, role)
VALUES ('your-email@example.com', 'superadmin');
```

Затем зарегистрируйтесь через Supabase Auth с этим email.

## Шаг 6: Сохранение credentials

Создайте файл `.env` в корне проекта (НЕ коммитьте его!):

```env
# Supabase Configuration
SUPABASE_URL=https://[your-project-ref].supabase.co
SUPABASE_ANON_KEY=[your-anon-key]
SUPABASE_SERVICE_ROLE_KEY=[your-service-role-key]
DATABASE_URL=postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
```

## Проверка установки

После выполнения всех шагов, проверьте:

- ✅ Все 5 таблиц созданы (users, articles, request_history, logs, admins)
- ✅ RLS политики включены для всех таблиц
- ✅ Можете подключиться к БД
- ✅ Credentials сохранены в `.env`

## Следующие шаги

После завершения настройки Supabase:
1. Переходите к задаче **AIL-282**: Создание структуры монорепозитория
2. Backend сможет подключиться к БД используя credentials из `.env`

