"""
Reply Keyboards

Обычные клавиатуры (Reply) для Telegram бота.
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_main_menu() -> ReplyKeyboardMarkup:
    """
    Главное меню бота

    Returns:
        ReplyKeyboardMarkup с основными командами
    """
    builder = ReplyKeyboardBuilder()

    # Первая строка
    builder.row(
        KeyboardButton(text="📦 Мои артикулы"),
        KeyboardButton(text="➕ Добавить артикул")
    )

    # Вторая строка
    builder.row(
        KeyboardButton(text="⚖️ Сравнить товары"),
        KeyboardButton(text="📊 Статистика")
    )

    # Третья строка
    builder.row(
        KeyboardButton(text="⚙️ Настройки"),
        KeyboardButton(text="ℹ️ Помощь")
    )

    return builder.as_markup(
        resize_keyboard=True,
        input_field_placeholder="Выберите действие..."
    )


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавиатура отмены
    
    Returns:
        ReplyKeyboardMarkup с кнопкой отмены
    """
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="❌ Отмена"))
    
    return builder.as_markup(
        resize_keyboard=True
    )


def get_confirmation_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавиатура подтверждения
    
    Returns:
        ReplyKeyboardMarkup с кнопками Да/Нет
    """
    builder = ReplyKeyboardBuilder()
    
    builder.row(
        KeyboardButton(text="✅ Да"),
        KeyboardButton(text="❌ Нет")
    )
    
    return builder.as_markup(
        resize_keyboard=True
    )

