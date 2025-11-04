"""
SPP (Скидка) Calculator
Утилита для расчёта показателей СПП (скидок) для товаров Ozon
"""

from typing import Optional, Dict


def calculate_spp_metrics(
    average_price_7days: Optional[float],
    normal_price: Optional[float],
    ozon_card_price: Optional[float]
) -> Dict[str, Optional[float]]:
    """
    Рассчитать показатели СПП (скидки)

    Формулы:
    - СПП1 = (Средняя за 7 дней - Обычная цена) / Средняя за 7 дней × 100%
    - СПП2 = (Обычная цена - Цена с картой) / Обычная цена × 100%
    - СПП Общий = (Средняя за 7 дней - Цена с картой) / Средняя за 7 дней × 100%

    Args:
        average_price_7days: Средняя цена за 7 дней
        normal_price: Цена без Ozon Card
        ozon_card_price: Цена с Ozon Card

    Returns:
        Dict с ключами spp1, spp2, spp_total (значения в процентах или None)

    Example:
        >>> calculate_spp_metrics(1950.0, 1999.0, 1799.0)
        {'spp1': -2.5, 'spp2': 10.0, 'spp_total': 7.7}
    """
    spp1 = None
    spp2 = None
    spp_total = None

    # СПП1: (avg - normal) / avg * 100
    if average_price_7days and average_price_7days > 0 and normal_price is not None:
        spp1 = round((average_price_7days - normal_price) / average_price_7days * 100, 1)

    # СПП2: (normal - card) / normal * 100
    if normal_price and normal_price > 0 and ozon_card_price is not None:
        spp2 = round((normal_price - ozon_card_price) / normal_price * 100, 1)

    # СПП Общий: (avg - card) / avg * 100
    if average_price_7days and average_price_7days > 0 and ozon_card_price is not None:
        spp_total = round((average_price_7days - ozon_card_price) / average_price_7days * 100, 1)

    return {
        "spp1": spp1,
        "spp2": spp2,
        "spp_total": spp_total
    }
