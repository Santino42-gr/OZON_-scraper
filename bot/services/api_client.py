"""
API Client для Backend

HTTP клиент для взаимодействия с FastAPI Backend.

Features:
- Async HTTP requests с aiohttp
- Retry логика с экспоненциальным backoff
- Обработка таймаутов
- Форматирование ошибок
- Типизированные методы для всех endpoint'ов
"""

import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime

import aiohttp
from loguru import logger

from config import settings


class APIError(Exception):
    """Базовая ошибка API"""
    pass


class APITimeoutError(APIError):
    """Таймаут API запроса"""
    pass


class APIConnectionError(APIError):
    """Ошибка подключения к API"""
    pass


class APIResponseError(APIError):
    """Ошибка ответа API"""
    def __init__(self, message: str, status_code: int, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}


class BackendAPIClient:
    """
    Клиент для работы с Backend API
    
    Обеспечивает типизированный доступ ко всем endpoint'ам FastAPI backend.
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
        retry_count: Optional[int] = None
    ):
        """
        Инициализация API клиента
        
        Args:
            base_url: URL Backend API (default: из settings)
            timeout: Таймаут запросов в секундах (default: из settings)
            retry_count: Количество повторов (default: из settings)
        """
        self.base_url = (base_url or settings.BACKEND_API_URL).rstrip("/")
        self.timeout = timeout or settings.API_TIMEOUT
        self.retry_count = retry_count or settings.API_RETRY_COUNT
        self._session: Optional[aiohttp.ClientSession] = None
        
        logger.info(f"🌐 Backend API Client initialized: {self.base_url}")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Получить или создать HTTP сессию"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "OZON-Bot/1.0"
                }
            )
        return self._session
    
    async def close(self):
        """Закрыть HTTP сессию"""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.info("🔒 API Client session closed")
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Выполнить HTTP запрос с retry логикой
        
        Args:
            method: HTTP метод (GET, POST, PUT, DELETE)
            endpoint: Путь endpoint (без base_url)
            **kwargs: Дополнительные параметры для aiohttp
            
        Returns:
            JSON ответ от API
            
        Raises:
            APITimeoutError: При таймауте
            APIConnectionError: При ошибке подключения
            APIResponseError: При ошибке ответа (4xx, 5xx)
        """
        url = f"{self.base_url}{endpoint}"
        last_error = None
        
        for attempt in range(self.retry_count):
            try:
                session = await self._get_session()
                
                logger.debug(f"🔄 {method} {url} (attempt {attempt + 1}/{self.retry_count})")
                
                async with session.request(method, url, **kwargs) as response:
                    # Получаем тело ответа
                    try:
                        data = await response.json()
                    except:
                        data = {"error": await response.text()}
                    
                    # Проверяем статус
                    if response.status >= 400:
                        error_msg = data.get("detail", data.get("error", "Unknown error"))
                        raise APIResponseError(
                            f"API error: {error_msg}",
                            status_code=response.status,
                            response_data=data
                        )
                    
                    logger.debug(f"✅ {method} {url} - {response.status}")
                    return data
                    
            except asyncio.TimeoutError as e:
                last_error = APITimeoutError(f"Request timeout: {url}")
                logger.warning(f"⏱️  Timeout on attempt {attempt + 1}: {url}")
                
            except aiohttp.ClientError as e:
                last_error = APIConnectionError(f"Connection error: {str(e)}")
                logger.warning(f"🔌 Connection error on attempt {attempt + 1}: {e}")
                
            except APIResponseError:
                # Не retry 4xx ошибки (клиентские ошибки)
                raise
                
            except Exception as e:
                last_error = APIError(f"Unexpected error: {str(e)}")
                logger.error(f"❌ Unexpected error: {e}")
            
            # Задержка перед retry (экспоненциальный backoff)
            if attempt < self.retry_count - 1:
                delay = 2 ** attempt  # 1s, 2s, 4s
                await asyncio.sleep(delay)
        
        # Все попытки исчерпаны
        logger.error(f"❌ All retry attempts failed for {url}")
        raise last_error
    
    # ==================== Health & Status ====================
    
    async def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья Backend API"""
        return await self._request("GET", "/health")
    
    # ==================== Users ====================
    
    async def register_user(
        self,
        telegram_id: int,
        telegram_username: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Зарегистрировать пользователя
        
        Args:
            telegram_id: Telegram ID пользователя
            telegram_username: Telegram username (опционально)
            
        Returns:
            Данные пользователя
        """
        return await self._request(
            "POST",
            "/api/v1/users/register",
            json={
                "telegram_id": telegram_id,
                "telegram_username": telegram_username
            }
        )
    
    async def get_user_by_telegram_id(self, telegram_id: int) -> Dict[str, Any]:
        """Получить пользователя по Telegram ID"""
        return await self._request(
            "GET",
            f"/api/v1/users/telegram/{telegram_id}"
        )
    
    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Получить статистику пользователя"""
        return await self._request(
            "GET",
            f"/api/v1/users/{user_id}/stats"
        )
    
    # ==================== Articles ====================
    
    async def create_article(
        self,
        user_id: str,
        article_number: str
    ) -> Dict[str, Any]:
        """
        Создать артикул
        
        Args:
            user_id: UUID пользователя
            article_number: Номер артикула OZON
            
        Returns:
            Данные артикула
        """
        return await self._request(
            "POST",
            "/api/v1/articles",
            json={
                "user_id": user_id,
                "article_number": article_number
            }
        )
    
    async def get_user_articles(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Получить артикулы пользователя"""
        response = await self._request(
            "GET",
            "/api/v1/articles/",
            params={"user_id": user_id, "limit": limit, "offset": offset}
        )
        # Ответ может быть списком напрямую или объектом с полем articles
        if isinstance(response, list):
            return response
        return response.get("articles", [])
    
    async def delete_article(self, article_id: str, user_id: str) -> Dict[str, Any]:
        """Удалить артикул"""
        return await self._request(
            "DELETE",
            f"/api/v1/articles/{article_id}",
            params={"user_id": user_id}
        )
    
    async def update_article(self, article_id: str) -> Dict[str, Any]:
        """Обновить данные артикула с OZON"""
        return await self._request(
            "PUT",
            f"/api/v1/articles/{article_id}/update"
        )
    
    async def check_article(self, article_id: str) -> Dict[str, Any]:
        """Проверить статус артикула на OZON"""
        return await self._request(
            "GET",
            f"/api/v1/articles/{article_id}/check"
        )

    # ==================== Comparison ====================

    async def quick_compare(
        self,
        user_id: str,
        own_article_number: str,
        competitor_article_number: str,
        group_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Быстрое сравнение своего артикула с конкурентом

        Args:
            user_id: UUID пользователя
            own_article_number: Артикул своего товара
            competitor_article_number: Артикул конкурента
            group_name: Название группы сравнения (опционально)

        Returns:
            Результат сравнения с метриками
        """
        return await self._request(
            "POST",
            "/api/v1/comparison/quick-compare",
            params={"user_id": user_id},
            json={
                "own_article_number": own_article_number,
                "competitor_article_number": competitor_article_number,
                "group_name": group_name,
                "scrape_now": True
            }
        )

    # ==================== Reports ====================
    
    async def generate_article_report(
        self,
        article_id: str,
        include_history: bool = True,
        days: int = 30
    ) -> Dict[str, Any]:
        """Сгенерировать отчет по артикулу"""
        return await self._request(
            "POST",
            "/api/v1/reports/article",
            json={
                "article_id": article_id,
                "include_history": include_history,
                "days": days
            }
        )
    
    async def generate_user_report(
        self,
        user_id: str,
        include_articles: bool = True,
        days: int = 30
    ) -> Dict[str, Any]:
        """Сгенерировать отчет по пользователю"""
        return await self._request(
            "POST",
            "/api/v1/reports/user",
            json={
                "user_id": user_id,
                "include_articles": include_articles,
                "days": days
            }
        )
    
    # ==================== Stats ====================
    
    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """Получить статистику dashboard"""
        return await self._request(
            "GET",
            "/api/v1/stats/dashboard"
        )


# ==================== Singleton ====================

_api_client_instance: Optional[BackendAPIClient] = None


def get_api_client() -> BackendAPIClient:
    """
    Получить singleton экземпляр API клиента
    
    Returns:
        BackendAPIClient instance
    """
    global _api_client_instance
    if _api_client_instance is None:
        _api_client_instance = BackendAPIClient()
    return _api_client_instance

