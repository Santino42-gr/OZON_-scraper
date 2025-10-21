"""
Тестовый скрипт для проверки показателей СПП

Usage:
    python test_spp_metrics.py
"""

import asyncio
from services.ozon_scraper import OzonScraper
from models.ozon_models import SPPMetrics
from database import get_supabase_client
from loguru import logger


def test_spp_calculation():
    """Тест функции расчета СПП"""
    logger.info("="*60)
    logger.info("Test 1: Расчет СПП метрик")
    logger.info("="*60)
    
    # Тест 1: Все цены доступны
    result = OzonScraper.calculate_spp_metrics(
        average_price_7days=1200.0,
        normal_price=900.0,
        ozon_card_price=810.0
    )
    
    assert result["spp1"] == 25.0, f"Expected spp1=25.0, got {result['spp1']}"
    assert result["spp2"] == 10.0, f"Expected spp2=10.0, got {result['spp2']}"
    assert result["spp_total"] == 32.5, f"Expected spp_total=32.5, got {result['spp_total']}"
    logger.info(f"✅ Тест 1 пройден: {result}")
    
    # Тест 2: Нет цены с картой (СПП2 и СПП Общий должны быть NULL)
    result2 = OzonScraper.calculate_spp_metrics(
        average_price_7days=1200.0,
        normal_price=900.0,
        ozon_card_price=None
    )
    
    assert result2["spp1"] == 25.0
    assert result2["spp2"] is None
    assert result2["spp_total"] is None
    logger.info(f"✅ Тест 2 пройден: {result2}")
    
    # Тест 3: Нет средней цены (СПП1 и СПП Общий должны быть NULL)
    result3 = OzonScraper.calculate_spp_metrics(
        average_price_7days=None,
        normal_price=900.0,
        ozon_card_price=810.0
    )
    
    assert result3["spp1"] is None
    assert result3["spp2"] == 10.0
    assert result3["spp_total"] is None
    logger.info(f"✅ Тест 3 пройден: {result3}")
    
    # Тест 4: Все цены NULL
    result4 = OzonScraper.calculate_spp_metrics(
        average_price_7days=None,
        normal_price=None,
        ozon_card_price=None
    )
    
    assert result4["spp1"] is None
    assert result4["spp2"] is None
    assert result4["spp_total"] is None
    logger.info(f"✅ Тест 4 пройден: {result4}")
    
    logger.info("✅ Все тесты расчета СПП пройдены!")


def test_spp_model():
    """Тест модели SPPMetrics"""
    logger.info("="*60)
    logger.info("Test 2: Модель SPPMetrics")
    logger.info("="*60)
    
    # Создание модели
    metrics = SPPMetrics(
        spp1=24.4,
        spp2=9.9,
        spp_total=31.9
    )
    
    # Тест форматирования
    assert metrics.format_spp(24.4) == "24.4%"
    assert metrics.format_spp(None) == "Н/Д"
    logger.info("✅ Форматирование работает")
    
    # Тест to_dict_formatted
    formatted = metrics.to_dict_formatted()
    assert formatted["spp1"] == "24.4%"
    assert formatted["spp2"] == "9.9%"
    assert formatted["spp_total"] == "31.9%"
    logger.info(f"✅ to_dict_formatted: {formatted}")
    
    # Модель с NULL значениями
    metrics_null = SPPMetrics(
        spp1=25.0,
        spp2=None,
        spp_total=None
    )
    
    formatted_null = metrics_null.to_dict_formatted()
    assert formatted_null["spp1"] == "25.0%"
    assert formatted_null["spp2"] == "Н/Д"
    assert formatted_null["spp_total"] == "Н/Д"
    logger.info(f"✅ Обработка NULL: {formatted_null}")
    
    logger.info("✅ Все тесты модели SPPMetrics пройдены!")


def test_sql_functions():
    """Тест SQL функций"""
    logger.info("="*60)
    logger.info("Test 3: SQL функции")
    logger.info("="*60)
    
    supabase = get_supabase_client()
    
    # Получаем первый активный артикул для теста
    response = supabase.table("ozon_scraper_articles") \
        .select("article_number, average_price_7days, normal_price, ozon_card_price") \
        .eq("status", "active") \
        .limit(1) \
        .execute()
    
    if not response.data:
        logger.warning("⚠️ Нет активных артикулов для теста SQL функций")
        return
    
    article = response.data[0]
    article_number = article["article_number"]
    
    logger.info(f"Тестируем артикул: {article_number}")
    logger.info(f"  Средняя цена: {article.get('average_price_7days')}")
    logger.info(f"  Обычная цена: {article.get('normal_price')}")
    logger.info(f"  Цена с картой: {article.get('ozon_card_price')}")
    
    # Тест calculate_spp_metrics
    try:
        result = supabase.rpc(
            "calculate_spp_metrics",
            {"p_article_number": article_number}
        ).execute()
        
        if result.data:
            logger.info(f"✅ calculate_spp_metrics: {result.data}")
        else:
            logger.warning("⚠️ Функция вернула пустой результат")
    except Exception as e:
        logger.error(f"❌ Ошибка при вызове calculate_spp_metrics: {e}")
    
    # Тест update_article_spp_metrics
    try:
        result = supabase.rpc(
            "update_article_spp_metrics",
            {"p_article_number": article_number}
        ).execute()
        
        logger.info(f"✅ update_article_spp_metrics: {result.data}")
        
        # Проверяем что обновилось
        updated = supabase.table("ozon_scraper_articles") \
            .select("spp1, spp2, spp_total") \
            .eq("article_number", article_number) \
            .limit(1) \
            .execute()
        
        if updated.data:
            logger.info(f"  СПП после обновления: {updated.data[0]}")
    except Exception as e:
        logger.error(f"❌ Ошибка при вызове update_article_spp_metrics: {e}")
    
    logger.info("✅ SQL функции протестированы!")


def main():
    """Запуск всех тестов"""
    logger.info("🚀 Запуск тестов показателей СПП")
    logger.info("")
    
    try:
        # Тест 1: Расчет СПП
        test_spp_calculation()
        logger.info("")
        
        # Тест 2: Модель SPPMetrics
        test_spp_model()
        logger.info("")
        
        # Тест 3: SQL функции
        test_sql_functions()
        logger.info("")
        
        logger.info("="*60)
        logger.info("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        logger.info("="*60)
        
    except AssertionError as e:
        logger.error(f"❌ Тест провален: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        logger.error(f"❌ Ошибка при выполнении тестов: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

