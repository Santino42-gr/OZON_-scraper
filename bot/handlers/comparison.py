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
    get_cancel_keyboard,
    get_report_frequency_keyboard
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
    waiting_for_report_frequency = State()


def validate_article_number(article: str) -> bool:
    """Валидация номера артикула OZON"""
    article = article.strip()
    pattern = r'^\d{5,12}$'
    return bool(re.match(pattern, article))


def escape_html(text: str) -> str:
    """Экранировать HTML спецсимволы"""
    if not text:
        return ""
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;"))


def format_comparison_result(comparison: dict) -> str:
    """
    Форматировать результат сравнения для отображения

    Args:
        comparison: Данные сравнения от API

    Returns:
        Отформатированный текст
    """
    try:
        text = "<b>Результаты сравнения</b>\n\n"

        # Основная информация - извлекаем данные безопасно
        own = comparison.get("own_product") or {}
        # Если own_product это объект Pydantic, преобразуем в dict
        if hasattr(own, 'dict'):
            own = own.dict()
        elif not isinstance(own, dict):
            own = {}
            
        # Конкурент может быть в списке competitors или как competitor_product
        competitor = None
        competitors = comparison.get("competitors", [])
        if competitors and len(competitors) > 0:
            competitor = competitors[0]
        elif comparison.get("competitor_product"):
            competitor = comparison.get("competitor_product")
        
        if competitor:
            # Если competitor это объект Pydantic, преобразуем в dict
            if hasattr(competitor, 'dict'):
                competitor = competitor.dict()
            elif not isinstance(competitor, dict):
                competitor = {}
        else:
            competitor = {}
            
        metrics = comparison.get("metrics") or {}
        # Если metrics это объект Pydantic, преобразуем в dict
        if hasattr(metrics, 'dict'):
            metrics = metrics.dict()
        elif not isinstance(metrics, dict):
            metrics = {}

        # Ваш товар
        text += "<b>Ваш товар:</b>\n"
        own_article = own.get('article_number', 'N/A') if own else 'N/A'
        text += f"   Артикул: {own_article}\n"
        if own.get("name"):
            name = escape_html(str(own.get('name')))
            text += f"   Название: {name}\n"
        own_normal_price = own.get('normal_price') or own.get('price') or 0
        own_card_price = own.get('ozon_card_price') or own_normal_price or 0
        text += f"   Цена: {own_normal_price:,.0f} ₽\n"
        text += f"   С Ozon Card: {own_card_price:,.0f} ₽\n"
        if own.get("rating"):
            text += f"   Рейтинг: {own.get('rating'):.1f} ({own.get('reviews_count', 0)} отзывов)\n"
        text += "\n"

        # Товар конкурента
        if competitor:
            text += "<b>Конкурент:</b>\n"
            comp_article = competitor.get('article_number', 'N/A')
            text += f"   Артикул: {comp_article}\n"
            if competitor.get("name"):
                name = escape_html(str(competitor.get('name')))
                text += f"   Название: {name}\n"
            comp_normal_price = competitor.get('normal_price') or competitor.get('price') or 0
            comp_card_price = competitor.get('ozon_card_price') or comp_normal_price or 0
            text += f"   Цена: {comp_normal_price:,.0f} ₽\n"
            text += f"   С Ozon Card: {comp_card_price:,.0f} ₽\n"
            if competitor.get("rating"):
                text += f"   Рейтинг: {competitor.get('rating'):.1f} ({competitor.get('reviews_count', 0)} отзывов)\n"
            text += "\n"

        # Метрики сравнения
        if metrics:
            text += "<b>Сравнительный анализ:</b>\n\n"

            # Цена - может быть как price или price_difference
            price_diff = metrics.get("price") or metrics.get("price_difference") or {}
            if price_diff:
                # Если это объект Pydantic, преобразуем
                if hasattr(price_diff, 'dict'):
                    price_diff = price_diff.dict()
                if isinstance(price_diff, dict):
                    text += f"<b>Ценовая позиция:</b>\n"
                    abs_diff = price_diff.get("absolute", 0)
                    pct_diff = price_diff.get("percentage", 0)
                    recommendation = price_diff.get("recommendation", "")
                    if abs_diff > 0:
                        text += f"   Ваша цена на {abs_diff:,.0f} ₽ ({pct_diff:.1f}%) выше конкурента\n"
                    elif abs_diff < 0:
                        text += f"   Ваша цена на {abs(-abs_diff):,.0f} ₽ ({abs(pct_diff):.1f}%) ниже конкурента\n"
                    else:
                        text += f"   Цены одинаковые\n"
                    if recommendation:
                        rec_text = escape_html(str(recommendation))
                        text += f"   {rec_text}\n"
                    text += "\n"

            # Рейтинг
            rating_diff = metrics.get("rating") or metrics.get("rating_difference") or {}
            if rating_diff:
                # Если это объект Pydantic, преобразуем
                if hasattr(rating_diff, 'dict'):
                    rating_diff = rating_diff.dict()
                if isinstance(rating_diff, dict):
                    text += f"<b>Рейтинг и отзывы:</b>\n"
                    rating_abs = rating_diff.get("absolute", 0)
                    if rating_abs > 0:
                        text += f"   Ваш рейтинг на {rating_abs:.1f} выше\n"
                    elif rating_abs < 0:
                        text += f"   Ваш рейтинг на {abs(rating_abs):.1f} ниже\n"
                    else:
                        text += f"   Рейтинги одинаковые\n"

                    # Отзывы могут быть в reviews или rating_difference
                    reviews_diff = metrics.get("reviews", {})
                    if isinstance(reviews_diff, dict):
                        reviews_abs = reviews_diff.get("absolute", 0)
                    else:
                        reviews_abs = rating_diff.get("reviews_difference", 0)
                        
                    if reviews_abs != 0:
                        text += f"   Отзывов: {'больше' if reviews_abs > 0 else 'меньше'} на {abs(reviews_abs)}\n"
                    text += "\n"

        # Рекомендации
        recommendations = comparison.get("recommendations", [])
        if not recommendations and metrics:
            # Может быть одна общая рекомендация
            overall_rec = metrics.get("overall_recommendation") or ""
            if overall_rec:
                recommendations = [overall_rec]
                
        if recommendations:
            text += "<b>Рекомендации:</b>\n"
            for i, rec in enumerate(recommendations[:3], 1):  # Первые 3 рекомендации
                # Экранируем рекомендации для безопасного HTML
                rec_text = escape_html(str(rec))
                text += f"   {i}. {rec_text}\n"

        return text

    except Exception as e:
        logger.error(f"Error formatting comparison: {e}")
        import traceback
        logger.error(traceback.format_exc())
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
            "Шаг 1 из 3: Отправьте <b>артикул вашего товара</b>\n\n"
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
            "Шаг 2 из 3: Отправьте <b>артикул конкурента</b>\n\n"
            "📝 <i>Пример: 987654321</i>\n\n"
            "Или нажмите ❌ Отмена"
        ),
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(CompareStates.waiting_for_competitor_article)
async def process_competitor_article(message: Message, state: FSMContext):
    """Обработка ввода артикула конкурента"""

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

    # Сохраняем артикул конкурента и переходим к выбору частоты
    await state.update_data(competitor_article=competitor_article)
    await state.set_state(CompareStates.waiting_for_report_frequency)
    
    await message.answer(
        text=(
            f"✅ Ваш товар: <code>{own_article}</code>\n"
            f"✅ Конкурент: <code>{competitor_article}</code>\n\n"
            "📅 <b>Шаг 3 из 3: Выберите частоту отчетов</b>\n\n"
            "Как часто вы хотите получать обновления цен для этих артикулов?\n\n"
            "• <b>1 раз в день</b> - каждое утро в 09:00\n"
            "• <b>2 раза в день</b> - утром в 09:00 и днем в 15:00"
        ),
        reply_markup=get_report_frequency_keyboard(),
        parse_mode="HTML"
    )


@router.message(CompareStates.waiting_for_report_frequency)
async def process_report_frequency_and_compare(message: Message, state: FSMContext):
    """Обработка выбора частоты отчетов и выполнение сравнения"""

    user = message.from_user

    # Проверка на отмену
    if message.text and message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            text="❌ Сравнение отменено",
            reply_markup=get_main_menu()
        )
        return

    # Определяем частоту по тексту кнопки
    report_frequency = None
    if message.text and ("1️⃣" in message.text or "1 раз" in message.text):
        report_frequency = "once"
    elif message.text and ("2️⃣" in message.text or "2 раза" in message.text):
        report_frequency = "twice"

    if not report_frequency:
        await message.answer(
            text="Пожалуйста, выберите частоту отчетов из предложенных вариантов",
            reply_markup=get_report_frequency_keyboard()
        )
        return

    # Получаем сохраненные артикулы
    data = await state.get_data()
    own_article = data.get("own_article")
    competitor_article = data.get("competitor_article")

    if not own_article or not competitor_article:
        await state.clear()
        await message.answer(
            text=format_error("Ошибка", "Потеряны артикулы. Начните сначала с /compare"),
            parse_mode="HTML"
        )
        return

    try:
        api_client = get_api_client()

        # Получаем пользователя
        user_data = await api_client.get_user_by_telegram_id(user.id)
        user_id = user_data.get("id")

        if not user_id:
            await state.clear()
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

        # Выполняем сравнение с выбранной частотой
        comparison = await api_client.quick_compare(
            user_id=user_id,
            own_article_number=own_article,
            competitor_article_number=competitor_article,
            group_name=f"Сравнение {own_article} vs {competitor_article}",
            report_frequency=report_frequency
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
