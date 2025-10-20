# Настройка аутентификации - OZON Bot Admin

## Обзор системы аутентификации

Система использует **Supabase Auth** для аутентификации администраторов панели. Таблица `ozon_scraper_admins` хранит информацию о ролях и правах доступа.

## Создание тестового админа

### Шаг 1: Создание пользователя в Supabase Auth

1. Откройте [Supabase Dashboard](https://supabase.com/dashboard/project/kknxajmrtexzzlqgvlxg)
2. Перейдите в раздел **Authentication** → **Users**
3. Нажмите кнопку **Add user** → **Create new user**
4. Заполните форму:
   - **Email**: `admin@ozonbot.dev`
   - **Password**: `admin123456` (или любой пароль минимум 6 символов)
   - **Auto Confirm User**: ✅ (включить)
5. Нажмите **Create user**

### Шаг 2: Добавление админа в таблицу

После создания пользователя в Auth, добавьте его в таблицу `ozon_scraper_admins`:

```sql
-- Добавить тестового админа
INSERT INTO ozon_scraper_admins (email, role)
VALUES ('admin@ozonbot.dev', 'superadmin')
ON CONFLICT (email) DO NOTHING;
```

Выполните этот SQL в **SQL Editor** в Supabase Dashboard.

## Тестовые учетные данные

После выполнения шагов выше, используйте для входа:

- **Email**: `admin@ozonbot.dev`
- **Password**: `admin123456`

## Роли администраторов

В системе доступны три роли:

- **superadmin** - полный доступ ко всем функциям
- **admin** - стандартные административные права
- **viewer** - только просмотр (без редактирования)

## Добавление новых администраторов

### Через Supabase Dashboard

1. Создайте пользователя в **Authentication** → **Users**
2. Добавьте email в таблицу `ozon_scraper_admins`:

```sql
INSERT INTO ozon_scraper_admins (email, role)
VALUES ('newemail@example.com', 'admin');
```

### Через SQL (будущая функциональность)

В будущем можно создать функцию для автоматизации:

```sql
CREATE OR REPLACE FUNCTION create_admin(
  admin_email TEXT,
  admin_role TEXT DEFAULT 'admin'
)
RETURNS UUID AS $$
DECLARE
  new_admin_id UUID;
BEGIN
  -- Добавить в таблицу admins
  INSERT INTO ozon_scraper_admins (email, role)
  VALUES (admin_email, admin_role)
  RETURNING id INTO new_admin_id;
  
  RETURN new_admin_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

## Проверка настроек

### 1. Проверка RLS политик

```sql
-- Проверить политики для admins
SELECT * FROM pg_policies WHERE tablename = 'ozon_scraper_admins';
```

### 2. Проверка списка админов

```sql
-- Посмотреть всех админов (только для superadmin)
SELECT id, email, role, created_at
FROM ozon_scraper_admins
ORDER BY created_at DESC;
```

## Сброс пароля

Пользователи могут сбросить пароль через страницу `/reset-password` в админ-панели. Supabase отправит email с инструкциями.

## Безопасность

✅ **Что реализовано:**
- Аутентификация через Supabase Auth
- Хэширование паролей (Supabase)
- Автоматическое обновление токенов
- RLS политики для таблицы admins
- Проверка email формата

⚠️ **Важно:**
- Не используйте слабые пароли в production
- Регулярно обновляйте права доступа
- Мониторьте логи входа в систему

## Troubleshooting

### Ошибка "Invalid login credentials"

- Проверьте правильность email и пароля
- Убедитесь, что пользователь создан в Supabase Auth
- Проверьте, что email добавлен в таблицу `ozon_scraper_admins`

### Пользователь создан, но не может войти

```sql
-- Проверить наличие админа в таблице
SELECT * FROM ozon_scraper_admins WHERE email = 'admin@example.com';

-- Если записи нет, добавить
INSERT INTO ozon_scraper_admins (email, role)
VALUES ('admin@example.com', 'admin');
```

### Email не отправляется при сбросе пароля

1. Проверьте настройки SMTP в Supabase Dashboard
2. Перейдите в **Authentication** → **Email Templates**
3. Настройте **Reset Password** template

---

**Дата создания:** 2025-10-20  
**Статус:** ✅ Готово к использованию

