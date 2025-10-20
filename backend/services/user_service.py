"""
User Service

Бизнес-логика для работы с пользователями Telegram бота.

Features:
- Регистрация пользователей из Telegram
- Управление пользователями (блокировка/разблокировка)
- Получение статистики пользователей
- Логирование всех операций

Author: AI Agent
Created: 2025-10-20
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from loguru import logger
from database import get_supabase_client
from models.user import (
    UserCreate,
    UserResponse,
    UserUpdate,
    UserStatsResponse
)


# ==================== Exceptions ====================

class UserServiceError(Exception):
    """Базовое исключение для UserService"""
    pass


class UserNotFoundError(UserServiceError):
    """Пользователь не найден"""
    pass


class UserAlreadyExistsError(UserServiceError):
    """Пользователь уже существует"""
    pass


# ==================== User Service ====================

class UserService:
    """
    Сервис для работы с пользователями
    
    Управляет жизненным циклом пользователей: регистрация,
    обновление, блокировка. Предоставляет статистику.
    """
    
    def __init__(self):
        """Инициализация сервиса"""
        self.supabase = get_supabase_client()
        logger.info("✅ UserService initialized")
    
    # ==================== Логирование ====================
    
    async def _log_operation(
        self,
        level: str,
        event_type: str,
        message: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Логирование операции в БД
        
        Args:
            level: Уровень лога (INFO, WARNING, ERROR, CRITICAL)
            event_type: Тип события
            message: Сообщение
            user_id: ID пользователя (опционально)
            metadata: Дополнительные данные (опционально)
        """
        try:
            log_data = {
                "level": level.upper(),
                "event_type": event_type,
                "message": message,
                "user_id": user_id,
                "metadata": metadata or {},
                "timestamp": datetime.now().isoformat()
            }
            
            self.supabase.table("ozon_scraper_logs").insert(log_data).execute()
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to log operation to DB: {e}")
    
    # ==================== User Operations ====================
    
    async def register_user(
        self,
        telegram_id: int,
        telegram_username: Optional[str] = None
    ) -> UserResponse:
        """
        Регистрация нового пользователя из Telegram
        
        Args:
            telegram_id: Telegram ID пользователя
            telegram_username: Telegram username (опционально)
            
        Returns:
            UserResponse с данными пользователя
            
        Raises:
            UserAlreadyExistsError: Если пользователь уже существует
            UserServiceError: При других ошибках
        """
        try:
            # Проверка существования
            existing = self.supabase.table("ozon_scraper_users").select("*").eq(
                "telegram_id", telegram_id
            ).execute()
            
            if existing.data:
                logger.info(f"👤 User already exists: {telegram_id}")
                # Обновляем last_active_at
                user_data = existing.data[0]
                self.supabase.table("ozon_scraper_users").update({
                    "last_active_at": datetime.now().isoformat()
                }).eq("id", user_data["id"]).execute()
                
                return UserResponse(**user_data)
            
            # Создаем нового пользователя
            user_data = {
                "telegram_id": telegram_id,
                "telegram_username": telegram_username,
                "is_blocked": False,
                "created_at": datetime.now().isoformat(),
                "last_active_at": datetime.now().isoformat()
            }
            
            result = self.supabase.table("ozon_scraper_users").insert(user_data).execute()
            
            if not result.data:
                raise UserServiceError("Failed to register user in database")
            
            created_user = result.data[0]
            
            # Логируем регистрацию
            await self._log_operation(
                level="INFO",
                event_type="user_registered",
                message=f"New user registered: {telegram_id} (@{telegram_username})",
                user_id=created_user["id"],
                metadata={
                    "telegram_id": telegram_id,
                    "telegram_username": telegram_username
                }
            )
            
            logger.success(f"✅ User registered: {telegram_id} (ID: {created_user['id']})")
            
            return UserResponse(**created_user)
            
        except UserAlreadyExistsError:
            raise
        except Exception as e:
            logger.error(f"❌ Error registering user: {e}")
            await self._log_operation(
                level="ERROR",
                event_type="user_registration_failed",
                message=f"Failed to register user {telegram_id}: {str(e)}",
                metadata={"error": str(e), "telegram_id": telegram_id}
            )
            raise UserServiceError(f"Failed to register user: {str(e)}")
    
    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[UserResponse]:
        """
        Найти пользователя по Telegram ID
        
        Args:
            telegram_id: Telegram ID пользователя
            
        Returns:
            UserResponse или None если не найден
        """
        try:
            result = self.supabase.table("ozon_scraper_users").select("*").eq(
                "telegram_id", telegram_id
            ).execute()
            
            if not result.data:
                logger.info(f"👤 User not found: {telegram_id}")
                return None
            
            user_data = result.data[0]
            
            # Обновляем last_active_at
            self.supabase.table("ozon_scraper_users").update({
                "last_active_at": datetime.now().isoformat()
            }).eq("id", user_data["id"]).execute()
            
            return UserResponse(**user_data)
            
        except Exception as e:
            logger.error(f"❌ Error fetching user: {e}")
            raise UserServiceError(f"Failed to fetch user: {str(e)}")
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserResponse]:
        """
        Найти пользователя по UUID
        
        Args:
            user_id: UUID пользователя
            
        Returns:
            UserResponse или None если не найден
        """
        try:
            result = self.supabase.table("ozon_scraper_users").select("*").eq(
                "id", user_id
            ).execute()
            
            if not result.data:
                return None
            
            return UserResponse(**result.data[0])
            
        except Exception as e:
            logger.error(f"❌ Error fetching user by ID: {e}")
            raise UserServiceError(f"Failed to fetch user: {str(e)}")
    
    async def block_user(self, user_id: str, reason: Optional[str] = None) -> UserResponse:
        """
        Заблокировать пользователя
        
        Args:
            user_id: UUID пользователя
            reason: Причина блокировки (опционально)
            
        Returns:
            UserResponse с обновленными данными
            
        Raises:
            UserNotFoundError: Если пользователь не найден
            UserServiceError: При других ошибках
        """
        try:
            # Проверяем существование
            user = await self.get_user_by_id(user_id)
            if not user:
                raise UserNotFoundError(f"User {user_id} not found")
            
            # Блокируем
            update_data = {
                "is_blocked": True,
                "updated_at": datetime.now().isoformat()
            }
            
            result = self.supabase.table("ozon_scraper_users").update(
                update_data
            ).eq("id", user_id).execute()
            
            if not result.data:
                raise UserServiceError("Failed to block user in database")
            
            updated_user = result.data[0]
            
            # Логируем блокировку
            await self._log_operation(
                level="WARNING",
                event_type="user_blocked",
                message=f"User {user.telegram_id} blocked",
                user_id=user_id,
                metadata={
                    "telegram_id": user.telegram_id,
                    "reason": reason
                }
            )
            
            logger.warning(f"⚠️  User blocked: {user.telegram_id} (ID: {user_id})")
            
            return UserResponse(**updated_user)
            
        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"❌ Error blocking user: {e}")
            await self._log_operation(
                level="ERROR",
                event_type="user_block_failed",
                message=f"Failed to block user {user_id}: {str(e)}",
                metadata={"error": str(e), "user_id": user_id}
            )
            raise UserServiceError(f"Failed to block user: {str(e)}")
    
    async def unblock_user(self, user_id: str) -> UserResponse:
        """
        Разблокировать пользователя
        
        Args:
            user_id: UUID пользователя
            
        Returns:
            UserResponse с обновленными данными
            
        Raises:
            UserNotFoundError: Если пользователь не найден
            UserServiceError: При других ошибках
        """
        try:
            # Проверяем существование
            user = await self.get_user_by_id(user_id)
            if not user:
                raise UserNotFoundError(f"User {user_id} not found")
            
            # Разблокируем
            update_data = {
                "is_blocked": False,
                "updated_at": datetime.now().isoformat()
            }
            
            result = self.supabase.table("ozon_scraper_users").update(
                update_data
            ).eq("id", user_id).execute()
            
            if not result.data:
                raise UserServiceError("Failed to unblock user in database")
            
            updated_user = result.data[0]
            
            # Логируем разблокировку
            await self._log_operation(
                level="INFO",
                event_type="user_unblocked",
                message=f"User {user.telegram_id} unblocked",
                user_id=user_id,
                metadata={"telegram_id": user.telegram_id}
            )
            
            logger.success(f"✅ User unblocked: {user.telegram_id} (ID: {user_id})")
            
            return UserResponse(**updated_user)
            
        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"❌ Error unblocking user: {e}")
            await self._log_operation(
                level="ERROR",
                event_type="user_unblock_failed",
                message=f"Failed to unblock user {user_id}: {str(e)}",
                metadata={"error": str(e), "user_id": user_id}
            )
            raise UserServiceError(f"Failed to unblock user: {str(e)}")
    
    async def get_all_users(
        self,
        limit: int = 100,
        offset: int = 0,
        include_blocked: bool = True
    ) -> List[UserResponse]:
        """
        Получить список всех пользователей
        
        Args:
            limit: Максимум записей (default: 100)
            offset: Смещение для пагинации (default: 0)
            include_blocked: Включать заблокированных (default: True)
            
        Returns:
            Список UserResponse
        """
        try:
            query = self.supabase.table("ozon_scraper_users").select(
                "*"
            ).order("created_at", desc=True).limit(limit).offset(offset)
            
            if not include_blocked:
                query = query.eq("is_blocked", False)
            
            result = query.execute()
            
            users = [UserResponse(**item) for item in result.data]
            
            logger.info(f"📋 Found {len(users)} users")
            
            return users
            
        except Exception as e:
            logger.error(f"❌ Error fetching users: {e}")
            raise UserServiceError(f"Failed to fetch users: {str(e)}")
    
    async def get_user_stats(self, user_id: str) -> UserStatsResponse:
        """
        Получить статистику пользователя
        
        Args:
            user_id: UUID пользователя
            
        Returns:
            UserStatsResponse со статистикой
            
        Raises:
            UserNotFoundError: Если пользователь не найден
        """
        try:
            # Проверяем существование пользователя
            user = await self.get_user_by_id(user_id)
            if not user:
                raise UserNotFoundError(f"User {user_id} not found")
            
            # Получаем количество артикулов
            articles_result = self.supabase.table("ozon_scraper_articles").select(
                "id, status"
            ).eq("user_id", user_id).execute()
            
            total_articles = len(articles_result.data)
            active_articles = len([a for a in articles_result.data if a["status"] == "active"])
            
            # Получаем количество запросов за последние 30 дней
            thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
            requests_result = self.supabase.table("ozon_scraper_request_history").select(
                "id, success"
            ).eq("user_id", user_id).gte("requested_at", thirty_days_ago).execute()
            
            total_requests = len(requests_result.data)
            successful_requests = len([r for r in requests_result.data if r.get("success", False)])
            
            # Формируем статистику
            stats = UserStatsResponse(
                user_id=user_id,
                telegram_id=user.telegram_id,
                telegram_username=user.telegram_username,
                is_blocked=user.is_blocked,
                created_at=user.created_at,
                last_active_at=user.last_active_at,
                total_articles=total_articles,
                active_articles=active_articles,
                total_requests_30d=total_requests,
                successful_requests_30d=successful_requests
            )
            
            logger.info(f"📊 Stats for user {user_id}: {total_articles} articles, {total_requests} requests")
            
            return stats
            
        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"❌ Error fetching user stats: {e}")
            raise UserServiceError(f"Failed to fetch user stats: {str(e)}")


# ==================== Singleton ====================

_user_service_instance: Optional[UserService] = None


def get_user_service() -> UserService:
    """
    Получить singleton экземпляр UserService
    
    Returns:
        UserService instance
    """
    global _user_service_instance
    if _user_service_instance is None:
        _user_service_instance = UserService()
    return _user_service_instance

