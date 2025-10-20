-- =====================================================
-- OZON Bot MVP - Row Level Security Policies (UPDATED)
-- Migration: 002
-- Description: Настройка RLS политик для таблиц с префиксом ozon_scraper_
-- Updated: 2025-10-20
-- =====================================================

-- =====================================================
-- Включение RLS для всех таблиц
-- =====================================================
ALTER TABLE ozon_scraper_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE ozon_scraper_admins ENABLE ROW LEVEL SECURITY;
ALTER TABLE ozon_scraper_articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE ozon_scraper_request_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE ozon_scraper_logs ENABLE ROW LEVEL SECURITY;

-- =====================================================
-- RLS Политики для Users
-- =====================================================

-- Пользователи могут видеть только свою запись
CREATE POLICY "Users can view own record"
    ON ozon_scraper_users FOR SELECT
    USING (telegram_id = current_setting('app.telegram_id', true)::BIGINT);

-- Service role может видеть всех пользователей
CREATE POLICY "Service role can view all users"
    ON ozon_scraper_users FOR SELECT
    TO service_role
    USING (true);

-- Service role может создавать пользователей
CREATE POLICY "Service role can insert users"
    ON ozon_scraper_users FOR INSERT
    TO service_role
    WITH CHECK (true);

-- Service role может обновлять пользователей
CREATE POLICY "Service role can update users"
    ON ozon_scraper_users FOR UPDATE
    TO service_role
    USING (true);

-- =====================================================
-- RLS Политики для Admins
-- =====================================================

-- Только аутентифицированные админы могут видеть записи
CREATE POLICY "Admins can view all admins"
    ON ozon_scraper_admins FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM ozon_scraper_admins 
            WHERE email = auth.jwt() ->> 'email'
        )
    );

-- Только superadmin может создавать новых админов
CREATE POLICY "Superadmins can create admins"
    ON ozon_scraper_admins FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM ozon_scraper_admins 
            WHERE email = auth.jwt() ->> 'email' 
            AND role = 'superadmin'
        )
    );

-- Service role имеет полный доступ
CREATE POLICY "Service role full access to admins"
    ON ozon_scraper_admins FOR ALL
    TO service_role
    USING (true);

-- =====================================================
-- RLS Политики для Articles
-- =====================================================

-- Пользователи могут видеть только свои артикулы
CREATE POLICY "Users can view own articles"
    ON ozon_scraper_articles FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM ozon_scraper_users 
            WHERE ozon_scraper_users.id = ozon_scraper_articles.user_id 
            AND ozon_scraper_users.telegram_id = current_setting('app.telegram_id', true)::BIGINT
        )
    );

-- Service role может видеть все артикулы
CREATE POLICY "Service role can view all articles"
    ON ozon_scraper_articles FOR SELECT
    TO service_role
    USING (true);

-- Service role может создавать артикулы
CREATE POLICY "Service role can insert articles"
    ON ozon_scraper_articles FOR INSERT
    TO service_role
    WITH CHECK (true);

-- Service role может обновлять артикулы
CREATE POLICY "Service role can update articles"
    ON ozon_scraper_articles FOR UPDATE
    TO service_role
    USING (true);

-- Service role может удалять артикулы
CREATE POLICY "Service role can delete articles"
    ON ozon_scraper_articles FOR DELETE
    TO service_role
    USING (true);

-- Админы могут видеть все артикулы
CREATE POLICY "Admins can view all articles"
    ON ozon_scraper_articles FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM ozon_scraper_admins 
            WHERE email = auth.jwt() ->> 'email'
        )
    );

-- =====================================================
-- RLS Политики для Request History
-- =====================================================

-- Пользователи могут видеть только свою историю
CREATE POLICY "Users can view own history"
    ON ozon_scraper_request_history FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM ozon_scraper_users 
            WHERE ozon_scraper_users.id = ozon_scraper_request_history.user_id 
            AND ozon_scraper_users.telegram_id = current_setting('app.telegram_id', true)::BIGINT
        )
    );

-- Service role имеет полный доступ
CREATE POLICY "Service role full access to history"
    ON ozon_scraper_request_history FOR ALL
    TO service_role
    USING (true);

-- Админы могут видеть всю историю
CREATE POLICY "Admins can view all history"
    ON ozon_scraper_request_history FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM ozon_scraper_admins 
            WHERE email = auth.jwt() ->> 'email'
        )
    );

-- =====================================================
-- RLS Политики для Logs
-- =====================================================

-- Service role имеет полный доступ к логам
CREATE POLICY "Service role full access to logs"
    ON ozon_scraper_logs FOR ALL
    TO service_role
    USING (true);

-- Админы могут читать все логи
CREATE POLICY "Admins can view all logs"
    ON ozon_scraper_logs FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM ozon_scraper_admins 
            WHERE email = auth.jwt() ->> 'email'
        )
    );

-- Админы могут создавать логи
CREATE POLICY "Admins can insert logs"
    ON ozon_scraper_logs FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM ozon_scraper_admins 
            WHERE email = auth.jwt() ->> 'email'
        )
    );

-- =====================================================
-- Вспомогательные функции для RLS
-- =====================================================

-- Функция для проверки, является ли пользователь админом
CREATE OR REPLACE FUNCTION is_admin()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM ozon_scraper_admins 
        WHERE email = auth.jwt() ->> 'email'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Функция для проверки, является ли пользователь superadmin
CREATE OR REPLACE FUNCTION is_superadmin()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM ozon_scraper_admins 
        WHERE email = auth.jwt() ->> 'email' 
        AND role = 'superadmin'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- Grant необходимых прав
-- =====================================================

-- Разрешаем anon и authenticated читать из tables (через RLS)
GRANT SELECT ON ozon_scraper_users TO anon, authenticated;
GRANT SELECT ON ozon_scraper_articles TO anon, authenticated;
GRANT SELECT ON ozon_scraper_request_history TO anon, authenticated;
GRANT SELECT ON ozon_scraper_admins TO authenticated;
GRANT SELECT ON ozon_scraper_logs TO authenticated;

-- Service role получает полный доступ
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;

-- =====================================================
-- Завершение миграции
-- =====================================================
DO $$
BEGIN
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Migration 002_rls_policies.sql (UPDATED) completed successfully!';
    RAISE NOTICE 'RLS enabled for all ozon_scraper_* tables';
    RAISE NOTICE 'Security policies configured';
    RAISE NOTICE 'System is now secure and ready for production';
    RAISE NOTICE '============================================';
END $$;

