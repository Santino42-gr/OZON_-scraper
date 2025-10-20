"""
Reports Handler

Обработчик команд для генерации отчетов.

Commands:
- /report - меню отчетов
- /report <артикул> - отчет по артикулу
- /report all - отчет по всем артикулам
"""

from aiogram import Router, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, CallbackQuery
from loguru import logger

from keyboards import get_main_menu
from services.api_client import get_api_client, APIError
from utils.formatters import format_report, format_error, truncate_text
from handlers.articles import validate_article_number


router = Router(name="reports")


@router.message(Command("report"))
async def cmd_report(message: Message, command: CommandObject):
    """
    Команда /report - генерация отчетов
    
    Варианты использования:
    - /report - меню выбора
    - /report 123456789 - отчет по артикулу
    - /report all - отчет по всем артикулам
    """
    user = message.from_user
    logger.info(f"📊 User {user.id} requested report")
    
    if not command.args:
        # Показываем меню
        text = (
            "📊 <b>Отчеты</b>\n\n"
            "Выберите тип отчета:\n\n"
            "📦 <code>/report 123456789</code> - отчет по конкретному артикулу\n"
            "📋 <code>/report all</code> - отчет по всем артикулам\n"
            "👤 <code>/report user</code> - моя статистика\n\n"
            "<i>Отчеты включают:</i>\n"
            "• Средние цены за 7 дней\n"
            "• Историю изменений\n"
            "• Статистику запросов\n"
            "• Графики (скоро)"
        )
        
        await message.answer(
            text=text,
            parse_mode="HTML"
        )
        return
    
    args = command.args.strip().lower()
    
    if args == "all":
        await generate_all_articles_report(message)
    elif args == "user":
        await generate_user_report(message)
    else:
        # Предполагаем, что это номер артикула
        article_number = command.args.strip()
        await generate_article_report(message, article_number)


async def generate_article_report(message: Message, article_number: str):
    """
    Сгенерировать отчет по конкретному артикулу
    
    Args:
        message: Сообщение пользователя
        article_number: Номер артикула
    """
    user = message.from_user
    
    if not validate_article_number(article_number):
        await message.answer(
            text=format_error(
                "Неверный формат артикула",
                "Артикул должен содержать только цифры (5-12 символов)"
            ),
            parse_mode="HTML"
        )
        return
    
    logger.info(f"📊 Generating article report for {article_number} (user {user.id})")
    
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
        
        # Получаем артикулы и ищем нужный
        articles = await api_client.get_user_articles(user_id)
        article_data = next(
            (a for a in articles if a.get("article_number") == article_number),
            None
        )
        
        if not article_data:
            await message.answer(
                text=format_error(
                    "Артикул не найден",
                    f"Артикул {article_number} не добавлен в ваш список.\nИспользуйте /add для добавления"
                ),
                parse_mode="HTML"
            )
            return
        
        article_id = article_data.get("id")
        
        # Отправляем "typing..."
        await message.bot.send_chat_action(message.chat.id, "typing")
        
        loading_msg = await message.answer(
            text="⏳ Генерирую отчет..."
        )
        
        # Генерируем отчет
        report = await api_client.generate_article_report(
            article_id=article_id,
            include_history=True,
            days=30
        )
        
        await loading_msg.delete()
        
        # Форматируем отчет
        text = format_report(report)
        
        await message.answer(
            text=truncate_text(text),
            parse_mode="HTML"
        )
        
        logger.success(f"✅ Generated article report for {article_number}")
        
    except APIError as e:
        await message.answer(
            text=format_error("Не удалось сгенерировать отчет", str(e)),
            parse_mode="HTML"
        )
        logger.error(f"❌ Error generating article report: {e}")
    
    except Exception as e:
        await message.answer(
            text=format_error("Произошла непредвиденная ошибка", str(e)),
            parse_mode="HTML"
        )
        logger.error(f"❌ Unexpected error generating report: {e}")


async def generate_all_articles_report(message: Message):
    """
    Сгенерировать отчет по всем артикулам пользователя
    
    Args:
        message: Сообщение пользователя
    """
    user = message.from_user
    logger.info(f"📊 Generating all articles report for user {user.id}")
    
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
        articles = await api_client.get_user_articles(user_id)
        
        if not articles:
            await message.answer(
                text=(
                    "📭 <b>У вас нет артикулов</b>\n\n"
                    "Добавьте артикулы для создания отчета"
                ),
                parse_mode="HTML"
            )
            return
        
        # Отправляем "typing..."
        await message.bot.send_chat_action(message.chat.id, "typing")
        
        loading_msg = await message.answer(
            text=f"⏳ Генерирую отчет по {len(articles)} артикулам..."
        )
        
        # Генерируем отчеты для каждого артикула
        reports_text = f"<b>📊 СВОДНЫЙ ОТЧЕТ</b>\n\n"
        reports_text += f"<b>Артикулов:</b> {len(articles)}\n"
        reports_text += f"<b>Пользователь:</b> @{user.username or user.id}\n\n"
        reports_text += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for i, article in enumerate(articles[:10], 1):  # Ограничиваем 10 артикулами
            article_id = article.get("id")
            article_number = article.get("article_number")
            
            try:
                report = await api_client.generate_article_report(
                    article_id=article_id,
                    include_history=False,
                    days=7
                )
                
                reports_text += f"<b>{i}. Артикул {article_number}</b>\n"
                
                # Средняя цена
                avg_price_7d = report.get("average_price_7d", {})
                avg_price = avg_price_7d.get("avg_price")
                if avg_price:
                    reports_text += f"   💰 Средняя: {avg_price} ₽\n"
                
                reports_text += "\n"
                
            except Exception as e:
                logger.warning(f"⚠️ Error generating report for {article_number}: {e}")
                reports_text += f"<b>{i}. Артикул {article_number}</b>\n"
                reports_text += f"   ❌ Ошибка получения данных\n\n"
        
        if len(articles) > 10:
            reports_text += f"\n<i>... и еще {len(articles) - 10} артикулов</i>\n"
        
        await loading_msg.delete()
        
        await message.answer(
            text=truncate_text(reports_text),
            parse_mode="HTML"
        )
        
        logger.success(f"✅ Generated all articles report for user {user.id}")
        
    except APIError as e:
        await message.answer(
            text=format_error("Не удалось сгенерировать отчет", str(e)),
            parse_mode="HTML"
        )
        logger.error(f"❌ Error generating all articles report: {e}")
    
    except Exception as e:
        await message.answer(
            text=format_error("Произошла непредвиденная ошибка", str(e)),
            parse_mode="HTML"
        )
        logger.error(f"❌ Unexpected error generating report: {e}")


async def generate_user_report(message: Message):
    """
    Сгенерировать отчет по пользователю (статистика)
    
    Args:
        message: Сообщение пользователя
    """
    user = message.from_user
    logger.info(f"📊 Generating user report for {user.id}")
    
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
            text="⏳ Генерирую отчет..."
        )
        
        # Генерируем отчет
        report = await api_client.generate_user_report(
            user_id=user_id,
            include_articles=True,
            days=30
        )
        
        await loading_msg.delete()
        
        # Форматируем отчет
        text = format_report(report)
        
        await message.answer(
            text=truncate_text(text),
            parse_mode="HTML"
        )
        
        logger.success(f"✅ Generated user report for {user.id}")
        
    except APIError as e:
        await message.answer(
            text=format_error("Не удалось сгенерировать отчет", str(e)),
            parse_mode="HTML"
        )
        logger.error(f"❌ Error generating user report: {e}")
    
    except Exception as e:
        await message.answer(
            text=format_error("Произошла непредвиденная ошибка", str(e)),
            parse_mode="HTML"
        )
        logger.error(f"❌ Unexpected error generating report: {e}")


@router.callback_query(F.data.startswith("article_report:"))
async def callback_article_report(callback: CallbackQuery):
    """Сгенерировать отчет по артикулу (из inline кнопки)"""
    await callback.answer("⏳ Генерирую отчет...")
    
    article_id = callback.data.split(":")[1]
    logger.info(f"📊 Generating article report from callback (article {article_id})")
    
    try:
        api_client = get_api_client()
        
        # Генерируем отчет
        report = await api_client.generate_article_report(
            article_id=article_id,
            include_history=True,
            days=30
        )
        
        # Форматируем отчет
        text = format_report(report)
        
        await callback.message.answer(
            text=truncate_text(text),
            parse_mode="HTML"
        )
        
        logger.success(f"✅ Generated article report for {article_id}")
        
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)
        logger.error(f"❌ Error generating report from callback: {e}")

