"""
Throttling Middleware

Rate limiting для предотвращения спама и защиты от злоупотреблений.

Features:
- Sliding window rate limiting
- Per-user limits
- Configurable limits from settings
- Friendly error messages
"""

from typing import Callable, Dict, Awaitable, Any
from datetime import datetime, timedelta

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from loguru import logger

from config import settings


class ThrottlingMiddleware(BaseMiddleware):
    """
    Middleware для ограничения частоты запросов (rate limiting)
    
    Использует sliding window алгоритм для отслеживания запросов пользователей.
    """
    
    def __init__(self, rate_limit: int = None):
        """
        Инициализация middleware
        
        Args:
            rate_limit: Количество запросов в минуту (default: из settings)
        """
        super().__init__()
        self.rate_limit = rate_limit or settings.RATE_LIMIT
        self.user_requests: Dict[int, list] = {}  # user_id -> [timestamps]
        
        logger.info(f"🚦 Throttling middleware initialized (rate: {self.rate_limit}/min)")
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """
        Обработка события с rate limiting
        
        Args:
            handler: Следующий handler в цепочке
            event: Telegram событие (Message, CallbackQuery, etc.)
            data: Данные события
            
        Returns:
            Результат handler'а или None если заблокировано
        """
        # Получаем user_id в зависимости от типа события
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
        
        if not user_id:
            # Если не можем определить user_id, пропускаем
            return await handler(event, data)
        
        # Проверяем rate limit
        if not self._check_rate_limit(user_id):
            logger.warning(f"🚫 Rate limit exceeded for user {user_id}")
            
            # Отправляем сообщение об ограничении
            await self._send_throttle_message(event)
            return None
        
        # Записываем запрос
        self._record_request(user_id)
        
        # Продолжаем обработку
        return await handler(event, data)
    
    def _check_rate_limit(self, user_id: int) -> bool:
        """
        Проверить, не превышен ли лимит для пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            True если можно продолжить, False если лимит превышен
        """
        now = datetime.now()
        window_start = now - timedelta(minutes=1)
        
        # Получаем запросы пользователя
        if user_id not in self.user_requests:
            return True
        
        # Удаляем старые запросы (вне окна)
        self.user_requests[user_id] = [
            timestamp for timestamp in self.user_requests[user_id]
            if timestamp > window_start
        ]
        
        # Проверяем лимит
        request_count = len(self.user_requests[user_id])
        return request_count < self.rate_limit
    
    def _record_request(self, user_id: int):
        """
        Записать запрос пользователя
        
        Args:
            user_id: ID пользователя
        """
        now = datetime.now()
        
        if user_id not in self.user_requests:
            self.user_requests[user_id] = []
        
        self.user_requests[user_id].append(now)
        
        # Очищаем старые данные (> 5 минут)
        # Это для освобождения памяти
        window_start = now - timedelta(minutes=5)
        self.user_requests[user_id] = [
            timestamp for timestamp in self.user_requests[user_id]
            if timestamp > window_start
        ]
    
    async def _send_throttle_message(self, event: TelegramObject):
        """
        Отправить сообщение о превышении лимита
        
        Args:
            event: Telegram событие
        """
        message_text = (
            "⏳ <b>Слишком много запросов</b>\n\n"
            f"Вы превысили лимит запросов ({self.rate_limit} в минуту).\n"
            "Пожалуйста, подождите немного и попробуйте снова.\n\n"
            "💡 <i>Это сделано для защиты сервера и улучшения работы бота</i>"
        )
        
        try:
            if isinstance(event, Message):
                await event.answer(
                    text=message_text,
                    parse_mode="HTML"
                )
            elif isinstance(event, CallbackQuery):
                await event.answer(
                    text="⏳ Слишком много запросов. Подождите немного",
                    show_alert=True
                )
        except Exception as e:
            logger.error(f"❌ Error sending throttle message: {e}")
    
    def get_user_request_count(self, user_id: int) -> int:
        """
        Получить количество запросов пользователя в текущем окне
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Количество запросов
        """
        now = datetime.now()
        window_start = now - timedelta(minutes=1)
        
        if user_id not in self.user_requests:
            return 0
        
        # Считаем запросы в текущем окне
        return sum(
            1 for timestamp in self.user_requests[user_id]
            if timestamp > window_start
        )
    
    def clear_user_limits(self, user_id: int):
        """
        Очистить лимиты для пользователя (для админов)
        
        Args:
            user_id: ID пользователя
        """
        if user_id in self.user_requests:
            del self.user_requests[user_id]
            logger.info(f"🔓 Rate limits cleared for user {user_id}")

