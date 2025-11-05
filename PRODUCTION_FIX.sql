-- =====================================================
-- PRODUCTION FIX: Apply Missing Migrations
-- =====================================================
-- Description: Консолидированный скрипт для применения всех недостающих миграций в продакшене
-- Created: 2025-11-05
-- =====================================================

BEGIN;

-- =====================================================
-- 1. Migration 006: Add Detailed Price Fields
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
DO $$
BEGIN
    ALTER TABLE ozon_scraper_articles
    ADD CONSTRAINT valid_detailed_prices CHECK (
        (normal_price IS NULL OR normal_price >= 0) AND
        (ozon_card_price IS NULL OR ozon_card_price >= 0) AND
        (average_price_7days IS NULL OR average_price_7days >= 0)
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- =====================================================
-- 2. Migration 009: Add Available Column
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
-- 3. Migration 010: Add Image URL, Product URL, Name, Last Check
-- =====================================================

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
-- Verification: Check All Columns
-- =====================================================

-- Проверка структуры таблицы
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'ozon_scraper_articles'
  AND column_name IN (
    'normal_price',
    'ozon_card_price',
    'average_price_7days',
    'price_updated_at',
    'available',
    'image_url',
    'product_url',
    'name',
    'last_check'
  )
ORDER BY column_name;

-- =====================================================
-- Success Message
-- =====================================================

DO $$
BEGIN
    RAISE NOTICE '============================================';
    RAISE NOTICE 'PRODUCTION FIX: Migrations applied successfully!';
    RAISE NOTICE 'Added columns:';
    RAISE NOTICE '  - normal_price, ozon_card_price, average_price_7days, price_updated_at';
    RAISE NOTICE '  - available';
    RAISE NOTICE '  - image_url, product_url, name, last_check';
    RAISE NOTICE 'All indexes and constraints created.';
    RAISE NOTICE '============================================';
END $$;

COMMIT;
