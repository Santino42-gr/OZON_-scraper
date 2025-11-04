-- =====================================================
-- Migration 009: Add Available Column to Articles
-- =====================================================
-- Description: Добавление колонки available в таблицу articles
--              для отслеживания наличия товара
-- Created: 2025-11-04
-- =====================================================

-- Добавляем колонку available
ALTER TABLE ozon_scraper_articles
ADD COLUMN IF NOT EXISTS available BOOLEAN DEFAULT TRUE;

-- Комментарий к колонке
COMMENT ON COLUMN ozon_scraper_articles.available IS 
    'Наличие товара - доступен ли товар для покупки';

-- Добавляем индекс для быстрого поиска по наличию
CREATE INDEX IF NOT EXISTS idx_ozon_scraper_articles_available 
    ON ozon_scraper_articles(available) WHERE available = FALSE;

-- Обновляем существующие записи: если статус 'active', то available = TRUE
UPDATE ozon_scraper_articles
SET available = TRUE
WHERE status = 'active' AND available IS NULL;

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
  AND column_name = 'available';

-- =====================================================
-- END OF MIGRATION
-- =====================================================

