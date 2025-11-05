-- =====================================================
-- Fix: Обновление функции get_group_comparison
-- для извлечения цен из last_check_data если поля NULL
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
        COALESCE(a.name, (a.last_check_data->>'name')::TEXT) AS name,
        -- Извлекаем цены из отдельных полей или из last_check_data если NULL
        COALESCE(
            a.price,
            (a.last_check_data->>'price')::DECIMAL(10,2),
            (a.last_check_data->>'ozon_card_price')::DECIMAL(10,2),
            (a.last_check_data->>'normal_price')::DECIMAL(10,2)
        ) AS price,
        COALESCE(
            a.old_price,
            (a.last_check_data->>'old_price')::DECIMAL(10,2)
        ) AS old_price,
        COALESCE(
            a.normal_price,
            (a.last_check_data->>'normal_price')::DECIMAL(10,2)
        ) AS normal_price,
        COALESCE(
            a.ozon_card_price,
            (a.last_check_data->>'ozon_card_price')::DECIMAL(10,2)
        ) AS ozon_card_price,
        COALESCE(
            a.average_price_7days,
            (a.last_check_data->>'average_price_7days')::DECIMAL(10,2)
        ) AS average_price_7days,
        COALESCE(
            a.rating,
            (a.last_check_data->>'rating')::DECIMAL(3,2)
        ) AS rating,
        COALESCE(
            a.reviews_count,
            (a.last_check_data->>'reviews_count')::INTEGER
        ) AS reviews_count,
        COALESCE(
            a.spp1,
            (a.last_check_data->>'spp1')::DECIMAL(5,2)
        ) AS spp1,
        COALESCE(
            a.spp2,
            (a.last_check_data->>'spp2')::DECIMAL(5,2)
        ) AS spp2,
        COALESCE(
            a.spp_total,
            (a.last_check_data->>'spp_total')::DECIMAL(5,2)
        ) AS spp_total,
        COALESCE(
            a.available,
            (a.last_check_data->>'available')::BOOLEAN,
            (a.last_check_data->>'availability')::TEXT = 'IN_STOCK',
            TRUE
        ) AS available,
        COALESCE(
            a.image_url,
            (a.last_check_data->>'image_url')::TEXT
        ) AS image_url,
        COALESCE(
            a.product_url,
            (a.last_check_data->>'url')::TEXT,
            (a.last_check_data->>'product_url')::TEXT
        ) AS product_url,
        a.last_check_data,
        m.position AS item_position
    FROM ozon_scraper_article_group_members m
    JOIN ozon_scraper_articles a ON m.article_id = a.id
    WHERE m.group_id = p_group_id
    ORDER BY m.position, m.added_at;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_group_comparison IS
    'Получает все артикулы группы с актуальными данными для сравнения. Извлекает данные из отдельных полей или из last_check_data если поля NULL';

