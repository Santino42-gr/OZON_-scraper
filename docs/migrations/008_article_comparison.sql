-- =====================================================
-- Migration 008: Article Comparison Feature
-- =====================================================
-- Description: Добавление функционала сравнения артикулов
--              (свой товар vs конкурент) с расчетом метрик
-- Created: 2025-10-30
-- Related Task: COMPARISON_FEATURE_PLAN.md - Phase 1
-- =====================================================

BEGIN;

-- =====================================================
-- 1. Таблица групп артикулов для сравнения
-- =====================================================
CREATE TABLE IF NOT EXISTS ozon_scraper_article_groups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES ozon_scraper_users(id) ON DELETE CASCADE,
    name TEXT,
    group_type TEXT DEFAULT 'comparison',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT valid_group_type CHECK (group_type IN ('comparison', 'variants', 'similar'))
);

-- Комментарии к таблице и полям
COMMENT ON TABLE ozon_scraper_article_groups IS
    'Группы артикулов для сравнения (свой товар vs конкурент)';

COMMENT ON COLUMN ozon_scraper_article_groups.user_id IS
    'ID пользователя-владельца группы';

COMMENT ON COLUMN ozon_scraper_article_groups.name IS
    'Название группы сравнения (опционально)';

COMMENT ON COLUMN ozon_scraper_article_groups.group_type IS
    'Тип группы: comparison (сравнение), variants (варианты), similar (похожие)';

-- =====================================================
-- 2. Таблица членов группы (связь многие-ко-многим)
-- =====================================================
CREATE TABLE IF NOT EXISTS ozon_scraper_article_group_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    group_id UUID NOT NULL REFERENCES ozon_scraper_article_groups(id) ON DELETE CASCADE,
    article_id UUID NOT NULL REFERENCES ozon_scraper_articles(id) ON DELETE CASCADE,
    role TEXT DEFAULT 'item',
    position INTEGER DEFAULT 0,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT valid_role CHECK (role IN ('own', 'competitor', 'item')),
    CONSTRAINT unique_group_article UNIQUE (group_id, article_id)
);

-- Комментарии к таблице и полям
COMMENT ON TABLE ozon_scraper_article_group_members IS
    'Связь артикулов с группами (N-to-N). Один артикул может быть в нескольких группах';

COMMENT ON COLUMN ozon_scraper_article_group_members.role IS
    'Роль артикула: own (свой товар), competitor (конкурент), item (просто товар)';

COMMENT ON COLUMN ozon_scraper_article_group_members.position IS
    'Позиция артикула в группе для сортировки';

-- =====================================================
-- 3. Таблица снэпшотов сравнений (для истории)
-- =====================================================
CREATE TABLE IF NOT EXISTS ozon_scraper_comparison_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    group_id UUID NOT NULL REFERENCES ozon_scraper_article_groups(id) ON DELETE CASCADE,
    snapshot_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    comparison_data JSONB NOT NULL,
    metrics JSONB,
    competitiveness_index DECIMAL(3,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Комментарии к таблице и полям
COMMENT ON TABLE ozon_scraper_comparison_snapshots IS
    'История снэпшотов сравнений для отслеживания изменений во времени';

COMMENT ON COLUMN ozon_scraper_comparison_snapshots.comparison_data IS
    'Полные данные сравнения на момент снимка (цены, рейтинги, СПП и т.д.)';

COMMENT ON COLUMN ozon_scraper_comparison_snapshots.metrics IS
    'Рассчитанные метрики сравнения (разницы в ценах, рейтингах, СПП)';

COMMENT ON COLUMN ozon_scraper_comparison_snapshots.competitiveness_index IS
    'Индекс конкурентоспособности (0-1), где 1 - максимально конкурентный';

-- =====================================================
-- Индексы для производительности
-- =====================================================

-- Индексы для article_groups
CREATE INDEX idx_article_groups_user_id
    ON ozon_scraper_article_groups(user_id);

CREATE INDEX idx_article_groups_type
    ON ozon_scraper_article_groups(group_type);

CREATE INDEX idx_article_groups_created_at
    ON ozon_scraper_article_groups(created_at DESC);

-- Индексы для group_members
CREATE INDEX idx_group_members_group_id
    ON ozon_scraper_article_group_members(group_id);

CREATE INDEX idx_group_members_article_id
    ON ozon_scraper_article_group_members(article_id);

CREATE INDEX idx_group_members_role
    ON ozon_scraper_article_group_members(role);

-- Индексы для comparison_snapshots
CREATE INDEX idx_comparison_snapshots_group_date
    ON ozon_scraper_comparison_snapshots(group_id, snapshot_date DESC);

CREATE INDEX idx_comparison_snapshots_metrics
    ON ozon_scraper_comparison_snapshots USING GIN(metrics);

CREATE INDEX idx_comparison_snapshots_index
    ON ozon_scraper_comparison_snapshots(competitiveness_index);

CREATE INDEX idx_comparison_snapshots_created_at
    ON ozon_scraper_comparison_snapshots(created_at DESC);

-- =====================================================
-- Триггеры для автообновления updated_at
-- =====================================================

CREATE TRIGGER update_article_groups_updated_at
    BEFORE UPDATE ON ozon_scraper_article_groups
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- RLS Policies (Row Level Security)
-- =====================================================

ALTER TABLE ozon_scraper_article_groups ENABLE ROW LEVEL SECURITY;
ALTER TABLE ozon_scraper_article_group_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE ozon_scraper_comparison_snapshots ENABLE ROW LEVEL SECURITY;

-- Политики для article_groups
CREATE POLICY "Users can view own groups"
    ON ozon_scraper_article_groups FOR SELECT
    USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can create own groups"
    ON ozon_scraper_article_groups FOR INSERT
    WITH CHECK (auth.uid()::text = user_id::text);

CREATE POLICY "Users can update own groups"
    ON ozon_scraper_article_groups FOR UPDATE
    USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can delete own groups"
    ON ozon_scraper_article_groups FOR DELETE
    USING (auth.uid()::text = user_id::text);

-- Политики для group_members
CREATE POLICY "Users can view own group members"
    ON ozon_scraper_article_group_members FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM ozon_scraper_article_groups g
            WHERE g.id = group_id AND g.user_id::text = auth.uid()::text
        )
    );

CREATE POLICY "Users can manage own group members"
    ON ozon_scraper_article_group_members FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM ozon_scraper_article_groups g
            WHERE g.id = group_id AND g.user_id::text = auth.uid()::text
        )
    );

-- Политики для comparison_snapshots
CREATE POLICY "Users can view own snapshots"
    ON ozon_scraper_comparison_snapshots FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM ozon_scraper_article_groups g
            WHERE g.id = group_id AND g.user_id::text = auth.uid()::text
        )
    );

CREATE POLICY "Users can create own snapshots"
    ON ozon_scraper_comparison_snapshots FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM ozon_scraper_article_groups g
            WHERE g.id = group_id AND g.user_id::text = auth.uid()::text
        )
    );

-- =====================================================
-- Grants (права доступа)
-- =====================================================

GRANT SELECT, INSERT, UPDATE, DELETE ON ozon_scraper_article_groups TO authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON ozon_scraper_article_group_members TO authenticated, service_role;
GRANT SELECT, INSERT ON ozon_scraper_comparison_snapshots TO authenticated, service_role;

-- =====================================================
-- SQL Функция: Получить сравнение группы
-- =====================================================

CREATE OR REPLACE FUNCTION get_group_comparison(p_group_id UUID)
RETURNS TABLE (
    article_id UUID,
    article_number TEXT,
    role TEXT,
    product_name TEXT,
    current_price DECIMAL(10,2),
    old_price DECIMAL(10,2),
    normal_price DECIMAL(10,2),
    ozon_card_price DECIMAL(10,2),
    average_price_7days DECIMAL(10,2),
    current_rating DECIMAL(3,2),
    reviews_count INTEGER,
    spp1 DECIMAL(5,2),
    spp2 DECIMAL(5,2),
    spp_total DECIMAL(5,2),
    available BOOLEAN,
    image_url TEXT,
    product_url TEXT,
    last_check JSONB,
    item_position INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        a.id,
        a.article_number,
        m.role,
        a.name,
        a.price,
        a.old_price,
        a.normal_price,
        a.ozon_card_price,
        a.average_price_7days,
        a.rating,
        a.reviews_count,
        a.spp1,
        a.spp2,
        a.spp_total,
        a.available,
        a.image_url,
        a.product_url,
        a.last_check_data,
        m.position AS item_position
    FROM ozon_scraper_article_group_members m
    JOIN ozon_scraper_articles a ON m.article_id = a.id
    WHERE m.group_id = p_group_id
    ORDER BY m.position, m.added_at;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_group_comparison IS
    'Получает все артикулы группы с актуальными данными для сравнения';

-- =====================================================
-- SQL Функция: Сохранить снэпшот сравнения
-- =====================================================

CREATE OR REPLACE FUNCTION save_comparison_snapshot(
    p_group_id UUID,
    p_comparison_data JSONB,
    p_metrics JSONB,
    p_competitiveness_index DECIMAL(3,2)
)
RETURNS UUID AS $$
DECLARE
    v_snapshot_id UUID;
BEGIN
    INSERT INTO ozon_scraper_comparison_snapshots (
        group_id,
        comparison_data,
        metrics,
        competitiveness_index
    ) VALUES (
        p_group_id,
        p_comparison_data,
        p_metrics,
        p_competitiveness_index
    ) RETURNING id INTO v_snapshot_id;

    RETURN v_snapshot_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION save_comparison_snapshot IS
    'Сохраняет снэпшот сравнения в историю. Возвращает ID снэпшота';

-- =====================================================
-- SQL Функция: Получить историю снэпшотов
-- =====================================================

CREATE OR REPLACE FUNCTION get_comparison_history(
    p_group_id UUID,
    p_days INTEGER DEFAULT 30
)
RETURNS TABLE (
    snapshot_id UUID,
    snapshot_date TIMESTAMP WITH TIME ZONE,
    comparison_data JSONB,
    metrics JSONB,
    competitiveness_index DECIMAL(3,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        s.id,
        s.snapshot_date,
        s.comparison_data,
        s.metrics,
        s.competitiveness_index
    FROM ozon_scraper_comparison_snapshots s
    WHERE s.group_id = p_group_id
      AND s.snapshot_date >= NOW() - (p_days || ' days')::INTERVAL
    ORDER BY s.snapshot_date DESC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_comparison_history IS
    'Получает историю снэпшотов за N дней (по умолчанию 30 дней)';

-- =====================================================
-- SQL Функция: Очистка старых снэпшотов
-- =====================================================

CREATE OR REPLACE FUNCTION cleanup_old_snapshots(p_retention_days INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM ozon_scraper_comparison_snapshots
    WHERE snapshot_date < NOW() - (p_retention_days || ' days')::INTERVAL;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_old_snapshots IS
    'Удаляет снэпшоты старше N дней (по умолчанию 90 дней). Возвращает количество удаленных записей';

-- =====================================================
-- SQL Функция: Статистика групп пользователя
-- =====================================================

CREATE OR REPLACE FUNCTION get_user_groups_stats(p_user_id UUID)
RETURNS TABLE (
    total_groups INTEGER,
    comparison_groups INTEGER,
    total_articles INTEGER,
    avg_competitiveness_index DECIMAL(3,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(DISTINCT g.id)::INTEGER as total_groups,
        COUNT(DISTINCT CASE WHEN g.group_type = 'comparison' THEN g.id END)::INTEGER as comparison_groups,
        COUNT(DISTINCT m.article_id)::INTEGER as total_articles,
        ROUND(AVG(s.competitiveness_index)::NUMERIC, 2)::DECIMAL(3,2) as avg_competitiveness_index
    FROM ozon_scraper_article_groups g
    LEFT JOIN ozon_scraper_article_group_members m ON g.id = m.group_id
    LEFT JOIN LATERAL (
        SELECT competitiveness_index
        FROM ozon_scraper_comparison_snapshots
        WHERE group_id = g.id
        ORDER BY snapshot_date DESC
        LIMIT 1
    ) s ON TRUE
    WHERE g.user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_user_groups_stats IS
    'Получает статистику групп пользователя: количество групп, артикулов, средний индекс';

-- =====================================================
-- Grants для функций
-- =====================================================

GRANT EXECUTE ON FUNCTION get_group_comparison TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION save_comparison_snapshot TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION get_comparison_history TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION cleanup_old_snapshots TO service_role;
GRANT EXECUTE ON FUNCTION get_user_groups_stats TO authenticated, service_role;

-- =====================================================
-- Тестовые запросы для проверки структуры
-- =====================================================

-- Проверка структуры таблицы article_groups
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'ozon_scraper_article_groups'
ORDER BY ordinal_position;

-- Проверка структуры таблицы group_members
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'ozon_scraper_article_group_members'
ORDER BY ordinal_position;

-- Проверка структуры таблицы comparison_snapshots
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'ozon_scraper_comparison_snapshots'
ORDER BY ordinal_position;

-- Проверка созданных индексов
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename IN (
    'ozon_scraper_article_groups',
    'ozon_scraper_article_group_members',
    'ozon_scraper_comparison_snapshots'
)
ORDER BY tablename, indexname;

-- Проверка RLS политик
SELECT
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual
FROM pg_policies
WHERE tablename IN (
    'ozon_scraper_article_groups',
    'ozon_scraper_article_group_members',
    'ozon_scraper_comparison_snapshots'
)
ORDER BY tablename, policyname;

COMMIT;

-- =====================================================
-- END OF MIGRATION
-- =====================================================
