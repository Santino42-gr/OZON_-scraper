-- =====================================================
-- Migration 010: Add image_url and product_url to Articles
-- =====================================================
-- Description: Добавление колонок image_url и product_url в таблицу articles
--              для хранения ссылок на изображения и страницы товаров
-- Created: 2025-11-05
-- =====================================================

BEGIN;

-- Добавляем колонку image_url (ссылка на изображение товара)
ALTER TABLE ozon_scraper_articles
ADD COLUMN IF NOT EXISTS image_url TEXT;

-- Добавляем колонку product_url (ссылка на страницу товара на OZON)
ALTER TABLE ozon_scraper_articles
ADD COLUMN IF NOT EXISTS product_url TEXT;

-- Добавляем колонку name (название товара) если её нет
ALTER TABLE ozon_scraper_articles
ADD COLUMN IF NOT EXISTS name TEXT;

-- Добавляем колонку last_check (время последней проверки) если её нет
ALTER TABLE ozon_scraper_articles
ADD COLUMN IF NOT EXISTS last_check TIMESTAMP WITH TIME ZONE;

-- Комментарии к новым полям
COMMENT ON COLUMN ozon_scraper_articles.image_url IS 
    'URL изображения товара на OZON';

COMMENT ON COLUMN ozon_scraper_articles.product_url IS 
    'URL страницы товара на OZON';

COMMENT ON COLUMN ozon_scraper_articles.name IS 
    'Название товара';

COMMENT ON COLUMN ozon_scraper_articles.last_check IS 
    'Время последней проверки товара через API';

-- Добавляем индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_ozon_scraper_articles_name 
    ON ozon_scraper_articles(name) WHERE name IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_ozon_scraper_articles_last_check 
    ON ozon_scraper_articles(last_check DESC) WHERE last_check IS NOT NULL;

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
  AND column_name IN ('image_url', 'product_url', 'name', 'last_check')
ORDER BY column_name;

-- =====================================================
-- END OF MIGRATION
-- =====================================================

COMMIT;

