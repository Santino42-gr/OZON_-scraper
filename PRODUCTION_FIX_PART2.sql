-- =====================================================
-- PRODUCTION FIX PART 2: Add Missing Price and Rating Columns
-- =====================================================
-- Description: Добавление недостающих колонок price, old_price, rating, reviews_count
-- Created: 2025-11-05
-- =====================================================

BEGIN;

-- =====================================================
-- Add Missing Price Columns
-- =====================================================

-- Добавляем колонку price (текущая основная цена)
ALTER TABLE ozon_scraper_articles
ADD COLUMN IF NOT EXISTS price DECIMAL(10,2);

-- Добавляем колонку old_price (старая перечеркнутая цена)
ALTER TABLE ozon_scraper_articles
ADD COLUMN IF NOT EXISTS old_price DECIMAL(10,2);

-- =====================================================
-- Add Rating and Reviews Columns
-- =====================================================

-- Добавляем колонку rating (рейтинг товара)
ALTER TABLE ozon_scraper_articles
ADD COLUMN IF NOT EXISTS rating DECIMAL(3,2);

-- Добавляем колонку reviews_count (количество отзывов)
ALTER TABLE ozon_scraper_articles
ADD COLUMN IF NOT EXISTS reviews_count INTEGER;

-- =====================================================
-- Add SPP Metrics Columns (if not exists)
-- =====================================================

-- Добавляем колонки для метрик СПП
ALTER TABLE ozon_scraper_articles
ADD COLUMN IF NOT EXISTS spp1 DECIMAL(5,2),
ADD COLUMN IF NOT EXISTS spp2 DECIMAL(5,2),
ADD COLUMN IF NOT EXISTS spp_total DECIMAL(5,2);

-- =====================================================
-- Add Comments
-- =====================================================

COMMENT ON COLUMN ozon_scraper_articles.price IS
    'Текущая основная цена товара';

COMMENT ON COLUMN ozon_scraper_articles.old_price IS
    'Старая цена (перечеркнутая) - показывает размер скидки';

COMMENT ON COLUMN ozon_scraper_articles.rating IS
    'Рейтинг товара (0.00 - 5.00)';

COMMENT ON COLUMN ozon_scraper_articles.reviews_count IS
    'Количество отзывов на товар';

COMMENT ON COLUMN ozon_scraper_articles.spp1 IS
    'СПП1 - скидка от средней цены до обычной цены (%)';

COMMENT ON COLUMN ozon_scraper_articles.spp2 IS
    'СПП2 - дополнительная скидка с Ozon Card (%)';

COMMENT ON COLUMN ozon_scraper_articles.spp_total IS
    'СПП Общий - общая скидка (SPP1 + SPP2) (%)';

-- =====================================================
-- Add Indexes
-- =====================================================

-- Индекс для быстрого поиска по цене
CREATE INDEX IF NOT EXISTS idx_ozon_scraper_articles_price
    ON ozon_scraper_articles(price) WHERE price IS NOT NULL;

-- Индекс для быстрого поиска по рейтингу
CREATE INDEX IF NOT EXISTS idx_ozon_scraper_articles_rating
    ON ozon_scraper_articles(rating DESC) WHERE rating IS NOT NULL;

-- =====================================================
-- Add Constraints
-- =====================================================

-- Constraint для валидации цен
DO $$
BEGIN
    ALTER TABLE ozon_scraper_articles
    ADD CONSTRAINT valid_price_fields CHECK (
        (price IS NULL OR price >= 0) AND
        (old_price IS NULL OR old_price >= 0) AND
        (rating IS NULL OR (rating >= 0 AND rating <= 5)) AND
        (reviews_count IS NULL OR reviews_count >= 0) AND
        (spp1 IS NULL OR (spp1 >= 0 AND spp1 <= 100)) AND
        (spp2 IS NULL OR (spp2 >= 0 AND spp2 <= 100)) AND
        (spp_total IS NULL OR (spp_total >= 0 AND spp_total <= 100))
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

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
    'price',
    'old_price',
    'rating',
    'reviews_count',
    'spp1',
    'spp2',
    'spp_total'
  )
ORDER BY column_name;

-- =====================================================
-- Success Message
-- =====================================================

DO $$
BEGIN
    RAISE NOTICE '============================================';
    RAISE NOTICE 'PRODUCTION FIX PART 2: Migrations applied successfully!';
    RAISE NOTICE 'Added columns:';
    RAISE NOTICE '  - price, old_price';
    RAISE NOTICE '  - rating, reviews_count';
    RAISE NOTICE '  - spp1, spp2, spp_total';
    RAISE NOTICE 'All indexes and constraints created.';
    RAISE NOTICE '============================================';
END $$;

COMMIT;
