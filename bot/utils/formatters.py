"""
Message Formatters

Вспомогательные функции для форматирования сообщений бота.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


def format_article_info(article: Dict[str, Any]) -> str:
    """
    Форматировать информацию об артикуле для отображения
    
    Args:
        article: Данные артикула из API
        
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
    text = f"<b>📦 Артикул:</b> <code>{article_number}</code>\n"
    text += f"<b>Статус:</b> {status_emoji} {status}\n"
    text += f"<b>Добавлен:</b> {date_str}\n"
    
    if is_problematic:
        text += f"\n⚠️ <b>Проблемный артикул</b>\n"
    
    # Данные последней проверки
    last_check = article.get("last_check_data")
    if last_check and isinstance(last_check, dict):
        if "error" in last_check:
            text += f"\n❌ <i>Ошибка: {last_check['error']}</i>\n"
        else:
            # Цены
            price = last_check.get("price")
            old_price = last_check.get("old_price")
            normal_price = last_check.get("normal_price")
            ozon_card_price = last_check.get("ozon_card_price")
            
            if price:
                text += f"\n<b>💰 Цена:</b> {price} ₽"
                if old_price and old_price > price:
                    text += f" <s>{old_price} ₽</s>"
                text += "\n"
            
            if normal_price:
                text += f"<b>💳 Без Ozon Card:</b> {normal_price} ₽\n"
            
            if ozon_card_price:
                text += f"<b>🎴 С Ozon Card:</b> {ozon_card_price} ₽\n"
            
            # Название товара
            name = last_check.get("name")
            if name:
                text += f"\n<b>Название:</b> {name}\n"
            
            # Наличие
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
        return "📭 <i>У вас пока нет отслеживаемых артикулов</i>"
    
    text = f"<b>📦 Ваши артикулы ({len(articles)}):</b>\n\n"
    
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
    
    text = "<b>📈 История цен:</b>\n\n"
    
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
            text += f"  💰 {price} ₽"
        if normal_price:
            text += f" | 💳 {normal_price} ₽"
        if ozon_card_price:
            text += f" | 🎴 {ozon_card_price} ₽"
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
    
    text = "<b>📊 Ваша статистика:</b>\n\n"
    text += f"<b>📦 Артикулы:</b>\n"
    text += f"  • Всего: {total_articles}\n"
    text += f"  • Активных: {active_articles}\n\n"
    
    text += f"<b>🔄 Запросы (30 дней):</b>\n"
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
    text = "<b>📋 ОТЧЕТ</b>\n\n"
    
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
        text += f"<b>📊 Статистика:</b>\n"
        text += f"  • Запросов: {report.get('total_requests', 0)}\n"
        text += f"  • Успешных: {report.get('successful_requests', 0)}\n\n"
    
    # Средняя цена за 7 дней
    avg_price_7d = report.get("average_price_7d")
    if avg_price_7d and isinstance(avg_price_7d, dict):
        text += f"<b>💰 Средние цены (7 дней):</b>\n"
        
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
        text += f"  • Точек данных: {data_points}\n"
    
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
    text = f"❌ <b>Ошибка:</b> {error}\n"
    
    if details:
        text += f"\n<i>{details}</i>\n"
    
    text += "\n💡 Попробуйте позже или обратитесь к администратору"
    
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

