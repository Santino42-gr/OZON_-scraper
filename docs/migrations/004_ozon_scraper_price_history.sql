-- =====================================================
-- Migration 004: OZON Scraper - Price History Table
-- =====================================================
-- Description: Таблица для хранения истории цен товаров OZON
--              Собирается автоматически через Cron Job каждые 24 часа
--              Используется для расчета средней цены за 7 дней
-- Created: 2025-10-20
-- =====================================================

-- Таблица истории цен
CREATE TABLE IF NOT EXISTS ozon_scraper_price_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Артикул товара
    article_number VARCHAR(255) NOT NULL,
    
    -- Различные типы цен (все в рублях)
    price DECIMAL(10,2),                    -- Текущая основная цена
    normal_price DECIMAL(10,2),             -- Цена без Ozon Card
    ozon_card_price DECIMAL(10,2),          -- Цена с Ozon Card
    old_price DECIMAL(10,2),                -- Старая цена (перечеркнутая)
    
    -- Метаданные scraping
    price_date TIMESTAMP NOT NULL DEFAULT NOW(),
    source VARCHAR(50) DEFAULT 'scraping',   -- 'scraping', 'api', 'manual'
    scraping_success BOOLEAN DEFAULT TRUE,
    scraping_duration_ms INTEGER,            -- Время scraping в миллисекундах
    
    -- Дополнительная информация
    product_available BOOLEAN DEFAULT TRUE,
    rating DECIMAL(3,2),                     -- Рейтинг на момент сбора
    reviews_count INTEGER,                   -- Количество отзывов
    
    -- Служебные поля
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Ограничения
    CONSTRAINT valid_prices CHECK (
        (price IS NULL OR price >= 0) AND
        (normal_price IS NULL OR normal_price >= 0) AND
        (ozon_card_price IS NULL OR ozon_card_price >= 0) AND
        (old_price IS NULL OR old_price >= 0)
    )
);

-- Индексы для быстрых запросов
CREATE INDEX IF NOT EXISTS idx_ozon_scraper_price_history_article_date 
    ON ozon_scraper_price_history(article_number, price_date DESC);

CREATE INDEX IF NOT EXISTS idx_ozon_scraper_price_history_date 
    ON ozon_scraper_price_history(price_date DESC);

CREATE INDEX IF NOT EXISTS idx_ozon_scraper_price_history_article 
    ON ozon_scraper_price_history(article_number);

-- Комментарии к таблице и колонкам
COMMENT ON TABLE ozon_scraper_price_history IS 
    'История цен товаров OZON, собираемая через web scraping';

COMMENT ON COLUMN ozon_scraper_price_history.article_number IS 
    'Артикул товара OZON (может быть SKU, offer_id или любой идентификатор)';

COMMENT ON COLUMN ozon_scraper_price_history.normal_price IS 
    'Цена без Ozon Card - обычная цена для всех покупателей';

COMMENT ON COLUMN ozon_scraper_price_history.ozon_card_price IS 
    'Специальная цена для держателей Ozon Card';

-- =====================================================
-- SQL Функция: Получить среднюю цену за N дней
-- =====================================================

CREATE OR REPLACE FUNCTION get_average_price_7days(
    p_article_number VARCHAR(255),
    p_days INTEGER DEFAULT 7
)
RETURNS TABLE (
    article_number VARCHAR(255),
    avg_price DECIMAL(10,2),
    avg_normal_price DECIMAL(10,2),
    avg_ozon_card_price DECIMAL(10,2),
    min_price DECIMAL(10,2),
    max_price DECIMAL(10,2),
    data_points INTEGER,
    first_date TIMESTAMP,
    last_date TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p_article_number,
        ROUND(AVG(ph.price), 2)::DECIMAL(10,2) as avg_price,
        ROUND(AVG(ph.normal_price), 2)::DECIMAL(10,2) as avg_normal_price,
        ROUND(AVG(ph.ozon_card_price), 2)::DECIMAL(10,2) as avg_ozon_card_price,
        MIN(ph.price)::DECIMAL(10,2) as min_price,
        MAX(ph.price)::DECIMAL(10,2) as max_price,
        COUNT(*)::INTEGER as data_points,
        MIN(ph.price_date) as first_date,
        MAX(ph.price_date) as last_date
    FROM ozon_scraper_price_history ph
    WHERE ph.article_number = p_article_number
      AND ph.price_date >= NOW() - (p_days || ' days')::INTERVAL
      AND ph.scraping_success = TRUE
      AND ph.price IS NOT NULL;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_average_price_7days IS 
    'Возвращает среднюю, минимальную и максимальную цену за указанное количество дней';

-- =====================================================
-- SQL Функция: Получить историю изменения цен
-- =====================================================

CREATE OR REPLACE FUNCTION get_price_history(
    p_article_number VARCHAR(255),
    p_days INTEGER DEFAULT 30,
    p_limit INTEGER DEFAULT 100
)
RETURNS TABLE (
    price_date TIMESTAMP,
    price DECIMAL(10,2),
    normal_price DECIMAL(10,2),
    ozon_card_price DECIMAL(10,2),
    old_price DECIMAL(10,2),
    product_available BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ph.price_date,
        ph.price,
        ph.normal_price,
        ph.ozon_card_price,
        ph.old_price,
        ph.product_available
    FROM ozon_scraper_price_history ph
    WHERE ph.article_number = p_article_number
      AND ph.price_date >= NOW() - (p_days || ' days')::INTERVAL
      AND ph.scraping_success = TRUE
    ORDER BY ph.price_date DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_price_history IS 
    'Возвращает историю изменения цен для артикула за указанный период';

-- =====================================================
-- SQL Функция: Очистка старых записей (> 30 дней)
-- =====================================================

CREATE OR REPLACE FUNCTION cleanup_old_price_history()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM ozon_scraper_price_history
    WHERE price_date < NOW() - INTERVAL '30 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_old_price_history IS 
    'Удаляет записи истории цен старше 30 дней. Возвращает количество удаленных записей.';

-- =====================================================
-- Триггер: Автоматическая очистка старых данных
-- (Опционально - можно запускать через Cron)
-- =====================================================

-- CREATE EXTENSION IF NOT EXISTS pg_cron;
-- 
-- SELECT cron.schedule(
--     'cleanup-old-price-history',
--     '0 3 * * *',  -- Каждый день в 3:00
--     $$SELECT cleanup_old_price_history()$$
-- );

-- =====================================================
-- Проверка и тестовые данные
-- =====================================================

-- Вставка тестовой записи
INSERT INTO ozon_scraper_price_history (
    article_number,
    price,
    normal_price,
    ozon_card_price,
    old_price,
    scraping_success,
    product_available
) VALUES (
    'TEST-ARTICLE-123',
    1999.00,
    1999.00,
    1799.00,
    2499.00,
    TRUE,
    TRUE
);

-- Проверка функции получения средней цены
SELECT * FROM get_average_price_7days('TEST-ARTICLE-123', 7);

-- Проверка функции получения истории
SELECT * FROM get_price_history('TEST-ARTICLE-123', 30, 10);

-- Удаление тестовых данных
DELETE FROM ozon_scraper_price_history WHERE article_number = 'TEST-ARTICLE-123';

-- =====================================================
-- Row Level Security (RLS)
-- =====================================================

-- Включаем RLS (если используется Supabase Auth)
ALTER TABLE ozon_scraper_price_history ENABLE ROW LEVEL SECURITY;

-- Политика: Все пользователи могут читать историю цен
CREATE POLICY "Anyone can read price history"
    ON ozon_scraper_price_history
    FOR SELECT
    USING (true);

-- Политика: Только системные процессы могут вставлять данные
-- (требует роль 'service_role' или 'authenticated' с правами)
CREATE POLICY "Only system can insert price history"
    ON ozon_scraper_price_history
    FOR INSERT
    WITH CHECK (auth.role() = 'service_role');

-- Политика: Никто не может обновлять историю (immutable)
CREATE POLICY "No one can update price history"
    ON ozon_scraper_price_history
    FOR UPDATE
    USING (false);

-- Политика: Только service_role может удалять старые данные
CREATE POLICY "Only system can delete old price history"
    ON ozon_scraper_price_history
    FOR DELETE
    USING (auth.role() = 'service_role');

-- =====================================================
-- Grants (права доступа)
-- =====================================================

-- Даем права на чтение всем аутентифицированным пользователям
GRANT SELECT ON ozon_scraper_price_history TO authenticated;
GRANT SELECT ON ozon_scraper_price_history TO anon;

-- Даем права на запись только service_role
GRANT INSERT, DELETE ON ozon_scraper_price_history TO service_role;

-- Даем права на выполнение функций
GRANT EXECUTE ON FUNCTION get_average_price_7days TO authenticated;
GRANT EXECUTE ON FUNCTION get_average_price_7days TO anon;
GRANT EXECUTE ON FUNCTION get_price_history TO authenticated;
GRANT EXECUTE ON FUNCTION get_price_history TO anon;
GRANT EXECUTE ON FUNCTION cleanup_old_price_history TO service_role;

-- =====================================================
-- END OF MIGRATION
-- =====================================================

