-- =====================================================
-- OZON Bot MVP - Seed Data (Test Data)
-- Migration: 003
-- Description: Тестовые данные для разработки
-- =====================================================

-- ВНИМАНИЕ: Этот скрипт только для development окружения!
-- НЕ запускайте на production!

-- =====================================================
-- 1. Создание тестовых админов
-- =====================================================

-- Примечание: После выполнения этого скрипта, зарегистрируйтесь
-- в Supabase Auth с этими email адресами

INSERT INTO admins (email, role) VALUES
    ('admin@example.com', 'superadmin'),
    ('viewer@example.com', 'viewer')
ON CONFLICT (email) DO NOTHING;

-- =====================================================
-- 2. Создание тестовых пользователей Telegram
-- =====================================================

INSERT INTO users (telegram_id, telegram_username, is_blocked) VALUES
    (123456789, 'test_user_1', false),
    (987654321, 'test_user_2', false),
    (111222333, 'test_user_3', false),
    (444555666, 'blocked_user', true)
ON CONFLICT (telegram_id) DO NOTHING;

-- =====================================================
-- 3. Создание тестовых артикулов
-- =====================================================

-- Получаем ID тестовых пользователей
DO $$
DECLARE
    user1_id UUID;
    user2_id UUID;
    article1_id UUID;
    article2_id UUID;
BEGIN
    -- Получаем ID пользователей
    SELECT id INTO user1_id FROM users WHERE telegram_id = 123456789;
    SELECT id INTO user2_id FROM users WHERE telegram_id = 987654321;
    
    -- Создаем артикулы для user1
    INSERT INTO articles (article_number, user_id, status, last_check_data, is_problematic)
    VALUES 
        ('1234567890', user1_id, 'active', '{"price": 1990, "stock": 10, "rating": 4.5}'::jsonb, false),
        ('0987654321', user1_id, 'active', '{"price": 2500, "stock": 5, "rating": 4.8}'::jsonb, false),
        ('1111111111', user1_id, 'error', NULL, true)
    ON CONFLICT (user_id, article_number) DO NOTHING
    RETURNING id INTO article1_id;
    
    -- Создаем артикулы для user2
    INSERT INTO articles (article_number, user_id, status, last_check_data)
    VALUES 
        ('2222222222', user2_id, 'active', '{"price": 3500, "stock": 20, "rating": 4.2}'::jsonb),
        ('3333333333', user2_id, 'active', '{"price": 899, "stock": 0, "rating": 3.9}'::jsonb)
    ON CONFLICT (user_id, article_number) DO NOTHING;
    
    -- =====================================================
    -- 4. Создание истории запросов
    -- =====================================================
    
    -- История для user1
    INSERT INTO request_history (user_id, article_id, response_data, error, execution_time_ms, success)
    SELECT 
        user1_id,
        id,
        last_check_data,
        NULL,
        FLOOR(RANDOM() * 1000 + 100)::INTEGER,
        true
    FROM articles 
    WHERE user_id = user1_id AND status = 'active'
    LIMIT 5;
    
    -- Добавляем несколько ошибочных запросов
    INSERT INTO request_history (user_id, article_id, response_data, error, execution_time_ms, success)
    VALUES 
        (user1_id, NULL, NULL, 'OZON API timeout', 10000, false),
        (user1_id, NULL, NULL, 'Article not found', 500, false);
    
    -- =====================================================
    -- 5. Создание тестовых логов
    -- =====================================================
    
    INSERT INTO logs (level, event_type, message, user_id, article_id, metadata)
    VALUES 
        ('INFO', 'user_registered', 'New user registered from Telegram', user1_id, NULL, '{"telegram_username": "test_user_1"}'::jsonb),
        ('INFO', 'article_added', 'User added new article', user1_id, article1_id, '{"article_number": "1234567890"}'::jsonb),
        ('WARNING', 'rate_limit_exceeded', 'Rate limit exceeded for OZON API', NULL, NULL, '{"attempts": 35, "limit": 30}'::jsonb),
        ('ERROR', 'ozon_api_error', 'Failed to fetch product data', user1_id, NULL, '{"error": "timeout", "article": "1111111111"}'::jsonb),
        ('INFO', 'report_generated', 'User generated report', user1_id, NULL, '{"articles_count": 3, "format": "text"}'::jsonb),
        ('CRITICAL', 'database_connection_lost', 'Lost connection to database', NULL, NULL, '{"retry_attempts": 3}'::jsonb);
    
    RAISE NOTICE 'Test data inserted successfully!';
    RAISE NOTICE 'Users: %, %', user1_id, user2_id;
    RAISE NOTICE 'Remember to register these users in Supabase Auth:';
    RAISE NOTICE '  - admin@example.com (superadmin)';
    RAISE NOTICE '  - viewer@example.com (viewer)';
END $$;

-- =====================================================
-- Статистика по созданным данным
-- =====================================================

DO $$
DECLARE
    users_count INTEGER;
    admins_count INTEGER;
    articles_count INTEGER;
    history_count INTEGER;
    logs_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO users_count FROM users;
    SELECT COUNT(*) INTO admins_count FROM admins;
    SELECT COUNT(*) INTO articles_count FROM articles;
    SELECT COUNT(*) INTO history_count FROM request_history;
    SELECT COUNT(*) INTO logs_count FROM logs;
    
    RAISE NOTICE '===========================================';
    RAISE NOTICE 'Database Statistics:';
    RAISE NOTICE '===========================================';
    RAISE NOTICE 'Users:           %', users_count;
    RAISE NOTICE 'Admins:          %', admins_count;
    RAISE NOTICE 'Articles:        %', articles_count;
    RAISE NOTICE 'Request History: %', history_count;
    RAISE NOTICE 'Logs:            %', logs_count;
    RAISE NOTICE '===========================================';
END $$;

