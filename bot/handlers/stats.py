"""
Stats Handler

Обработчик команд для просмотра статистики.

Commands:
- /stats - показать статистику пользователя
- Кнопка "📊 Статистика" из главного меню
"""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from loguru import logger

from services.api_client import get_api_client, APIError
from utils.formatters import format_stats, format_error


router = Router(name="stats")


@router.message(Command("stats"))
@router.message(F.text == "📊 Статистика")
async def cmd_stats(message: Message):
    """
    Команда /stats - показать статистику пользователя
    """
    user = message.from_user
    logger.info(f"📊 User {user.id} requested stats")
    
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
        
        # Получаем статистику
        stats = await api_client.get_user_stats(user_id)
        
        # Форматируем статистику
        text = format_stats(stats)
        
        await message.answer(
            text=text,
            parse_mode="HTML"
        )
        
        logger.success(f"✅ Sent stats for user {user.id}")
        
    except APIError as e:
        await message.answer(
            text=format_error("Не удалось получить статистику", str(e)),
            parse_mode="HTML"
        )
        logger.error(f"❌ Error getting stats for user {user.id}: {e}")
    
    except Exception as e:
        await message.answer(
            text=format_error("Произошла непредвиденная ошибка", str(e)),
            parse_mode="HTML"
        )
        logger.error(f"❌ Unexpected error getting stats: {e}")

