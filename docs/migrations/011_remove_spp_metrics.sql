-- =====================================================
-- Migration: 011 - Remove SPP Metrics
-- Description: Удаление всех колонок и функций связанных с СПП
-- Date: 2025-01-XX
-- =====================================================

-- Удаляем колонки СПП из таблицы ozon_scraper_articles
ALTER TABLE ozon_scraper_articles
DROP COLUMN IF EXISTS spp1,
DROP COLUMN IF EXISTS spp2,
DROP COLUMN IF EXISTS spp_total;

-- Удаляем колонки СПП из таблицы ozon_scraper_price_history
ALTER TABLE ozon_scraper_price_history
DROP COLUMN IF EXISTS spp1,
DROP COLUMN IF EXISTS spp2,
DROP COLUMN IF EXISTS spp_total;

-- Удаляем SQL функции для расчета СПП
DROP FUNCTION IF EXISTS calculate_spp_metrics(VARCHAR);
DROP FUNCTION IF EXISTS update_article_spp_metrics(VARCHAR);
DROP FUNCTION IF EXISTS update_all_spp_metrics();

-- Комментарий
COMMENT ON TABLE ozon_scraper_articles IS 'Таблица артикулов OZON без СПП метрик';

