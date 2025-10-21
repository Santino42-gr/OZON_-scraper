-- =====================================================
-- Migration 006: Add Detailed Price Fields to Articles
-- =====================================================
-- Description: Добавление детальных полей цен в таблицу articles
--              для поддержки цен с/без Ozon Card и средней цены за 7 дней
-- Created: 2025-10-21
-- Related Task: AIL-305
-- =====================================================

-- Добавляем новые поля для детальных цен
ALTER TABLE ozon_scraper_articles
ADD COLUMN IF NOT EXISTS normal_price DECIMAL(10,2),
ADD COLUMN IF NOT EXISTS ozon_card_price DECIMAL(10,2),
ADD COLUMN IF NOT EXISTS average_price_7days DECIMAL(10,2),
ADD COLUMN IF NOT EXISTS price_updated_at TIMESTAMP;

-- Комментарии к новым полям
COMMENT ON COLUMN ozon_scraper_articles.normal_price IS 
    'Цена без Ozon Card - обычная цена для всех покупателей';

COMMENT ON COLUMN ozon_scraper_articles.ozon_card_price IS 
    'Специальная цена для держателей Ozon Card';

COMMENT ON COLUMN ozon_scraper_articles.average_price_7days IS 
    'Средняя цена за последние 7 дней (рассчитывается из price_history)';

COMMENT ON COLUMN ozon_scraper_articles.price_updated_at IS 
    'Время последнего обновления информации о ценах';

-- Добавляем индекс для быстрого поиска по дате обновления цен
CREATE INDEX IF NOT EXISTS idx_ozon_scraper_articles_price_updated_at 
    ON ozon_scraper_articles(price_updated_at DESC);

-- Добавляем constraint для валидации цен
ALTER TABLE ozon_scraper_articles
ADD CONSTRAINT IF NOT EXISTS valid_detailed_prices CHECK (
    (normal_price IS NULL OR normal_price >= 0) AND
    (ozon_card_price IS NULL OR ozon_card_price >= 0) AND
    (average_price_7days IS NULL OR average_price_7days >= 0)
);

-- =====================================================
-- SQL Функция: Обновить средние цены для всех артикулов
-- =====================================================

CREATE OR REPLACE FUNCTION update_all_average_prices()
RETURNS INTEGER AS $$
DECLARE
    updated_count INTEGER := 0;
    article_record RECORD;
    avg_data RECORD;
BEGIN
    -- Проходим по всем активным артикулам
    FOR article_record IN 
        SELECT DISTINCT article_number 
        FROM ozon_scraper_articles 
        WHERE status = 'active'
    LOOP
        -- Получаем среднюю цену за 7 дней
        SELECT * INTO avg_data 
        FROM get_average_price_7days(article_record.article_number, 7);
        
        -- Обновляем только если есть данные
        IF avg_data.avg_price IS NOT NULL THEN
            UPDATE ozon_scraper_articles
            SET average_price_7days = avg_data.avg_price,
                price_updated_at = NOW()
            WHERE article_number = article_record.article_number;
            
            updated_count := updated_count + 1;
        END IF;
    END LOOP;
    
    RETURN updated_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_all_average_prices IS 
    'Обновляет средние цены за 7 дней для всех активных артикулов. Возвращает количество обновленных записей.';

-- =====================================================
-- SQL Функция: Обновить средние цены для конкретного артикула
-- =====================================================

CREATE OR REPLACE FUNCTION update_article_average_price(
    p_article_number VARCHAR(255)
)
RETURNS BOOLEAN AS $$
DECLARE
    avg_data RECORD;
BEGIN
    -- Получаем среднюю цену за 7 дней
    SELECT * INTO avg_data 
    FROM get_average_price_7days(p_article_number, 7);
    
    -- Обновляем если есть данные
    IF avg_data.avg_price IS NOT NULL THEN
        UPDATE ozon_scraper_articles
        SET average_price_7days = avg_data.avg_price,
            price_updated_at = NOW()
        WHERE article_number = p_article_number;
        
        RETURN TRUE;
    END IF;
    
    RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_article_average_price IS 
    'Обновляет среднюю цену за 7 дней для конкретного артикула. Возвращает TRUE если обновлено.';

-- =====================================================
-- Grants (права доступа)
-- =====================================================

-- Даем права на выполнение функций
GRANT EXECUTE ON FUNCTION update_all_average_prices TO service_role;
GRANT EXECUTE ON FUNCTION update_article_average_price TO authenticated;
GRANT EXECUTE ON FUNCTION update_article_average_price TO service_role;

-- =====================================================
-- Тестирование
-- =====================================================

-- Проверка структуры таблицы
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'ozon_scraper_articles'
  AND column_name IN ('normal_price', 'ozon_card_price', 'average_price_7days', 'price_updated_at')
ORDER BY ordinal_position;

-- =====================================================
-- END OF MIGRATION
-- =====================================================

