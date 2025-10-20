-- =====================================================
-- OZON Bot MVP - Add Test Admin
-- Migration: 005
-- Description: Добавление тестового администратора
-- Created: 2025-10-20
-- =====================================================

-- ⚠️ ВАЖНО: Перед выполнением этой миграции
-- создайте пользователя в Supabase Auth Dashboard:
-- Email: admin@ozonbot.dev
-- Password: admin123456 (или любой пароль минимум 6 символов)
-- Auto Confirm User: ✅

-- =====================================================
-- Добавление тестового админа
-- =====================================================

INSERT INTO ozon_scraper_admins (email, role)
VALUES ('admin@ozonbot.dev', 'superadmin')
ON CONFLICT (email) DO NOTHING;

-- =====================================================
-- Проверка
-- =====================================================

-- Посмотреть всех админов
SELECT id, email, role, created_at
FROM ozon_scraper_admins
ORDER BY created_at DESC;

