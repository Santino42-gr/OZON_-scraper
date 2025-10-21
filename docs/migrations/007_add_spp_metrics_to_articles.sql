-- =====================================================
-- Migration 007: Add SPP Metrics to Articles
-- =====================================================
-- Description: Добавление показателей скидки (СПП) в таблицы
--              СПП1, СПП2, СПП Общий для анализа скидок
-- Created: 2025-10-21
-- Related Task: Добавить показатели СПП
-- =====================================================

-- Добавляем поля СПП в таблицу articles
ALTER TABLE ozon_scraper_articles
ADD COLUMN IF NOT EXISTS spp1 DECIMAL(5,2),        -- СПП1 в процентах
ADD COLUMN IF NOT EXISTS spp2 DECIMAL(5,2),        -- СПП2 в процентах
ADD COLUMN IF NOT EXISTS spp_total DECIMAL(5,2);   -- СПП Общий в процентах

-- Комментарии к полям
COMMENT ON COLUMN ozon_scraper_articles.spp1 IS 
    'СПП1 - Скидка от средней цены за 7 дней до обычной цены (%)';

COMMENT ON COLUMN ozon_scraper_articles.spp2 IS 
    'СПП2 - Скидка Ozon Card: от обычной цены до цены с картой (%)';

COMMENT ON COLUMN ozon_scraper_articles.spp_total IS 
    'СПП Общий - Общая скидка от средней за 7 дней до цены с картой (%)';

-- Добавляем индекс для сортировки по СПП
CREATE INDEX IF NOT EXISTS idx_ozon_scraper_articles_spp_total 
    ON ozon_scraper_articles(spp_total DESC);

CREATE INDEX IF NOT EXISTS idx_ozon_scraper_articles_spp1 
    ON ozon_scraper_articles(spp1 DESC);

-- Добавляем поля СПП в таблицу price_history
ALTER TABLE ozon_scraper_price_history
ADD COLUMN IF NOT EXISTS spp1 DECIMAL(5,2),
ADD COLUMN IF NOT EXISTS spp2 DECIMAL(5,2),
ADD COLUMN IF NOT EXISTS spp_total DECIMAL(5,2);

-- Комментарии к полям price_history
COMMENT ON COLUMN ozon_scraper_price_history.spp1 IS 
    'СПП1 на момент сбора данных (%)';

COMMENT ON COLUMN ozon_scraper_price_history.spp2 IS 
    'СПП2 на момент сбора данных (%)';

COMMENT ON COLUMN ozon_scraper_price_history.spp_total IS 
    'СПП Общий на момент сбора данных (%)';

-- =====================================================
-- SQL Функция: Рассчитать показатели СПП
-- =====================================================

CREATE OR REPLACE FUNCTION calculate_spp_metrics(p_article_number VARCHAR(255))
RETURNS TABLE (
    spp1 DECIMAL(5,2),
    spp2 DECIMAL(5,2),
    spp_total DECIMAL(5,2)
) AS $$
DECLARE
    v_average_price DECIMAL(10,2);
    v_normal_price DECIMAL(10,2);
    v_ozon_card_price DECIMAL(10,2);
BEGIN
    -- Получаем цены из таблицы
    SELECT average_price_7days, normal_price, ozon_card_price
    INTO v_average_price, v_normal_price, v_ozon_card_price
    FROM ozon_scraper_articles
    WHERE article_number = p_article_number
    LIMIT 1;
    
    -- СПП1: (avg - normal) / avg * 100
    IF v_average_price IS NOT NULL AND v_average_price > 0 AND v_normal_price IS NOT NULL THEN
        spp1 := ROUND(((v_average_price - v_normal_price) / v_average_price * 100)::NUMERIC, 1);
    ELSE
        spp1 := NULL;
    END IF;
    
    -- СПП2: (normal - card) / normal * 100
    IF v_normal_price IS NOT NULL AND v_normal_price > 0 AND v_ozon_card_price IS NOT NULL THEN
        spp2 := ROUND(((v_normal_price - v_ozon_card_price) / v_normal_price * 100)::NUMERIC, 1);
    ELSE
        spp2 := NULL;
    END IF;
    
    -- СПП Общий: (avg - card) / avg * 100
    IF v_average_price IS NOT NULL AND v_average_price > 0 AND v_ozon_card_price IS NOT NULL THEN
        spp_total := ROUND(((v_average_price - v_ozon_card_price) / v_average_price * 100)::NUMERIC, 1);
    ELSE
        spp_total := NULL;
    END IF;
    
    RETURN QUERY SELECT spp1, spp2, spp_total;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION calculate_spp_metrics IS 
    'Рассчитывает показатели скидки (СПП1, СПП2, СПП Общий) для артикула';

-- =====================================================
-- SQL Функция: Обновить показатели СПП для артикула
-- =====================================================

CREATE OR REPLACE FUNCTION update_article_spp_metrics(p_article_number VARCHAR(255))
RETURNS BOOLEAN AS $$
DECLARE
    v_metrics RECORD;
BEGIN
    SELECT * INTO v_metrics FROM calculate_spp_metrics(p_article_number);
    
    UPDATE ozon_scraper_articles
    SET spp1 = v_metrics.spp1,
        spp2 = v_metrics.spp2,
        spp_total = v_metrics.spp_total
    WHERE article_number = p_article_number;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_article_spp_metrics IS 
    'Обновляет показатели СПП для конкретного артикула. Возвращает TRUE если обновлено.';

-- =====================================================
-- SQL Функция: Обновить СПП для всех артикулов
-- =====================================================

CREATE OR REPLACE FUNCTION update_all_spp_metrics()
RETURNS INTEGER AS $$
DECLARE
    updated_count INTEGER := 0;
    article_record RECORD;
BEGIN
    FOR article_record IN 
        SELECT DISTINCT article_number 
        FROM ozon_scraper_articles 
        WHERE status = 'active'
    LOOP
        IF update_article_spp_metrics(article_record.article_number) THEN
            updated_count := updated_count + 1;
        END IF;
    END LOOP;
    
    RETURN updated_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_all_spp_metrics IS 
    'Обновляет показатели СПП для всех активных артикулов. Возвращает количество обновленных записей.';

-- =====================================================
-- Grants (права доступа)
-- =====================================================

-- Даем права на выполнение функций
GRANT EXECUTE ON FUNCTION calculate_spp_metrics TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION update_article_spp_metrics TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION update_all_spp_metrics TO service_role;

-- =====================================================
-- Тестирование
-- =====================================================

-- Проверка структуры таблицы articles
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'ozon_scraper_articles'
  AND column_name IN ('spp1', 'spp2', 'spp_total')
ORDER BY ordinal_position;

-- Проверка структуры таблицы price_history
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'ozon_scraper_price_history'
  AND column_name IN ('spp1', 'spp2', 'spp_total')
ORDER BY ordinal_position;

-- =====================================================
-- END OF MIGRATION
-- =====================================================

