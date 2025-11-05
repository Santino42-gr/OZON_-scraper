-- =====================================================
-- Обновление существующих артикулов:
-- Заполнение полей цен из last_check_data
-- =====================================================

UPDATE ozon_scraper_articles
SET
    -- Заполняем цены из last_check_data если поля NULL
    price = COALESCE(
        price,
        (last_check_data->>'price')::DECIMAL(10,2),
        (last_check_data->>'ozon_card_price')::DECIMAL(10,2),
        (last_check_data->>'normal_price')::DECIMAL(10,2)
    ),
    old_price = COALESCE(
        old_price,
        (last_check_data->>'old_price')::DECIMAL(10,2)
    ),
    normal_price = COALESCE(
        normal_price,
        (last_check_data->>'normal_price')::DECIMAL(10,2)
    ),
    ozon_card_price = COALESCE(
        ozon_card_price,
        (last_check_data->>'ozon_card_price')::DECIMAL(10,2)
    ),
    average_price_7days = COALESCE(
        average_price_7days,
        (last_check_data->>'average_price_7days')::DECIMAL(10,2)
    ),
    -- Заполняем другие поля
    name = COALESCE(name, (last_check_data->>'name')::TEXT),
    rating = COALESCE(rating, (last_check_data->>'rating')::DECIMAL(3,2)),
    reviews_count = COALESCE(
        reviews_count,
        (last_check_data->>'reviews_count')::INTEGER
    ),
    spp1 = COALESCE(spp1, (last_check_data->>'spp1')::DECIMAL(5,2)),
    spp2 = COALESCE(spp2, (last_check_data->>'spp2')::DECIMAL(5,2)),
    spp_total = COALESCE(spp_total, (last_check_data->>'spp_total')::DECIMAL(5,2)),
    available = COALESCE(
        available,
        (last_check_data->>'available')::BOOLEAN,
        (last_check_data->>'availability')::TEXT = 'IN_STOCK',
        TRUE
    ),
    image_url = COALESCE(
        image_url,
        (last_check_data->>'image_url')::TEXT
    ),
    product_url = COALESCE(
        product_url,
        (last_check_data->>'url')::TEXT,
        (last_check_data->>'product_url')::TEXT
    )
WHERE 
    last_check_data IS NOT NULL
    AND (
        -- Обновляем только если есть данные в last_check_data
        (last_check_data->>'price') IS NOT NULL
        OR (last_check_data->>'normal_price') IS NOT NULL
        OR (last_check_data->>'ozon_card_price') IS NOT NULL
    )
    AND (
        -- И хотя бы одно поле цены NULL
        price IS NULL
        OR normal_price IS NULL
        OR ozon_card_price IS NULL
    );

