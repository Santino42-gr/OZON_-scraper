"""
Comparison Handler

Обработчик команд для сравнения товаров с конкурентами.

Commands:
- /compare - сравнить свой товар с конкурентом
- Кнопки меню для управления
"""

import re
from typing import Optional

from aiogram import Router, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from loguru import logger

from keyboards import (
    get_main_menu,
    get_cancel_keyboard
)
from services.api_client import get_api_client, APIError
from utils.formatters import (
    format_error,
    truncate_text
)


router = Router(name="comparison")


# FSM States для сравнения
class CompareStates(StatesGroup):
    waiting_for_own_article = State()
    waiting_for_competitor_article = State()


def validate_article_number(article: str) -> bool:
    """Валидация номера артикула OZON"""
    article = article.strip()
    pattern = r'^\d{5,12}$'
    return bool(re.match(pattern, article))


def format_comparison_result(comparison: dict) -> str:
    """
    Форматировать результат сравнения для отображения

    Args:
        comparison: Данные сравнения от API

    Returns:
        Отформатированный текст
    """
    try:
        text = "🔥 <b>Результаты сравнения</b>\n\n"

        # Основная информация
        own = comparison.get("own_product", {})
        competitor = comparison.get("competitor_product", {})
        metrics = comparison.get("metrics", {})

        # Ваш товар
        text += "📦 <b>Ваш товар:</b>\n"
        text += f"   Артикул: {own.get('article_number', 'N/A')}\n"
        if own.get("name"):
            text += f"   Название: {own.get('name')}\n"
        text += f"   💰 Цена: {own.get('normal_price', 0):,.0f} ₽\n"
        text += f"   💳 С Ozon Card: {own.get('ozon_card_price', 0):,.0f} ₽\n"
        if own.get("rating"):
            text += f"   ⭐ Рейтинг: {own.get('rating'):.1f} ({own.get('reviews_count', 0)} отзывов)\n"
        text += "\n"

        # Товар конкурента
        text += "🎯 <b>Конкурент:</b>\n"
        text += f"   Артикул: {competitor.get('article_number', 'N/A')}\n"
        if competitor.get("name"):
            text += f"   Название: {competitor.get('name')}\n"
        text += f"   💰 Цена: {competitor.get('normal_price', 0):,.0f} ₽\n"
        text += f"   💳 С Ozon Card: {competitor.get('ozon_card_price', 0):,.0f} ₽\n"
        if competitor.get("rating"):
            text += f"   ⭐ Рейтинг: {competitor.get('rating'):.1f} ({competitor.get('reviews_count', 0)} отзывов)\n"
        text += "\n"

        # Метрики сравнения
        text += "📊 <b>Сравнительный анализ:</b>\n\n"

        # Цена
        price_diff = metrics.get("price_difference", {})
        if price_diff:
            text += f"💵 <b>Ценовая позиция:</b>\n"
            abs_diff = price_diff.get("absolute", 0)
            pct_diff = price_diff.get("percentage", 0)
            if abs_diff > 0:
                text += f"   Ваша цена на {abs_diff:,.0f} ₽ ({pct_diff:.1f}%) выше конкурента\n"
            elif abs_diff < 0:
                text += f"   Ваша цена на {abs(-abs_diff):,.0f} ₽ ({abs(pct_diff):.1f}%) ниже конкурента ✅\n"
            else:
                text += f"   Цены одинаковые\n"
            text += "\n"

        # Рейтинг
        rating_diff = metrics.get("rating_difference", {})
        if rating_diff:
            text += f"⭐ <b>Рейтинг и отзывы:</b>\n"
            rating_abs = rating_diff.get("absolute", 0)
            if rating_abs > 0:
                text += f"   Ваш рейтинг на {rating_abs:.1f} выше ✅\n"
            elif rating_abs < 0:
                text += f"   Ваш рейтинг на {abs(rating_abs):.1f} ниже\n"
            else:
                text += f"   Рейтинги одинаковые\n"

            reviews_diff = rating_diff.get("reviews_difference", 0)
            if reviews_diff != 0:
                text += f"   Отзывов: {'больше' if reviews_diff > 0 else 'меньше'} на {abs(reviews_diff)}\n"
            text += "\n"

        # Индекс конкурентоспособности
        competitiveness = comparison.get("competitiveness_index")
        if competitiveness:
            text += f"🎯 <b>Индекс конкурентоспособности:</b> {competitiveness:.1f}/100\n"

            grade = comparison.get("grade", "")
            grade_emoji = {
                "A+": "🏆", "A": "🥇", "B": "🥈",
                "C": "🥉", "D": "⚠️", "F": "❌"
            }.get(grade, "")

            if grade:
                text += f"   Оценка: {grade_emoji} <b>{grade}</b>\n"
            text += "\n"

        # Рекомендации
        recommendations = comparison.get("recommendations", [])
        if recommendations:
            text += "💡 <b>Рекомендации:</b>\n"
            for i, rec in enumerate(recommendations[:3], 1):  # Первые 3 рекомендации
                text += f"   {i}. {rec}\n"

        return text

    except Exception as e:
        logger.error(f"Error formatting comparison: {e}")
        return "Результаты сравнения получены, но произошла ошибка форматирования"


# ==================== Сравнение товаров ====================

@router.message(Command("compare"))
async def cmd_compare(message: Message, command: CommandObject, state: FSMContext):
    """
    Команда /compare - сравнить свой товар с конкурентом

    Использование:
    - /compare - начать процесс сравнения
    """
    user = message.from_user
    logger.info(f"⚖️ User {user.id} wants to compare products")

    await state.set_state(CompareStates.waiting_for_own_article)
    await message.answer(
        text=(
            "⚖️ <b>Сравнение с конкурентом</b>\n\n"
            "Шаг 1 из 2: Отправьте <b>артикул вашего товара</b>\n\n"
            "📝 <i>Пример: 123456789</i>\n\n"
            "Или нажмите ❌ Отмена"
        ),
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(F.text == "⚖️ Сравнить товары")
async def btn_compare(message: Message, state: FSMContext):
    """Кнопка 'Сравнить товары' из главного меню"""
    await cmd_compare(message, CommandObject(command="", args=""), state)


@router.message(CompareStates.waiting_for_own_article)
async def process_own_article(message: Message, state: FSMContext):
    """Обработка ввода своего артикула"""

    # Проверка на отмену
    if message.text and message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            text="❌ Сравнение отменено",
            reply_markup=get_main_menu()
        )
        return

    article_number = message.text.strip() if message.text else ""

    # Валидация
    if not validate_article_number(article_number):
        await message.answer(
            text=format_error(
                "Неверный формат артикула",
                "Артикул должен содержать только цифры (5-12 символов)"
            ),
            parse_mode="HTML"
        )
        return

    # Сохраняем артикул в состоянии
    await state.update_data(own_article=article_number)

    # Переходим к следующему шагу
    await state.set_state(CompareStates.waiting_for_competitor_article)
    await message.answer(
        text=(
            f"✅ Ваш товар: <code>{article_number}</code>\n\n"
            "Шаг 2 из 2: Отправьте <b>артикул конкурента</b>\n\n"
            "📝 <i>Пример: 987654321</i>\n\n"
            "Или нажмите ❌ Отмена"
        ),
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(CompareStates.waiting_for_competitor_article)
async def process_competitor_article(message: Message, state: FSMContext):
    """Обработка ввода артикула конкурента и выполнение сравнения"""

    user = message.from_user

    # Проверка на отмену
    if message.text and message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            text="❌ Сравнение отменено",
            reply_markup=get_main_menu()
        )
        return

    competitor_article = message.text.strip() if message.text else ""

    # Валидация
    if not validate_article_number(competitor_article):
        await message.answer(
            text=format_error(
                "Неверный формат артикула",
                "Артикул должен содержать только цифры (5-12 символов)"
            ),
            parse_mode="HTML"
        )
        return

    # Получаем сохраненный артикул
    data = await state.get_data()
    own_article = data.get("own_article")

    if not own_article:
        await state.clear()
        await message.answer(
            text=format_error("Ошибка", "Потерян артикул вашего товара. Начните сначала с /compare"),
            parse_mode="HTML"
        )
        return

    # Проверка что артикулы разные
    if own_article == competitor_article:
        await message.answer(
            text=format_error(
                "Одинаковые артикулы",
                "Артикул конкурента должен отличаться от вашего"
            ),
            parse_mode="HTML"
        )
        return

    try:
        api_client = get_api_client()

        # Получаем пользователя
        user_data = await api_client.get_user_by_telegram_id(user.id)
        user_id = user_data.get("id")

        if not user_id:
            await message.answer(
                text=format_error(
                    "Пользователь не найден",
                    "Используйте /start для регистрации"
                ),
                parse_mode="HTML"
            )
            return

        # Отправляем "typing..."
        await message.bot.send_chat_action(message.chat.id, "typing")

        loading_msg = await message.answer(
            text="⏳ Сравниваю товары и получаю данные с OZON...\n"
                 "Это может занять до 30 секунд."
        )

        # Выполняем сравнение
        comparison = await api_client.quick_compare(
            user_id=user_id,
            own_article_number=own_article,
            competitor_article_number=competitor_article,
            group_name=f"Сравнение {own_article} vs {competitor_article}"
        )

        await loading_msg.delete()

        # Очищаем состояние
        await state.clear()

        # Форматируем и отправляем результат
        result_text = format_comparison_result(comparison)

        await message.answer(
            text=truncate_text(result_text),
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )

        logger.success(f"✅ Comparison completed for user {user.id}: {own_article} vs {competitor_article}")

    except APIError as e:
        await state.clear()

        error_msg = str(e)
        if "not found" in error_msg.lower():
            error_text = "Один из товаров не найден на OZON"
            details = "Проверьте правильность артикулов"
        else:
            error_text = "Не удалось выполнить сравнение"
            details = error_msg

        await message.answer(
            text=format_error(error_text, details),
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )

        logger.error(f"❌ Error comparing products for user {user.id}: {e}")

    except Exception as e:
        await state.clear()

        await message.answer(
            text=format_error("Произошла непредвиденная ошибка", str(e)),
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )

        logger.error(f"❌ Unexpected error comparing products: {e}")
