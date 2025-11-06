"""
Message Formatters

Вспомогательные функции для форматирования сообщений бота.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


def calculate_price_change(current_price: Optional[float], previous_price: Optional[float]) -> Optional[Dict[str, Any]]:
    """
    Рассчитать изменение цены
    
    Args:
        current_price: Текущая цена
        previous_price: Предыдущая цена
        
    Returns:
        Dict с ключами: arrow (🔺/🔻), abs_change (в рублях), pct_change (в процентах)
        или None если данных недостаточно
    """
    if current_price is None or previous_price is None:
        return None
    
    if previous_price == 0:
        return None
    
    abs_change = current_price - previous_price
    pct_change = (abs_change / previous_price) * 100
    
    if abs_change > 0:
        arrow = "🔺"
    elif abs_change < 0:
        arrow = "🔻"
    else:
        return None  # Цена не изменилась
    
    return {
        "arrow": arrow,
        "abs_change": abs_change,
        "pct_change": pct_change
    }


def format_price_with_dynamics(
    price: Optional[float],
    previous_price: Optional[float],
    label: str
) -> str:
    """
    Форматировать цену с динамикой изменения
    
    Args:
        price: Текущая цена
        previous_price: Предыдущая цена
        label: Название цены (например, "Без Ozon Card")
        
    Returns:
        Отформатированная строка с ценой и динамикой
    """
    if price is None:
        return ""
    
    text = f"   {label}: {price:,.0f} ₽"
    
    change = calculate_price_change(price, previous_price)
    if change:
        text += f" {change['arrow']} {abs(change['abs_change']):,.0f} ₽ ({change['pct_change']:+.1f}%)"
    
    return text + "\n"


def format_article_info(article: Dict[str, Any], previous_prices: Optional[Dict[str, float]] = None) -> str:
    """
    Форматировать информацию об артикуле для отображения
    
    Args:
        article: Данные артикула из API
        previous_prices: Опциональный словарь с предыдущими ценами:
            {"normal_price": float, "ozon_card_price": float}
        
    Returns:
        Отформатированная строка
    """
    article_number = article.get("article_number", "N/A")
    status = article.get("status", "unknown")
    created_at = article.get("created_at", "")
    is_problematic = article.get("is_problematic", False)
    
    # Emoji для статуса
    status_emoji = {
        "active": "✅",
        "inactive": "⏸️",
        "error": "❌"
    }.get(status, "❓")
    
    # Форматируем дату
    try:
        date_obj = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        date_str = date_obj.strftime("%d.%m.%Y %H:%M")
    except:
        date_str = created_at
    
    # Основная информация
    text = f"<b>Артикул:</b> <code>{article_number}</code>\n"
    text += f"<b>Статус:</b> {status_emoji} {status}\n"
    text += f"<b>Добавлен:</b> {date_str}\n"
    
    if is_problematic:
        text += f"\n<b>Проблемный артикул</b>\n"
    
    # Извлекаем цены из корневых полей или из last_check_data
    # Сначала проверяем корневые поля (приоритет)
    normal_price = article.get("normal_price")
    ozon_card_price = article.get("ozon_card_price")
    price = article.get("price")
    old_price = article.get("old_price")
    average_price_7days = article.get("average_price_7days")
    
    # Если нет в корневых полях, берем из last_check_data
    last_check = article.get("last_check_data")
    if last_check and isinstance(last_check, dict):
        if "error" in last_check:
            text += f"\n❌ <i>Ошибка: {last_check['error']}</i>\n"
        else:
            # Fallback на last_check_data если корневые поля пустые
            if not normal_price:
                normal_price = last_check.get("normal_price")
            if not ozon_card_price:
                ozon_card_price = last_check.get("ozon_card_price")
            if not price:
                price = last_check.get("price")
            if not old_price:
                old_price = last_check.get("old_price")
            if not average_price_7days:
                average_price_7days = last_check.get("average_price_7days")
    
    # Показываем цены если они есть
    if normal_price or ozon_card_price or price:
        text += "\n<b>Цены:</b>\n"
        
        # Получаем предыдущие цены если они переданы
        prev_normal = previous_prices.get("normal_price") if previous_prices else None
        prev_card = previous_prices.get("ozon_card_price") if previous_prices else None
        
        if normal_price:
            text += format_price_with_dynamics(normal_price, prev_normal, "Без Ozon Card")
        
        if ozon_card_price:
            text += format_price_with_dynamics(ozon_card_price, prev_card, "С Ozon Card")
        
        # Если есть старая цена, показываем
        if old_price and price and old_price > price:
            text += f"   Текущая цена: {price:,.0f} ₽ <s>{old_price:,.0f} ₽</s>\n"
        elif price:
            text += f"   Цена: {price:,.0f} ₽\n"
        
        # Средняя цена за неделю
        if average_price_7days:
            text += f"   Средняя за неделю: {average_price_7days:,.0f} ₽\n"
    
    # СПП показатели (из корневых полей или last_check_data)
    spp1 = article.get("spp1")
    spp2 = article.get("spp2")
    spp_total = article.get("spp_total")
    
    if last_check and isinstance(last_check, dict):
        if spp1 is None:
            spp1 = last_check.get("spp1")
        if spp2 is None:
            spp2 = last_check.get("spp2")
        if spp_total is None:
            spp_total = last_check.get("spp_total")
    
    if any([spp1 is not None, spp2 is not None, spp_total is not None]):
        text += "\n<b>Показатели скидки (СПП):</b>\n"
        
        if spp_total is not None:
            text += f"  <b>СПП Общий: {spp_total:.1f}%</b>\n"
            text += f"     (скидка от средней за неделю)\n"
        else:
            text += f"  • СПП Общий: Н/Д\n"
        
        if spp1 is not None:
            text += f"  • СПП1: {spp1:.1f}%\n"
            text += f"     (от средней → обычная цена)\n"
        else:
            text += f"  • СПП1: Н/Д\n"
        
        if spp2 is not None:
            text += f"  • СПП2: {spp2:.1f}%\n"
            text += f"     (скидка Ozon Card)\n"
        else:
            text += f"  • СПП2: Н/Д\n"
    
    # Название товара
    name = article.get("name")
    if not name and last_check and isinstance(last_check, dict):
        name = last_check.get("name")
    if name:
        text += f"\n<b>Название:</b> {name}\n"
    
    # Наличие
    available = article.get("available")
    if available is None and last_check and isinstance(last_check, dict):
        available = last_check.get("available", last_check.get("availability"))
    if available is not None:
        avail_text = "В наличии" if available else "Нет в наличии"
        avail_emoji = "✅" if available else "❌"
        text += f"<b>Наличие:</b> {avail_emoji} {avail_text}\n"
    
    return text


def format_article_list(articles: List[Dict[str, Any]]) -> str:
    """
    Форматировать список артикулов
    
    Args:
        articles: Список артикулов
        
    Returns:
        Отформатированная строка
    """
    if not articles:
        return "<i>У вас пока нет отслеживаемых артикулов</i>"
    
    text = f"<b>Ваши артикулы ({len(articles)}):</b>\n\n"
    
    for i, article in enumerate(articles, 1):
        article_number = article.get("article_number", "N/A")
        status = article.get("status", "unknown")
        
        # Emoji для статуса
        status_emoji = {
            "active": "✅",
            "inactive": "⏸️",
            "error": "❌"
        }.get(status, "❓")
        
        text += f"{i}. {status_emoji} <code>{article_number}</code>\n"
    
    return text


def format_price_history(history: List[Dict[str, Any]]) -> str:
    """
    Форматировать историю цен
    
    Args:
        history: История изменения цен
        
    Returns:
        Отформатированная строка
    """
    if not history:
        return "<i>История цен пока недоступна</i>"
    
    text = "<b>История цен:</b>\n\n"
    
    for entry in history[:10]:  # Показываем последние 10
        date = entry.get("price_date", "")
        price = entry.get("price")
        normal_price = entry.get("normal_price")
        ozon_card_price = entry.get("ozon_card_price")
        
        try:
            date_obj = datetime.fromisoformat(date.replace("Z", "+00:00"))
            date_str = date_obj.strftime("%d.%m %H:%M")
        except:
            date_str = date
        
        text += f"<b>{date_str}:</b>\n"
        if price:
            text += f"  {price} ₽"
        if normal_price:
            text += f" | {normal_price} ₽"
        if ozon_card_price:
            text += f" | {ozon_card_price} ₽"
        text += "\n"
    
    return text


def format_stats(stats: Dict[str, Any]) -> str:
    """
    Форматировать статистику пользователя
    
    Args:
        stats: Статистика из API
        
    Returns:
        Отформатированная строка
    """
    total_articles = stats.get("total_articles", 0)
    active_articles = stats.get("active_articles", 0)
    total_requests = stats.get("total_requests_30d", 0)
    successful_requests = stats.get("successful_requests_30d", 0)
    
    text = "<b>Ваша статистика:</b>\n\n"
    text += f"<b>Артикулы:</b>\n"
    text += f"  • Всего: {total_articles}\n"
    text += f"  • Активных: {active_articles}\n\n"
    
    text += f"<b>Запросы (30 дней):</b>\n"
    text += f"  • Всего: {total_requests}\n"
    text += f"  • Успешных: {successful_requests}\n"
    
    if total_requests > 0:
        success_rate = (successful_requests / total_requests * 100)
        text += f"  • Success rate: {success_rate:.1f}%\n"
    
    return text


def format_report(report: Dict[str, Any]) -> str:
    """
    Форматировать отчет
    
    Args:
        report: Данные отчета из API
        
    Returns:
        Отформатированная строка
    """
    text = "<b>ОТЧЕТ</b>\n\n"
    
    # Артикул
    article_number = report.get("article_number")
    if article_number:
        text += f"<b>Артикул:</b> <code>{article_number}</code>\n\n"
    
    # Telegram user
    telegram_id = report.get("telegram_id")
    if telegram_id:
        text += f"<b>Пользователь:</b> {telegram_id}\n\n"
    
    # Статистика артикула
    if "total_requests" in report:
        text += f"<b>Статистика:</b>\n"
        text += f"  • Запросов: {report.get('total_requests', 0)}\n"
        text += f"  • Успешных: {report.get('successful_requests', 0)}\n\n"
    
    # Средняя цена за 7 дней
    avg_price_7d = report.get("average_price_7d")
    if avg_price_7d and isinstance(avg_price_7d, dict):
        text += f"<b>Средние цены (7 дней):</b>\n"
        
        avg_price = avg_price_7d.get("avg_price")
        if avg_price:
            text += f"  • Цена: {avg_price} ₽\n"
        
        avg_normal = avg_price_7d.get("avg_normal_price")
        if avg_normal:
            text += f"  • Без карты: {avg_normal} ₽\n"
        
        avg_card = avg_price_7d.get("avg_ozon_card_price")
        if avg_card:
            text += f"  • С картой: {avg_card} ₽\n"
        
        data_points = avg_price_7d.get("data_points", 0)
        text += f"  • Точек данных: {data_points}\n\n"
    
    # СПП показатели
    spp1 = report.get("spp1")
    spp2 = report.get("spp2")
    spp_total = report.get("spp_total")
    
    if any([spp1 is not None, spp2 is not None, spp_total is not None]):
        text += f"<b>Показатели скидки:</b>\n"
        
        if spp1 is not None:
            text += f"  • СПП1: {spp1:.1f}%\n"
        else:
            text += f"  • СПП1: Н/Д\n"
        
        if spp2 is not None:
            text += f"  • СПП2: {spp2:.1f}%\n"
        else:
            text += f"  • СПП2: Н/Д\n"
        
        if spp_total is not None:
            text += f"  • СПП Общий: {spp_total:.1f}%\n"
        else:
            text += f"  • СПП Общий: Н/Д\n"
    
    return text


def format_error(error: str, details: Optional[str] = None) -> str:
    """
    Форматировать сообщение об ошибке
    
    Args:
        error: Текст ошибки
        details: Дополнительные детали (опционально)
        
    Returns:
        Отформатированная строка
    """
    text = f"<b>Ошибка:</b> {error}\n"
    
    if details:
        text += f"\n<i>{details}</i>\n"
    
    text += "\nПопробуйте позже или обратитесь к администратору"
    
    return text


def truncate_text(text: str, max_length: int = 4096) -> str:
    """
    Обрезать текст до максимальной длины (Telegram лимит)
    
    Args:
        text: Исходный текст
        max_length: Максимальная длина (default: 4096)
        
    Returns:
        Обрезанный текст
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - 50] + "\n\n...\n<i>(текст обрезан)</i>"

