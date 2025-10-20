-- =====================================================
-- OZON Bot MVP - Initial Database Schema (UPDATED)
-- Migration: 001
-- Description: Создание всех таблиц с префиксом ozon_scraper_
-- Updated: 2025-10-20 (добавлен префикс для всех таблиц)
-- =====================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- 1. Users Table (Telegram пользователи)
-- =====================================================
CREATE TABLE IF NOT EXISTS ozon_scraper_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    telegram_id BIGINT UNIQUE NOT NULL,
    telegram_username TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_blocked BOOLEAN DEFAULT FALSE,
    last_active_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Индексы для ozon_scraper_users
CREATE INDEX idx_ozon_scraper_users_telegram_id ON ozon_scraper_users(telegram_id);
CREATE INDEX idx_ozon_scraper_users_created_at ON ozon_scraper_users(created_at DESC);
CREATE INDEX idx_ozon_scraper_users_is_blocked ON ozon_scraper_users(is_blocked) WHERE is_blocked = TRUE;

-- =====================================================
-- 2. Admins Table (Администраторы панели)
-- =====================================================
CREATE TABLE IF NOT EXISTS ozon_scraper_admins (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    role TEXT NOT NULL DEFAULT 'admin',
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT valid_role CHECK (role IN ('admin', 'superadmin', 'viewer'))
);

-- Индексы для ozon_scraper_admins
CREATE INDEX idx_ozon_scraper_admins_email ON ozon_scraper_admins(email);

-- =====================================================
-- 3. Articles Table (Артикулы OZON)
-- =====================================================
CREATE TABLE IF NOT EXISTS ozon_scraper_articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    article_number TEXT NOT NULL,
    user_id UUID NOT NULL REFERENCES ozon_scraper_users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status TEXT DEFAULT 'active',
    last_check_data JSONB,
    is_problematic BOOLEAN DEFAULT FALSE,
    CONSTRAINT valid_status CHECK (status IN ('active', 'inactive', 'error')),
    CONSTRAINT unique_user_article UNIQUE (user_id, article_number)
);

-- Индексы для ozon_scraper_articles
CREATE INDEX idx_ozon_scraper_articles_user_id ON ozon_scraper_articles(user_id);
CREATE INDEX idx_ozon_scraper_articles_article_number ON ozon_scraper_articles(article_number);
CREATE INDEX idx_ozon_scraper_articles_created_at ON ozon_scraper_articles(created_at DESC);
CREATE INDEX idx_ozon_scraper_articles_status ON ozon_scraper_articles(status);
CREATE INDEX idx_ozon_scraper_articles_is_problematic ON ozon_scraper_articles(is_problematic) WHERE is_problematic = TRUE;
CREATE INDEX idx_ozon_scraper_articles_last_check_data ON ozon_scraper_articles USING GIN(last_check_data);

-- =====================================================
-- 4. Request History Table (История запросов)
-- =====================================================
CREATE TABLE IF NOT EXISTS ozon_scraper_request_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES ozon_scraper_users(id) ON DELETE CASCADE,
    article_id UUID REFERENCES ozon_scraper_articles(id) ON DELETE SET NULL,
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    response_data JSONB,
    error TEXT,
    execution_time_ms INTEGER,
    success BOOLEAN DEFAULT TRUE
);

-- Индексы для ozon_scraper_request_history
CREATE INDEX idx_ozon_scraper_request_history_user_id ON ozon_scraper_request_history(user_id);
CREATE INDEX idx_ozon_scraper_request_history_article_id ON ozon_scraper_request_history(article_id);
CREATE INDEX idx_ozon_scraper_request_history_requested_at ON ozon_scraper_request_history(requested_at DESC);
CREATE INDEX idx_ozon_scraper_request_history_success ON ozon_scraper_request_history(success);
CREATE INDEX idx_ozon_scraper_request_history_response_data ON ozon_scraper_request_history USING GIN(response_data);

-- =====================================================
-- 5. Logs Table (Системные логи)
-- =====================================================
CREATE TABLE IF NOT EXISTS ozon_scraper_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    level TEXT NOT NULL DEFAULT 'INFO',
    event_type TEXT NOT NULL,
    message TEXT NOT NULL,
    user_id UUID REFERENCES ozon_scraper_users(id) ON DELETE SET NULL,
    article_id UUID REFERENCES ozon_scraper_articles(id) ON DELETE SET NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT valid_level CHECK (level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'info', 'error'))
);

-- Индексы для ozon_scraper_logs
CREATE INDEX idx_ozon_scraper_logs_timestamp ON ozon_scraper_logs(timestamp DESC);
CREATE INDEX idx_ozon_scraper_logs_level ON ozon_scraper_logs(level);
CREATE INDEX idx_ozon_scraper_logs_event_type ON ozon_scraper_logs(event_type);
CREATE INDEX idx_ozon_scraper_logs_user_id ON ozon_scraper_logs(user_id);
CREATE INDEX idx_ozon_scraper_logs_metadata ON ozon_scraper_logs USING GIN(metadata);

-- =====================================================
-- Triggers для автообновления updated_at
-- =====================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_ozon_scraper_articles_updated_at
    BEFORE UPDATE ON ozon_scraper_articles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- Триггер для обновления last_active_at у users
-- =====================================================
CREATE OR REPLACE FUNCTION update_user_last_active()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE ozon_scraper_users 
    SET last_active_at = NOW() 
    WHERE id = NEW.user_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_user_activity_on_request
    AFTER INSERT ON ozon_scraper_request_history
    FOR EACH ROW
    EXECUTE FUNCTION update_user_last_active();

-- =====================================================
-- Комментарии к таблицам (документация)
-- =====================================================
COMMENT ON TABLE ozon_scraper_users IS 'Пользователи Telegram бота OZON Scraper';
COMMENT ON TABLE ozon_scraper_admins IS 'Администраторы веб-панели OZON Scraper';
COMMENT ON TABLE ozon_scraper_articles IS 'Артикулы OZON отслеживаемые пользователями';
COMMENT ON TABLE ozon_scraper_request_history IS 'История запросов к OZON (scraping)';
COMMENT ON TABLE ozon_scraper_logs IS 'Системные логи приложения OZON Scraper';

-- =====================================================
-- Завершение миграции
-- =====================================================
DO $$
BEGIN
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Migration 001_initial_schema.sql (UPDATED) completed successfully!';
    RAISE NOTICE 'Tables created with prefix "ozon_scraper_":';
    RAISE NOTICE '  - ozon_scraper_users';
    RAISE NOTICE '  - ozon_scraper_admins';
    RAISE NOTICE '  - ozon_scraper_articles';
    RAISE NOTICE '  - ozon_scraper_request_history';
    RAISE NOTICE '  - ozon_scraper_logs';
    RAISE NOTICE 'Next step: Run 002_rls_policies.sql';
    RAISE NOTICE '============================================';
END $$;

