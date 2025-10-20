"""
Onboarding Handler

Интерактивное введение для новых пользователей.

Features:
- Пошаговое знакомство с ботом
- Возможность пропустить
- Сохранение прогресса
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from loguru import logger

from keyboards import get_main_menu, get_url_button
from keyboards.inline import InlineKeyboardBuilder, InlineKeyboardButton


router = Router(name="onboarding")


def get_onboarding_keyboard(step: int, total_steps: int):
    """
    Клавиатура для onboarding
    
    Args:
        step: Текущий шаг
        total_steps: Всего шагов
        
    Returns:
        InlineKeyboardMarkup
    """
    builder = InlineKeyboardBuilder()
    
    # Кнопки навигации
    nav_buttons = []
    
    if step > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=f"onboarding_step:{step - 1}"
            )
        )
    
    if step < total_steps:
        nav_buttons.append(
            InlineKeyboardButton(
                text="Далее ▶️",
                callback_data=f"onboarding_step:{step + 1}"
            )
        )
    else:
        nav_buttons.append(
            InlineKeyboardButton(
                text="✅ Начать работу",
                callback_data="onboarding_complete"
            )
        )
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    # Кнопка пропуска
    if step < total_steps:
        builder.row(
            InlineKeyboardButton(
                text="⏩ Пропустить введение",
                callback_data="onboarding_skip"
            )
        )
    
    return builder.as_markup()


def get_onboarding_step_content(step: int) -> tuple[str, str]:
    """
    Получить контент для шага onboarding
    
    Args:
        step: Номер шага (1-4)
        
    Returns:
        Tuple (title, content)
    """
    steps = {
        1: (
            "👋 Добро пожаловать!",
            (
                "<b>Привет! Я - OZON Monitor Bot</b> 🤖\n\n"
                "Я помогу вам отслеживать цены на товары OZON:\n\n"
                "✅ <b>Мониторинг цен</b>\n"
                "   • Цена без Ozon Card\n"
                "   • Цена с Ozon Card\n"
                "   • Средняя цена за 7 дней\n\n"
                "✅ <b>Автоматическое обновление</b>\n"
                "   • Данные обновляются каждые 24 часа\n"
                "   • История изменения цен\n\n"
                "✅ <b>Отчеты и статистика</b>\n"
                "   • Детальные отчеты по артикулам\n"
                "   • Экспорт данных\n\n"
                "<i>Нажмите 'Далее' для продолжения ▶️</i>"
            )
        ),
        2: (
            "📦 Как добавить артикул",
            (
                "<b>Добавление артикула OZON:</b>\n\n"
                "<b>Способ 1: Команда</b>\n"
                "Отправьте: <code>/add 123456789</code>\n\n"
                "<b>Способ 2: Кнопка меню</b>\n"
                "Нажмите '➕ Добавить артикул'\n\n"
                "<b>Способ 3: Просто номер</b>\n"
                "Отправьте номер артикула (5-12 цифр)\n"
                "Бот автоматически распознает его\n\n"
                "💡 <b>Где найти артикул?</b>\n"
                "Артикул - это цифры в URL товара на OZON:\n"
                "<code>ozon.ru/product/<b>123456789</b>/</code>\n\n"
                "📊 <b>После добавления:</b>\n"
                "• Бот автоматически получит данные\n"
                "• Вы увидите цены и наличие\n"
                "• Артикул добавится в ваш список"
            )
        ),
        3: (
            "📊 Отчеты и мониторинг",
            (
                "<b>Просмотр данных:</b>\n\n"
                "<b>📦 Список артикулов</b>\n"
                "Команда: <code>/list</code>\n"
                "или кнопка '📦 Мои артикулы'\n\n"
                "<b>🔍 Проверка артикула</b>\n"
                "Команда: <code>/check 123456789</code>\n"
                "Получить актуальные данные с OZON\n\n"
                "<b>📋 Отчеты</b>\n"
                "• <code>/report 123456789</code> - по артикулу\n"
                "• <code>/report all</code> - по всем\n"
                "• <code>/report user</code> - ваша статистика\n\n"
                "<b>📈 Что в отчете:</b>\n"
                "• Средние цены за 7 дней\n"
                "• История изменений\n"
                "• Статистика запросов\n"
                "• Графики (скоро)"
            )
        ),
        4: (
            "🎯 Полезные советы",
            (
                "<b>Советы по использованию:</b>\n\n"
                "💡 <b>Лимиты</b>\n"
                f"• Максимум артикулов: 50\n"
                f"• Запросов в минуту: 5\n\n"
                "💡 <b>Обновление данных</b>\n"
                "• Автоматически каждые 24 часа\n"
                "• Вручную через кнопку '🔄 Обновить'\n\n"
                "💡 <b>Команды</b>\n"
                "• <code>/help</code> - справка\n"
                "• <code>/stats</code> - статистика\n"
                "• Используйте кнопки меню для быстрого доступа\n\n"
                "💡 <b>Поддержка</b>\n"
                "Есть вопросы? Напишите @admin_username\n\n"
                "<b>✅ Всё готово! Начните с добавления первого артикула</b>"
            )
        )
    }
    
    return steps.get(step, ("", ""))


@router.callback_query(F.data.startswith("onboarding_step:"))
async def callback_onboarding_step(callback: CallbackQuery):
    """Навигация по шагам onboarding"""
    await callback.answer()
    
    step = int(callback.data.split(":")[1])
    total_steps = 4
    
    logger.info(f"👣 User {callback.from_user.id} on onboarding step {step}")
    
    title, content = get_onboarding_step_content(step)
    
    text = f"<b>{title}</b>\n\n{content}\n\n"
    text += f"<i>Шаг {step} из {total_steps}</i>"
    
    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=get_onboarding_keyboard(step, total_steps),
            parse_mode="HTML"
        )
    except Exception as e:
        # Если не удалось отредактировать (например, текст не изменился)
        logger.warning(f"⚠️ Could not edit onboarding message: {e}")


@router.callback_query(F.data == "onboarding_skip")
async def callback_onboarding_skip(callback: CallbackQuery):
    """Пропустить onboarding"""
    await callback.answer("Введение пропущено")
    
    logger.info(f"⏩ User {callback.from_user.id} skipped onboarding")
    
    text = (
        "✅ <b>Введение пропущено</b>\n\n"
        "Вы всегда можете вернуться к справке с помощью команды /help\n\n"
        "Начните работу с добавления артикула:\n"
        "• Нажмите '➕ Добавить артикул'\n"
        "• Или используйте команду <code>/add 123456789</code>"
    )
    
    try:
        await callback.message.edit_text(
            text=text,
            parse_mode="HTML"
        )
    except:
        await callback.message.answer(
            text=text,
            parse_mode="HTML"
        )
    
    # Отправляем главное меню
    await callback.message.answer(
        text="🎯 <b>Главное меню</b>",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "onboarding_complete")
async def callback_onboarding_complete(callback: CallbackQuery):
    """Завершение onboarding"""
    await callback.answer("✅ Введение завершено!")
    
    logger.success(f"✅ User {callback.from_user.id} completed onboarding")
    
    text = (
        "🎉 <b>Отлично! Вы готовы к работе</b>\n\n"
        "Теперь вы можете:\n"
        "• Добавлять артикулы OZON\n"
        "• Отслеживать цены\n"
        "• Генерировать отчеты\n\n"
        "Используйте кнопки меню ниже для навигации ⬇️\n\n"
        "💡 <i>Команда /help всегда доступна для справки</i>"
    )
    
    try:
        await callback.message.edit_text(
            text=text,
            parse_mode="HTML"
        )
    except:
        await callback.message.answer(
            text=text,
            parse_mode="HTML"
        )
    
    # Отправляем главное меню
    await callback.message.answer(
        text="🎯 <b>Главное меню</b>",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )


def get_onboarding_start_keyboard():
    """
    Клавиатура для начала onboarding
    
    Returns:
        InlineKeyboardMarkup
    """
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="🚀 Начать знакомство",
            callback_data="onboarding_step:1"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="⏩ Пропустить",
            callback_data="onboarding_skip"
        )
    )
    
    return builder.as_markup()

