"""
Inline Keyboards

Inline клавиатуры для Telegram бота.
"""

from typing import List, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_article_actions_keyboard(article_id: str) -> InlineKeyboardMarkup:
    """
    Клавиатура действий с артикулом
    
    Args:
        article_id: UUID артикула
        
    Returns:
        InlineKeyboardMarkup с действиями
    """
    builder = InlineKeyboardBuilder()
    
    # Первая строка
    builder.row(
        InlineKeyboardButton(
            text="🔄 Обновить",
            callback_data=f"article_update:{article_id}"
        ),
        InlineKeyboardButton(
            text="📊 Отчет",
            callback_data=f"article_report:{article_id}"
        )
    )
    
    # Вторая строка
    builder.row(
        InlineKeyboardButton(
            text="🗑️ Удалить",
            callback_data=f"article_delete:{article_id}"
        )
    )
    
    return builder.as_markup()


def get_articles_list_keyboard(
    articles: List[dict],
    page: int = 0,
    page_size: int = 5
) -> InlineKeyboardMarkup:
    """
    Клавиатура со списком артикулов (пагинация)
    
    Args:
        articles: Список артикулов
        page: Номер страницы
        page_size: Размер страницы
        
    Returns:
        InlineKeyboardMarkup со списком
    """
    builder = InlineKeyboardBuilder()
    
    # Артикулы на текущей странице
    start_idx = page * page_size
    end_idx = start_idx + page_size
    page_articles = articles[start_idx:end_idx]
    
    for article in page_articles:
        status_emoji = "✅" if article.get("status") == "active" else "❌"
        article_number = article.get("article_number", "N/A")
        
        # Добавляем СПП Общий если доступен
        spp_total = article.get("spp_total")
        spp_text = ""
        if spp_total is not None:
            spp_text = f" | СПП: {spp_total:.1f}%"
        
        # Формируем текст кнопки (ограничиваем длину)
        button_text = f"{status_emoji} {article_number}{spp_text}"
        # Telegram ограничивает длину текста кнопки до 64 символов
        if len(button_text) > 60:
            button_text = f"{status_emoji} {article_number}"
        
        builder.row(
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"article_view:{article['id']}"
            )
        )
    
    # Кнопки навигации
    nav_buttons = []
    
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=f"articles_page:{page - 1}"
            )
        )
    
    # Показываем номер страницы
    total_pages = (len(articles) + page_size - 1) // page_size
    nav_buttons.append(
        InlineKeyboardButton(
            text=f"📄 {page + 1}/{total_pages}",
            callback_data="noop"
        )
    )
    
    if end_idx < len(articles):
        nav_buttons.append(
            InlineKeyboardButton(
                text="Вперед ▶️",
                callback_data=f"articles_page:{page + 1}"
            )
        )
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    # Кнопка обновления
    builder.row(
        InlineKeyboardButton(
            text="🔄 Обновить список",
            callback_data="articles_refresh"
        )
    )
    
    return builder.as_markup()


def get_delete_confirmation_keyboard(article_id: str) -> InlineKeyboardMarkup:
    """
    Клавиатура подтверждения удаления
    
    Args:
        article_id: UUID артикула
        
    Returns:
        InlineKeyboardMarkup с подтверждением
    """
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="✅ Да, удалить",
            callback_data=f"article_delete_confirm:{article_id}"
        ),
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="article_delete_cancel"
        )
    )
    
    return builder.as_markup()


def get_back_button(callback_data: str = "back") -> InlineKeyboardMarkup:
    """
    Клавиатура с кнопкой "Назад"
    
    Args:
        callback_data: Callback data для кнопки
        
    Returns:
        InlineKeyboardMarkup с кнопкой назад
    """
    builder = InlineKeyboardBuilder()
    
    builder.add(
        InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=callback_data
        )
    )
    
    return builder.as_markup()


def get_url_button(text: str, url: str) -> InlineKeyboardMarkup:
    """
    Клавиатура с URL кнопкой
    
    Args:
        text: Текст кнопки
        url: URL для перехода
        
    Returns:
        InlineKeyboardMarkup с URL кнопкой
    """
    builder = InlineKeyboardBuilder()
    
    builder.add(
        InlineKeyboardButton(
            text=text,
            url=url
        )
    )
    
    return builder.as_markup()

