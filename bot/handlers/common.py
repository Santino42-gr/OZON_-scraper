"""
Common Handlers

Обработчики общих команд и кнопок меню.
"""

from aiogram import Router, F
from aiogram.types import Message
from loguru import logger

from keyboards import get_main_menu


router = Router(name="common")


@router.message(F.text == "⚙️ Настройки")
async def btn_settings(message: Message):
    """
    Кнопка 'Настройки' из главного меню
    
    TODO: Реализовать настройки
    """
    logger.info(f"⚙️ User {message.from_user.id} opened settings")
    
    text = (
        "⚙️ <b>Настройки</b>\n\n"
        "🚧 <i>Раздел в разработке</i>\n\n"
        "Скоро здесь будут доступны:\n"
        "• Уведомления о изменениях цен\n"
        "• Частота проверок\n"
        "• Формат отчетов\n"
        "• Язык интерфейса\n"
        "• Экспорт данных"
    )
    
    await message.answer(
        text=text,
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )


@router.message(F.text.startswith("/"))
async def unknown_command(message: Message):
    """
    Обработчик неизвестных команд
    
    Fallback на /help
    """
    logger.warning(f"❓ Unknown command from user {message.from_user.id}: {message.text}")
    
    text = (
        "❓ <b>Неизвестная команда</b>\n\n"
        f"Команда <code>{message.text}</code> не найдена.\n\n"
        "Используйте /help для просмотра доступных команд"
    )
    
    await message.answer(
        text=text,
        parse_mode="HTML"
    )


@router.message(F.text)
async def text_message_handler(message: Message):
    """
    Обработчик произвольных текстовых сообщений
    
    Проверяем, не артикул ли это
    """
    text = message.text.strip()
    
    # Проверяем, похоже ли на артикул (только цифры)
    if text.isdigit() and 5 <= len(text) <= 12:
        logger.info(f"🔍 User {message.from_user.id} sent potential article number: {text}")
        
        await message.answer(
            text=(
                f"💡 <b>Похоже на артикул OZON</b>\n\n"
                f"Артикул: <code>{text}</code>\n\n"
                f"Выберите действие:\n"
                f"• <code>/add {text}</code> - добавить артикул\n"
                f"• <code>/check {text}</code> - проверить артикул\n"
                f"• <code>/report {text}</code> - сгенерировать отчет"
            ),
            parse_mode="HTML"
        )
    else:
        # Просто игнорируем
        logger.debug(f"💬 Text message from user {message.from_user.id}: {text[:50]}")

