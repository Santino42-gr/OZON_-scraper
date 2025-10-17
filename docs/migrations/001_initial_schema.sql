-- =====================================================
-- OZON Bot MVP - Initial Database Schema
-- Migration: 001
-- Description: Создание всех таблиц и базовых индексов
-- =====================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- 1. Users Table (Telegram пользователи)
-- =====================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    telegram_id BIGINT UNIQUE NOT NULL,
    telegram_username TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_blocked BOOLEAN DEFAULT FALSE,
    last_active_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Индексы для users
CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_users_created_at ON users(created_at DESC);
CREATE INDEX idx_users_is_blocked ON users(is_blocked) WHERE is_blocked = TRUE;

-- =====================================================
-- 2. Admins Table (Администраторы панели)
-- =====================================================
CREATE TABLE IF NOT EXISTS admins (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    role TEXT NOT NULL DEFAULT 'admin',
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT valid_role CHECK (role IN ('admin', 'superadmin', 'viewer'))
);

-- Индексы для admins
CREATE INDEX idx_admins_email ON admins(email);

-- =====================================================
-- 3. Articles Table (Артикулы OZON)
-- =====================================================
CREATE TABLE IF NOT EXISTS articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    article_number TEXT NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status TEXT DEFAULT 'active',
    last_check_data JSONB,
    is_problematic BOOLEAN DEFAULT FALSE,
    CONSTRAINT valid_status CHECK (status IN ('active', 'inactive', 'error')),
    CONSTRAINT unique_user_article UNIQUE (user_id, article_number)
);

-- Индексы для articles
CREATE INDEX idx_articles_user_id ON articles(user_id);
CREATE INDEX idx_articles_article_number ON articles(article_number);
CREATE INDEX idx_articles_created_at ON articles(created_at DESC);
CREATE INDEX idx_articles_status ON articles(status);
CREATE INDEX idx_articles_is_problematic ON articles(is_problematic) WHERE is_problematic = TRUE;
CREATE INDEX idx_articles_last_check_data ON articles USING GIN(last_check_data);

-- =====================================================
-- 4. Request History Table (История запросов)
-- =====================================================
CREATE TABLE IF NOT EXISTS request_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    article_id UUID REFERENCES articles(id) ON DELETE SET NULL,
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    response_data JSONB,
    error TEXT,
    execution_time_ms INTEGER,
    success BOOLEAN DEFAULT TRUE
);

-- Индексы для request_history
CREATE INDEX idx_request_history_user_id ON request_history(user_id);
CREATE INDEX idx_request_history_article_id ON request_history(article_id);
CREATE INDEX idx_request_history_requested_at ON request_history(requested_at DESC);
CREATE INDEX idx_request_history_success ON request_history(success);
CREATE INDEX idx_request_history_response_data ON request_history USING GIN(response_data);

-- =====================================================
-- 5. Logs Table (Системные логи)
-- =====================================================
CREATE TABLE IF NOT EXISTS logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    level TEXT NOT NULL DEFAULT 'INFO',
    event_type TEXT NOT NULL,
    message TEXT NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    article_id UUID REFERENCES articles(id) ON DELETE SET NULL,
    metadata JSONB,
    CONSTRAINT valid_level CHECK (level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'))
);

-- Индексы для logs
CREATE INDEX idx_logs_timestamp ON logs(timestamp DESC);
CREATE INDEX idx_logs_level ON logs(level);
CREATE INDEX idx_logs_event_type ON logs(event_type);
CREATE INDEX idx_logs_user_id ON logs(user_id);
CREATE INDEX idx_logs_metadata ON logs USING GIN(metadata);

-- Партиционирование логов по времени (опционально, для больших объемов)
-- CREATE INDEX idx_logs_timestamp_brin ON logs USING BRIN(timestamp);

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

CREATE TRIGGER update_articles_updated_at
    BEFORE UPDATE ON articles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- Триггер для обновления last_active_at у users
-- =====================================================
CREATE OR REPLACE FUNCTION update_user_last_active()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE users 
    SET last_active_at = NOW() 
    WHERE id = NEW.user_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_user_activity_on_request
    AFTER INSERT ON request_history
    FOR EACH ROW
    EXECUTE FUNCTION update_user_last_active();

-- =====================================================
-- Комментарии к таблицам (документация)
-- =====================================================
COMMENT ON TABLE users IS 'Пользователи Telegram бота';
COMMENT ON TABLE admins IS 'Администраторы веб-панели';
COMMENT ON TABLE articles IS 'Артикулы OZON отслеживаемые пользователями';
COMMENT ON TABLE request_history IS 'История запросов к OZON API';
COMMENT ON TABLE logs IS 'Системные логи приложения';

-- =====================================================
-- Завершение миграции
-- =====================================================
DO $$
BEGIN
    RAISE NOTICE 'Migration 001_initial_schema.sql completed successfully!';
    RAISE NOTICE 'Tables created: users, admins, articles, request_history, logs';
    RAISE NOTICE 'Next step: Run 002_rls_policies.sql to enable Row Level Security';
END $$;

