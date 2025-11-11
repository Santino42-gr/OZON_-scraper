-- =====================================================
-- Migration: 012 - Add Report Frequency
-- Description: Добавление поля report_frequency для выбора частоты отчетов
-- Date: 2025-01-XX
-- =====================================================

-- Добавляем колонку report_frequency в таблицу ozon_scraper_articles
ALTER TABLE ozon_scraper_articles
ADD COLUMN IF NOT EXISTS report_frequency VARCHAR(10) DEFAULT 'once' CHECK (report_frequency IN ('once', 'twice'));

-- Комментарий
COMMENT ON COLUMN ozon_scraper_articles.report_frequency IS 
    'Частота отчетов: once - 1 раз в день (09:00), twice - 2 раза в день (09:00 и 15:00)';

-- Создаем индекс для быстрого поиска артикулов по частоте отчетов
CREATE INDEX IF NOT EXISTS idx_ozon_scraper_articles_report_frequency 
ON ozon_scraper_articles(report_frequency) 
WHERE status = 'active';

