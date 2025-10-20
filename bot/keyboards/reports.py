"""
Reports Keyboards

Inline клавиатуры для отчетов.
"""

from typing import List, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_report_type_selection_keyboard():
    """
    Клавиатура выбора типа отчета
    
    Returns:
        InlineKeyboardMarkup
    """
    builder = InlineKeyboardBuilder()
    
    # Типы отчетов
    builder.row(
        InlineKeyboardButton(
            text="📦 По артикулу",
            callback_data="report_type:article"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="📋 По всем артикулам",
            callback_data="report_type:all"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="👤 Моя статистика",
            callback_data="report_type:user"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="report_cancel"
        )
    )
    
    return builder.as_markup()


def get_report_period_keyboard(report_type: str):
    """
    Клавиатура выбора периода отчета
    
    Args:
        report_type: Тип отчета (article, all, user)
        
    Returns:
        InlineKeyboardMarkup
    """
    builder = InlineKeyboardBuilder()
    
    # Периоды
    builder.row(
        InlineKeyboardButton(
            text="7 дней",
            callback_data=f"report_period:{report_type}:7"
        ),
        InlineKeyboardButton(
            text="14 дней",
            callback_data=f"report_period:{report_type}:14"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="30 дней",
            callback_data=f"report_period:{report_type}:30"
        ),
        InlineKeyboardButton(
            text="90 дней",
            callback_data=f"report_period:{report_type}:90"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="report_menu"
        )
    )
    
    return builder.as_markup()


def get_report_export_keyboard(report_id: Optional[str] = None):
    """
    Клавиатура экспорта отчета
    
    Args:
        report_id: ID отчета (опционально)
        
    Returns:
        InlineKeyboardMarkup
    """
    builder = InlineKeyboardBuilder()
    
    if report_id:
        builder.row(
            InlineKeyboardButton(
                text="📥 Скачать CSV",
                callback_data=f"report_export:csv:{report_id}"
            ),
            InlineKeyboardButton(
                text="📥 Скачать XLSX",
                callback_data=f"report_export:xlsx:{report_id}"
            )
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text="📥 Экспорт CSV",
                callback_data="report_export:csv"
            ),
            InlineKeyboardButton(
                text="📥 Экспорт XLSX",
                callback_data="report_export:xlsx"
            )
        )
    
    return builder.as_markup()

