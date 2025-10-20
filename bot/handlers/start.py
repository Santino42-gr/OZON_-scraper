"""
Start Command Handler

Обработчик команды /start - первый контакт пользователя с ботом.
"""

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from loguru import logger

from keyboards import get_main_menu
from services.api_client import get_api_client
from handlers.onboarding import get_onboarding_start_keyboard


router = Router(name="start")


# Отслеживание новых пользователей
_seen_users = set()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """
    Обработчик команды /start
    
    Регистрирует пользователя в системе и показывает главное меню.
    """
    user = message.from_user
    
    logger.info(f"👤 User started bot: {user.id} (@{user.username})")
    
    # Проверяем, новый ли это пользователь
    is_new_user = user.id not in _seen_users
    
    try:
        # Регистрируем пользователя в Backend
        api_client = get_api_client()
        
        user_data = await api_client.register_user(
            telegram_id=user.id,
            telegram_username=user.username
        )
        
        logger.success(f"✅ User registered/updated: {user.id}")
        
        # Добавляем в список seen
        _seen_users.add(user.id)
        
        # Для новых пользователей показываем onboarding
        if is_new_user:
            welcome_text = (
                f"👋 <b>Привет, {user.first_name}!</b>\n\n"
                f"Я - <b>OZON Monitor Bot</b> 🤖\n\n"
                f"Я помогу вам отслеживать цены на товары OZON:\n"
                f"• 💰 Мониторинг цен\n"
                f"• 📊 История изменений\n"
                f"• 📈 Отчеты и статистика\n\n"
                f"Хотите узнать подробнее?"
            )
            
            await message.answer(
                text=welcome_text,
                reply_markup=get_onboarding_start_keyboard(),
                parse_mode="HTML"
            )
        else:
            # Для возвращающихся пользователей - просто приветствие
            welcome_text = (
                f"👋 С возвращением, {user.first_name}!\n\n"
                f"Используйте кнопки меню ниже для работы ⬇️"
            )
            
            await message.answer(
                text=welcome_text,
                reply_markup=get_main_menu(),
                parse_mode="HTML"
            )
        
    except Exception as e:
        logger.error(f"❌ Error in start handler: {e}")
        
        await message.answer(
            text=(
                "❌ Произошла ошибка при регистрации.\n"
                "Попробуйте позже или обратитесь к администратору."
            )
        )

