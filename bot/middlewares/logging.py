"""
Logging Middleware

Middleware для логирования всех событий бота.

Features:
- Логирование всех сообщений
- Логирование всех callback queries
- Информация о пользователях
- Время обработки
- Ошибки
"""

from typing import Callable, Dict, Awaitable, Any
from datetime import datetime
import time

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from loguru import logger


class LoggingMiddleware(BaseMiddleware):
    """
    Middleware для логирования событий бота
    
    Логирует все входящие события с деталями пользователей и временем обработки.
    """
    
    def __init__(self):
        """Инициализация middleware"""
        super().__init__()
        logger.info("📝 Logging middleware initialized")
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """
        Обработка события с логированием
        
        Args:
            handler: Следующий handler в цепочке
            event: Telegram событие
            data: Данные события
            
        Returns:
            Результат handler'а
        """
        start_time = time.perf_counter()
        
        # Логируем входящее событие
        await self._log_incoming_event(event)
        
        try:
            # Обрабатываем событие
            result = await handler(event, data)
            
            # Логируем успешную обработку
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            await self._log_success(event, duration_ms)
            
            return result
            
        except Exception as e:
            # Логируем ошибку
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            await self._log_error(event, e, duration_ms)
            raise
    
    async def _log_incoming_event(self, event: TelegramObject):
        """
        Логировать входящее событие
        
        Args:
            event: Telegram событие
        """
        if isinstance(event, Message):
            user = event.from_user
            chat_type = event.chat.type
            text = event.text[:100] if event.text else "<no text>"
            
            logger.info(
                f"📨 Message | "
                f"User: {user.id} (@{user.username}) | "
                f"Chat: {chat_type} | "
                f"Text: {text}"
            )
            
        elif isinstance(event, CallbackQuery):
            user = event.from_user
            callback_data = event.data[:100] if event.data else "<no data>"
            
            logger.info(
                f"🔘 Callback | "
                f"User: {user.id} (@{user.username}) | "
                f"Data: {callback_data}"
            )
    
    async def _log_success(self, event: TelegramObject, duration_ms: int):
        """
        Логировать успешную обработку
        
        Args:
            event: Telegram событие
            duration_ms: Время обработки в миллисекундах
        """
        event_type = "Message" if isinstance(event, Message) else "Callback"
        
        logger.success(
            f"✅ {event_type} processed successfully in {duration_ms}ms"
        )
    
    async def _log_error(self, event: TelegramObject, error: Exception, duration_ms: int):
        """
        Логировать ошибку обработки
        
        Args:
            event: Telegram событие
            error: Исключение
            duration_ms: Время обработки в миллисекундах
        """
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
        
        event_type = "Message" if isinstance(event, Message) else "Callback"
        
        logger.error(
            f"❌ {event_type} processing failed after {duration_ms}ms | "
            f"User: {user_id} | "
            f"Error: {type(error).__name__}: {str(error)}"
        )


class UserActivityMiddleware(BaseMiddleware):
    """
    Middleware для отслеживания активности пользователей
    
    Записывает последнюю активность пользователей для аналитики.
    """
    
    def __init__(self):
        """Инициализация middleware"""
        super().__init__()
        self.user_activity: Dict[int, datetime] = {}
        logger.info("👥 User activity middleware initialized")
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """
        Обработка события с отслеживанием активности
        
        Args:
            handler: Следующий handler в цепочке
            event: Telegram событие
            data: Данные события
            
        Returns:
            Результат handler'а
        """
        # Получаем user_id
        user_id = None
        username = None
        
        if isinstance(event, Message):
            user_id = event.from_user.id
            username = event.from_user.username
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            username = event.from_user.username
        
        # Записываем активность
        if user_id:
            now = datetime.now()
            
            # Логируем только если прошло > 5 минут с последней активности
            if user_id not in self.user_activity or \
               (now - self.user_activity[user_id]).seconds > 300:
                logger.info(f"👤 User {user_id} (@{username}) is active")
            
            self.user_activity[user_id] = now
        
        # Продолжаем обработку
        return await handler(event, data)
    
    def get_active_users_count(self, minutes: int = 60) -> int:
        """
        Получить количество активных пользователей за последние N минут
        
        Args:
            minutes: Временное окно в минутах
            
        Returns:
            Количество активных пользователей
        """
        now = datetime.now()
        threshold = now - timedelta(minutes=minutes)
        
        return sum(
            1 for timestamp in self.user_activity.values()
            if timestamp > threshold
        )
    
    def get_user_last_activity(self, user_id: int) -> datetime | None:
        """
        Получить время последней активности пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Datetime последней активности или None
        """
        return self.user_activity.get(user_id)


# Импорт для использования
from datetime import timedelta

