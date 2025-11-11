"""
Telegram Notifier Service

Сервис для отправки уведомлений в Telegram при изменении цен товаров.
"""

import os
from typing import Optional, Dict, Any
import aiohttp
from loguru import logger


class TelegramNotifier:
    """
    Сервис для отправки уведомлений в Telegram
    
    Использует Telegram Bot API напрямую через HTTP запросы.
    """
    
    def __init__(self, bot_token: Optional[str] = None):
        """
        Инициализация сервиса
        
        Args:
            bot_token: Токен Telegram бота (если не указан, берется из переменных окружения)
        """
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN не установлен")
        
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        logger.info("✅ TelegramNotifier initialized")
    
    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str = "HTML"
    ) -> bool:
        """
        Отправить сообщение в Telegram
        
        Args:
            chat_id: ID чата (telegram_id пользователя)
            text: Текст сообщения
            parse_mode: Режим парсинга (HTML или Markdown)
            
        Returns:
            True если успешно отправлено
        """
        try:
            url = f"{self.api_url}/sendMessage"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json={
                        "chat_id": chat_id,
                        "text": text,
                        "parse_mode": parse_mode
                    }
                ) as response:
                    if response.status == 200:
                        logger.info(f"✅ Notification sent to {chat_id}")
                        return True
                    else:
                        error_data = await response.json()
                        logger.error(f"❌ Failed to send notification: {error_data}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ Error sending notification: {e}")
            return False
    
    def format_price_change_notification(
        self,
        article_number: str,
        article_name: Optional[str],
        old_prices: Dict[str, Optional[float]],
        new_prices: Dict[str, Optional[float]]
    ) -> str:
        """
        Форматировать уведомление об изменении цены
        
        Args:
            article_number: Номер артикула
            article_name: Название товара (опционально)
            old_prices: Старые цены {"normal_price": float, "ozon_card_price": float}
            new_prices: Новые цены {"normal_price": float, "ozon_card_price": float}
            
        Returns:
            Отформатированное сообщение
        """
        text = "🔔 <b>Обновление цены</b>\n\n"
        text += f"Артикул: <code>{article_number}</code>\n"
        
        if article_name:
            text += f"Название: {article_name}\n"
        
        text += "\n<b>Цены:</b>\n"
        
        # Нормальная цена
        old_normal = old_prices.get("normal_price")
        new_normal = new_prices.get("normal_price")
        
        if old_normal is not None and new_normal is not None:
            if old_normal != new_normal:
                change = new_normal - old_normal
                change_pct = (change / old_normal * 100) if old_normal > 0 else 0
                arrow = "🔺" if change > 0 else "🔻"
                color_tag = "red" if change > 0 else "green"
                
                text += (
                    f"• Без Ozon Card: {old_normal:,.0f} ₽ → "
                    f"<span style='color:{color_tag}'>{new_normal:,.0f} ₽</span> "
                    f"{arrow} {abs(change):,.0f} ₽ ({change_pct:+.1f}%)\n"
                )
            else:
                text += f"• Без Ozon Card: {new_normal:,.0f} ₽\n"
        elif new_normal is not None:
            text += f"• Без Ozon Card: {new_normal:,.0f} ₽\n"
        
        # Цена с Ozon Card
        old_card = old_prices.get("ozon_card_price")
        new_card = new_prices.get("ozon_card_price")
        
        if old_card is not None and new_card is not None:
            if old_card != new_card:
                change = new_card - old_card
                change_pct = (change / old_card * 100) if old_card > 0 else 0
                arrow = "🔺" if change > 0 else "🔻"
                color_tag = "red" if change > 0 else "green"
                
                text += (
                    f"• С Ozon Card: {old_card:,.0f} ₽ → "
                    f"<span style='color:{color_tag}'>{new_card:,.0f} ₽</span> "
                    f"{arrow} {abs(change):,.0f} ₽ ({change_pct:+.1f}%)\n"
                )
            else:
                text += f"• С Ozon Card: {new_card:,.0f} ₽\n"
        elif new_card is not None:
            text += f"• С Ozon Card: {new_card:,.0f} ₽\n"
        
        return text
    
    async def send_price_update_notification(
        self,
        telegram_id: int,
        article_number: str,
        article_name: Optional[str],
        old_prices: Dict[str, Optional[float]],
        new_prices: Dict[str, Optional[float]]
    ) -> bool:
        """
        Отправить уведомление об изменении цены
        
        Args:
            telegram_id: Telegram ID пользователя
            article_number: Номер артикула
            article_name: Название товара
            old_prices: Старые цены
            new_prices: Новые цены
            
        Returns:
            True если успешно отправлено
        """
        # Проверяем, изменились ли цены
        old_normal = old_prices.get("normal_price")
        new_normal = new_prices.get("normal_price")
        old_card = old_prices.get("ozon_card_price")
        new_card = new_prices.get("ozon_card_price")
        
        # Если цены не изменились, не отправляем уведомление
        if (old_normal == new_normal and old_card == new_card):
            logger.debug(f"No price change for article {article_number}, skipping notification")
            return False
        
        # Форматируем сообщение
        message = self.format_price_change_notification(
            article_number=article_number,
            article_name=article_name,
            old_prices=old_prices,
            new_prices=new_prices
        )
        
        # Отправляем
        return await self.send_message(telegram_id, message)


# Singleton instance
_telegram_notifier_instance: Optional[TelegramNotifier] = None


def get_telegram_notifier(bot_token: Optional[str] = None) -> TelegramNotifier:
    """
    Получить singleton экземпляр TelegramNotifier
    
    Args:
        bot_token: Токен бота (опционально)
        
    Returns:
        TelegramNotifier instance
    """
    global _telegram_notifier_instance
    if _telegram_notifier_instance is None:
        _telegram_notifier_instance = TelegramNotifier(bot_token=bot_token)
    return _telegram_notifier_instance

