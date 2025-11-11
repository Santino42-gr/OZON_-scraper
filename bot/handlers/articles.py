"""
Articles Handler

Обработчик команд для управления артикулами OZON.

Commands:
- /add <артикул> - добавить артикул
- /list - список артикулов
- /check <артикул> - проверить артикул
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
    get_articles_list_keyboard,
    get_article_actions_keyboard,
    get_delete_confirmation_keyboard,
    get_report_frequency_keyboard
)
from services.api_client import get_api_client, APIError, APITimeoutError
from utils.formatters import (
    format_article_info,
    format_article_list,
    format_error,
    truncate_text
)
from config import settings


router = Router(name="articles")


# FSM States для добавления артикула
class AddArticleStates(StatesGroup):
    waiting_for_article_number = State()
    waiting_for_report_frequency = State()


def validate_article_number(article: str) -> bool:
    """
    Валидация номера артикула OZON
    
    Args:
        article: Номер артикула
        
    Returns:
        True если валидный, False иначе
    """
    # Убираем пробелы
    article = article.strip()
    
    # OZON артикулы обычно цифровые, 5-12 символов
    pattern = r'^\d{5,12}$'
    return bool(re.match(pattern, article))


# ==================== Добавление артикула ====================

@router.message(Command("add"))
async def cmd_add_article(message: Message, command: CommandObject, state: FSMContext):
    """
    Команда /add - добавить артикул
    
    Варианты использования:
    - /add - начать процесс добавления
    - /add 123456789 - добавить артикул сразу
    """
    user = message.from_user
    logger.info(f"📦 User {user.id} wants to add article")
    
    # Проверяем аргумент команды
    if command.args:
        article_number = command.args.strip()
        await process_add_article(message, article_number, state)
    else:
        # Запрашиваем артикул
        await state.set_state(AddArticleStates.waiting_for_article_number)
        await message.answer(
            text=(
                "➕ <b>Добавление артикула</b>\n\n"
                "Отправьте номер артикула OZON (только цифры, 5-12 символов)\n\n"
                "📝 <i>Пример: 123456789</i>\n\n"
                "Или нажмите ❌ Отмена"
            ),
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML"
        )


@router.message(F.text == "➕ Добавить артикул")
async def btn_add_article(message: Message, state: FSMContext):
    """Кнопка 'Добавить артикул' из главного меню"""
    await cmd_add_article(message, CommandObject(command="", args=""), state)


@router.message(AddArticleStates.waiting_for_article_number)
async def process_article_number_input(message: Message, state: FSMContext):
    """Обработка ввода номера артикула"""
    
    # Проверка на отмену
    if message.text and message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            text="❌ Добавление артикула отменено",
            reply_markup=get_main_menu()
        )
        return
    
    article_number = message.text.strip() if message.text else ""
    
    # Валидация артикула
    if not validate_article_number(article_number):
        await message.answer(
            text=format_error(
                "Неверный формат артикула",
                "Артикул должен содержать только цифры (5-12 символов)"
            ),
            parse_mode="HTML"
        )
        return
    
    # Сохраняем артикул в состояние и переходим к выбору частоты
    await state.update_data(article_number=article_number)
    await state.set_state(AddArticleStates.waiting_for_report_frequency)
    
    await message.answer(
        text=(
            "📅 <b>Выберите частоту отчетов</b>\n\n"
            "Как часто вы хотите получать обновления цен?\n\n"
            "• <b>1 раз в день</b> - каждое утро в 09:00\n"
            "• <b>2 раза в день</b> - утром в 09:00 и днем в 15:00"
        ),
        reply_markup=get_report_frequency_keyboard(),
        parse_mode="HTML"
    )


@router.message(AddArticleStates.waiting_for_report_frequency)
async def process_report_frequency_input(message: Message, state: FSMContext):
    """Обработка выбора частоты отчетов"""
    
    # Проверка на отмену
    if message.text and message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            text="❌ Добавление артикула отменено",
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
    
    # Получаем артикул из состояния
    data = await state.get_data()
    article_number = data.get("article_number")
    
    if not article_number:
        await state.clear()
        await message.answer(
            text="Ошибка: артикул не найден. Начните заново.",
            reply_markup=get_main_menu()
        )
        return
    
    # Создаем артикул с выбранной частотой
    await process_add_article(message, article_number, state, report_frequency)


async def process_add_article(message: Message, article_number: str, state: FSMContext, report_frequency: str = "once"):
    """
    Обработать добавление артикула
    
    Args:
        message: Сообщение пользователя
        article_number: Номер артикула
        state: FSM состояние
    """
    user = message.from_user
    
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
        
        # Создаем артикул
        loading_msg = await message.answer(
            text="⏳ Добавляю артикул и получаю данные с OZON..."
        )
        
        article = await api_client.create_article(
            user_id=user_id,
            article_number=article_number,
            report_frequency=report_frequency
        )
        
        await loading_msg.delete()
        
        # Очищаем состояние
        await state.clear()
        
        # Форматируем ответ
        text = "✅ <b>Артикул успешно добавлен!</b>\n\n"
        text += format_article_info(article)
        
        await message.answer(
            text=truncate_text(text),
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )
        
        logger.success(f"✅ Article {article_number} added for user {user.id}")
        
    except APITimeoutError as e:
        await state.clear()
        await loading_msg.delete() if 'loading_msg' in locals() else None
        
        error_text = "Таймаут при получении данных с OZON"
        details = "Парсинг товара занял слишком много времени. Попробуйте позже или проверьте правильность артикула."
        
        await message.answer(
            text=format_error(error_text, details),
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )
        
        logger.error(f"⏱️ Timeout adding article for user {user.id}: {e}")
        return
    
    except APIError as e:
        await state.clear()
        await loading_msg.delete() if 'loading_msg' in locals() else None
        
        error_msg = str(e)
        if "already exists" in error_msg.lower() or "уже добавлен" in error_msg.lower():
            # Если артикул уже существует, получаем его и показываем информацию
            try:
                # Получаем список артикулов пользователя
                articles = await api_client.get_user_articles(user_id=user_id, limit=100)
                
                # Ищем нужный артикул
                existing_article = None
                if articles:
                    for article in articles:
                        if article.get("article_number") == article_number:
                            existing_article = article
                            break
                
                if existing_article:
                    # Показываем информацию о существующем артикуле
                    text = "ℹ️ <b>Этот артикул уже добавлен в ваш список</b>\n\n"
                    text += format_article_info(existing_article)
                    
                    await message.answer(
                        text=truncate_text(text),
                        reply_markup=get_main_menu(),
                        parse_mode="HTML"
                    )
                    
                    logger.info(f"ℹ️ Article {article_number} already exists for user {user.id}, showing info")
                else:
                    # Если не нашли в списке, показываем обычное сообщение
                    error_text = "Этот артикул уже добавлен"
                    details = "Проверьте список своих артикулов с помощью /list"
                    
                    await message.answer(
                        text=format_error(error_text, details),
                        reply_markup=get_main_menu(),
                        parse_mode="HTML"
                    )
            except APIError as fetch_error:
                # Если не удалось получить артикул (404 или другая ошибка API), показываем обычное сообщение
                logger.warning(f"Failed to fetch existing article: {fetch_error}")
                error_text = "Этот артикул уже добавлен"
                details = "Проверьте список своих артикулов с помощью /list"
                
                await message.answer(
                    text=format_error(error_text, details),
                    reply_markup=get_main_menu(),
                    parse_mode="HTML"
                )
            except Exception as fetch_error:
                # Если произошла другая ошибка, логируем и показываем сообщение
                logger.error(f"Unexpected error fetching existing article: {fetch_error}")
                error_text = "Этот артикул уже добавлен"
                details = "Проверьте список своих артикулов с помощью /list"
                
                await message.answer(
                    text=format_error(error_text, details),
                    reply_markup=get_main_menu(),
                    parse_mode="HTML"
                )
        elif "maximum" in error_msg.lower() or "limit" in error_msg.lower():
            error_text = f"Достигнут лимит артикулов ({settings.MAX_ARTICLES_PER_USER})"
            details = "Удалите ненужные артикулы перед добавлением новых"
            
            await message.answer(
                text=format_error(error_text, details),
                reply_markup=get_main_menu(),
                parse_mode="HTML"
            )
        else:
            error_text = "Не удалось добавить артикул"
            details = error_msg
            
            await message.answer(
                text=format_error(error_text, details),
                reply_markup=get_main_menu(),
                parse_mode="HTML"
            )
        
        # Логируем только если это не "уже существует" (для него уже залогировано выше)
        if "already exists" not in error_msg.lower() and "уже добавлен" not in error_msg.lower():
            logger.error(f"❌ Error adding article for user {user.id}: {e}")
    
    except Exception as e:
        await state.clear()
        
        await message.answer(
            text=format_error("Произошла непредвиденная ошибка", str(e)),
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )
        
        logger.error(f"❌ Unexpected error adding article: {e}")


# ==================== Список артикулов ====================

@router.message(Command("list"))
@router.message(F.text == "📦 Мои артикулы")
async def cmd_list_articles(message: Message):
    """
    Команда /list - показать список артикулов пользователя
    """
    user = message.from_user
    logger.info(f"📋 User {user.id} requested articles list")
    
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
        
        # Получаем артикулы
        articles = await api_client.get_user_articles(user_id, limit=50)
        
        if not articles:
            await message.answer(
                text=(
                    "📭 <b>У вас пока нет артикулов</b>\n\n"
                    "Добавьте артикул с помощью:\n"
                    "• Команды /add\n"
                    "• Кнопки '➕ Добавить артикул'"
                ),
                reply_markup=get_main_menu(),
                parse_mode="HTML"
            )
            return
        
        # Показываем список с inline кнопками
        text = f"<b>📦 Ваши артикулы ({len(articles)}):</b>\n\n"
        text += "<i>Нажмите на артикул для просмотра деталей</i>"
        
        await message.answer(
            text=text,
            reply_markup=get_articles_list_keyboard(articles, page=0),
            parse_mode="HTML"
        )
        
        logger.info(f"📋 Listed {len(articles)} articles for user {user.id}")
        
    except APIError as e:
        await message.answer(
            text=format_error("Не удалось получить список артикулов", str(e)),
            parse_mode="HTML"
        )
        logger.error(f"❌ Error listing articles for user {user.id}: {e}")
    
    except Exception as e:
        await message.answer(
            text=format_error("Произошла непредвиденная ошибка", str(e)),
            parse_mode="HTML"
        )
        logger.error(f"❌ Unexpected error listing articles: {e}")


# ==================== Проверка артикула ====================

@router.message(Command("check"))
async def cmd_check_article(message: Message, command: CommandObject):
    """
    Команда /check - проверить артикул на OZON
    
    Использование: /check 123456789
    """
    user = message.from_user
    
    if not command.args:
        await message.answer(
            text=(
                "ℹ️ <b>Проверка артикула</b>\n\n"
                "Использование: <code>/check 123456789</code>\n\n"
                "Или выберите артикул из списка /list"
            ),
            parse_mode="HTML"
        )
        return
    
    article_number = command.args.strip()
    
    if not validate_article_number(article_number):
        await message.answer(
            text=format_error(
                "Неверный формат артикула",
                "Артикул должен содержать только цифры (5-12 символов)"
            ),
            parse_mode="HTML"
        )
        return
    
    logger.info(f"🔍 User {user.id} checking article {article_number}")
    
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
            text="⏳ Проверяю артикул на OZON..."
        )
        
        # Получаем артикулы пользователя и ищем нужный
        articles = await api_client.get_user_articles(user_id)
        article_data = next(
            (a for a in articles if a.get("article_number") == article_number),
            None
        )
        
        if not article_data:
            await loading_msg.delete()
            await message.answer(
                text=format_error(
                    "Артикул не найден",
                    f"Артикул {article_number} не добавлен в ваш список.\nИспользуйте /add для добавления"
                ),
                parse_mode="HTML"
            )
            return
        
        article_id = article_data.get("id")
        
        # Проверяем статус артикула
        check_result = await api_client.check_article(article_id)
        
        await loading_msg.delete()
        
        # Форматируем ответ
        text = "🔍 <b>Результат проверки</b>\n\n"
        text += format_article_info(check_result)
        
        await message.answer(
            text=truncate_text(text),
            reply_markup=get_article_actions_keyboard(article_id),
            parse_mode="HTML"
        )
        
        logger.success(f"✅ Checked article {article_number} for user {user.id}")
        
    except APIError as e:
        await message.answer(
            text=format_error("Не удалось проверить артикул", str(e)),
            parse_mode="HTML"
        )
        logger.error(f"❌ Error checking article for user {user.id}: {e}")
    
    except Exception as e:
        await message.answer(
            text=format_error("Произошла непредвиденная ошибка", str(e)),
            parse_mode="HTML"
        )
        logger.error(f"❌ Unexpected error checking article: {e}")


# ==================== Callback Handlers ====================

@router.callback_query(F.data.startswith("article_view:"))
async def callback_article_view(callback: CallbackQuery):
    """Просмотр деталей артикула (из списка)"""
    await callback.answer()
    
    article_id = callback.data.split(":")[1]
    logger.info(f"👁️ User {callback.from_user.id} viewing article {article_id}")
    
    try:
        api_client = get_api_client()
        
        # Получаем пользователя
        user_data = await api_client.get_user_by_telegram_id(callback.from_user.id)
        user_id = user_data.get("id")
        
        # Получаем артикулы и находим нужный
        articles = await api_client.get_user_articles(user_id)
        article = next((a for a in articles if a.get("id") == article_id), None)
        
        if not article:
            await callback.message.answer(
                text=format_error("Артикул не найден"),
                parse_mode="HTML"
            )
            return
        
        # Получаем предыдущие цены из истории (за последние 2 дня)
        previous_prices = None
        try:
            price_history = await api_client.get_article_price_history(article_id, days=2)
            logger.debug(f"Price history response: {price_history}")
            
            if price_history and price_history.get("history"):
                history = price_history.get("history", [])
                logger.debug(f"Found {len(history)} history records")
                
                # История отсортирована по убыванию даты (DESC), первая запись - самая новая
                # Нужно найти предыдущую запись (не самую новую)
                if len(history) >= 2:
                    # Берем вторую запись как предыдущую
                    prev_record = history[1]
                    previous_prices = {
                        "normal_price": prev_record.get("normal_price"),
                        "ozon_card_price": prev_record.get("ozon_card_price")
                    }
                    logger.debug(f"Using previous prices from history[1]: {previous_prices}")
                elif len(history) == 1:
                    # Если только одна запись, возможно это первая запись
                    # Попробуем использовать её, но лучше сравнить даты
                    prev_record = history[0]
                    # Проверяем, не является ли это текущей ценой
                    current_normal = article.get("normal_price")
                    current_card = article.get("ozon_card_price")
                    
                    # Если цены отличаются, используем как предыдущую
                    if (prev_record.get("normal_price") != current_normal or 
                        prev_record.get("ozon_card_price") != current_card):
                        previous_prices = {
                            "normal_price": prev_record.get("normal_price"),
                            "ozon_card_price": prev_record.get("ozon_card_price")
                        }
                        logger.debug(f"Using previous prices from single history record: {previous_prices}")
            
            # Если истории нет, пытаемся использовать last_check_data как fallback
            if not previous_prices:
                last_check = article.get("last_check_data")
                if last_check and isinstance(last_check, dict):
                    # Используем цены из last_check_data как предыдущие
                    prev_normal = last_check.get("normal_price")
                    prev_card = last_check.get("ozon_card_price")
                    current_normal = article.get("normal_price")
                    current_card = article.get("ozon_card_price")
                    
                    # Используем только если цены отличаются от текущих
                    if (prev_normal and prev_normal != current_normal) or (prev_card and prev_card != current_card):
                        previous_prices = {
                            "normal_price": prev_normal,
                            "ozon_card_price": prev_card
                        }
                        logger.debug(f"Using previous prices from last_check_data: {previous_prices}")
        except Exception as e:
            logger.warning(f"Could not fetch price history for article {article_id}: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            # Пробуем fallback на last_check_data
            last_check = article.get("last_check_data")
            if last_check and isinstance(last_check, dict):
                prev_normal = last_check.get("normal_price")
                prev_card = last_check.get("ozon_card_price")
                current_normal = article.get("normal_price")
                current_card = article.get("ozon_card_price")
                
                if (prev_normal and prev_normal != current_normal) or (prev_card and prev_card != current_card):
                    previous_prices = {
                        "normal_price": prev_normal,
                        "ozon_card_price": prev_card
                    }
        
        # Форматируем информацию
        text = format_article_info(article, previous_prices=previous_prices)
        
        await callback.message.answer(
            text=truncate_text(text),
            reply_markup=get_article_actions_keyboard(article_id),
            parse_mode="HTML"
        )
        
    except Exception as e:
        await callback.message.answer(
            text=format_error("Не удалось получить данные артикула", str(e)),
            parse_mode="HTML"
        )
        logger.error(f"❌ Error viewing article: {e}")


@router.callback_query(F.data.startswith("article_update:"))
async def callback_article_update(callback: CallbackQuery):
    """Обновить данные артикула"""
    await callback.answer("⏳ Обновляю данные...")
    
    article_id = callback.data.split(":")[1]
    logger.info(f"🔄 User {callback.from_user.id} updating article {article_id}")
    
    try:
        api_client = get_api_client()
        
        # Обновляем артикул
        article = await api_client.update_article(article_id)
        
        # Получаем предыдущие цены из истории (за последние 2 дня)
        previous_prices = None
        try:
            price_history = await api_client.get_article_price_history(article_id, days=2)
            logger.debug(f"Price history response: {price_history}")
            
            if price_history and price_history.get("history"):
                history = price_history.get("history", [])
                logger.debug(f"Found {len(history)} history records")
                
                # История отсортирована по убыванию даты (DESC), первая запись - самая новая
                # Нужно найти предыдущую запись (не самую новую)
                if len(history) >= 2:
                    # Берем вторую запись как предыдущую
                    prev_record = history[1]
                    previous_prices = {
                        "normal_price": prev_record.get("normal_price"),
                        "ozon_card_price": prev_record.get("ozon_card_price")
                    }
                    logger.debug(f"Using previous prices from history[1]: {previous_prices}")
                elif len(history) == 1:
                    # Если только одна запись, возможно это первая запись
                    # Попробуем использовать её, но лучше сравнить даты
                    prev_record = history[0]
                    # Проверяем, не является ли это текущей ценой
                    current_normal = article.get("normal_price")
                    current_card = article.get("ozon_card_price")
                    
                    # Если цены отличаются, используем как предыдущую
                    if (prev_record.get("normal_price") != current_normal or 
                        prev_record.get("ozon_card_price") != current_card):
                        previous_prices = {
                            "normal_price": prev_record.get("normal_price"),
                            "ozon_card_price": prev_record.get("ozon_card_price")
                        }
                        logger.debug(f"Using previous prices from single history record: {previous_prices}")
            
            # Если истории нет, пытаемся использовать last_check_data как fallback
            if not previous_prices:
                last_check = article.get("last_check_data")
                if last_check and isinstance(last_check, dict):
                    # Используем цены из last_check_data как предыдущие
                    prev_normal = last_check.get("normal_price")
                    prev_card = last_check.get("ozon_card_price")
                    current_normal = article.get("normal_price")
                    current_card = article.get("ozon_card_price")
                    
                    # Используем только если цены отличаются от текущих
                    if (prev_normal and prev_normal != current_normal) or (prev_card and prev_card != current_card):
                        previous_prices = {
                            "normal_price": prev_normal,
                            "ozon_card_price": prev_card
                        }
                        logger.debug(f"Using previous prices from last_check_data: {previous_prices}")
        except Exception as e:
            logger.warning(f"Could not fetch price history for article {article_id}: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            # Пробуем fallback на last_check_data
            last_check = article.get("last_check_data")
            if last_check and isinstance(last_check, dict):
                prev_normal = last_check.get("normal_price")
                prev_card = last_check.get("ozon_card_price")
                current_normal = article.get("normal_price")
                current_card = article.get("ozon_card_price")
                
                if (prev_normal and prev_normal != current_normal) or (prev_card and prev_card != current_card):
                    previous_prices = {
                        "normal_price": prev_normal,
                        "ozon_card_price": prev_card
                    }
        
        # Форматируем ответ
        text = "✅ <b>Данные обновлены</b>\n\n"
        text += format_article_info(article, previous_prices=previous_prices)
        
        await callback.message.edit_text(
            text=truncate_text(text),
            reply_markup=get_article_actions_keyboard(article_id),
            parse_mode="HTML"
        )
        
        logger.success(f"✅ Updated article {article_id}")
        
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)
        logger.error(f"❌ Error updating article: {e}")


@router.callback_query(F.data.startswith("article_delete:"))
async def callback_article_delete(callback: CallbackQuery):
    """Запрос подтверждения удаления"""
    await callback.answer()
    
    article_id = callback.data.split(":")[1]
    
    await callback.message.edit_text(
        text=(
            "⚠️ <b>Удаление артикула</b>\n\n"
            "Вы уверены, что хотите удалить этот артикул?\n"
            "Это действие нельзя отменить."
        ),
        reply_markup=get_delete_confirmation_keyboard(article_id),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("article_delete_confirm:"))
async def callback_article_delete_confirm(callback: CallbackQuery):
    """Подтверждение удаления артикула"""
    await callback.answer("⏳ Удаляю...")
    
    article_id = callback.data.split(":")[1]
    logger.info(f"🗑️ User {callback.from_user.id} deleting article {article_id}")
    
    try:
        api_client = get_api_client()
        
        # Получаем пользователя
        user_data = await api_client.get_user_by_telegram_id(callback.from_user.id)
        user_id = user_data.get("id")
        
        # Удаляем артикул
        await api_client.delete_article(article_id, user_id)
        
        await callback.message.edit_text(
            text="✅ <b>Артикул успешно удален</b>",
            parse_mode="HTML"
        )
        
        logger.success(f"✅ Deleted article {article_id}")
        
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)
        logger.error(f"❌ Error deleting article: {e}")


@router.callback_query(F.data == "article_delete_cancel")
async def callback_article_delete_cancel(callback: CallbackQuery):
    """Отмена удаления"""
    await callback.answer("Удаление отменено")
    
    await callback.message.edit_text(
        text="❌ Удаление отменено",
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("articles_page:"))
async def callback_articles_page(callback: CallbackQuery):
    """Пагинация списка артикулов"""
    await callback.answer()
    
    page = int(callback.data.split(":")[1])
    
    try:
        api_client = get_api_client()
        
        # Получаем пользователя
        user_data = await api_client.get_user_by_telegram_id(callback.from_user.id)
        user_id = user_data.get("id")
        
        # Получаем артикулы
        articles = await api_client.get_user_articles(user_id, limit=50)
        
        # Обновляем клавиатуру
        await callback.message.edit_reply_markup(
            reply_markup=get_articles_list_keyboard(articles, page=page)
        )
        
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)
        logger.error(f"❌ Error changing page: {e}")


@router.callback_query(F.data == "articles_refresh")
async def callback_articles_refresh(callback: CallbackQuery):
    """Обновить список артикулов"""
    await callback.answer("🔄 Обновляю...")
    
    try:
        api_client = get_api_client()
        
        # Получаем пользователя
        user_data = await api_client.get_user_by_telegram_id(callback.from_user.id)
        user_id = user_data.get("id")
        
        # Получаем артикулы
        articles = await api_client.get_user_articles(user_id, limit=50)
        
        # Обновляем сообщение
        text = f"<b>📦 Ваши артикулы ({len(articles)}):</b>\n\n"
        text += "<i>Нажмите на артикул для просмотра деталей</i>"
        
        await callback.message.edit_text(
            text=text,
            reply_markup=get_articles_list_keyboard(articles, page=0),
            parse_mode="HTML"
        )
        
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)
        logger.error(f"❌ Error refreshing articles: {e}")


@router.callback_query(F.data == "noop")
async def callback_noop(callback: CallbackQuery):
    """No-op callback (для кнопок-индикаторов)"""
    await callback.answer()

