"""
Article Service

Бизнес-логика для работы с артикулами OZON.

Features:
- CRUD операции для артикулов
- Интеграция с OzonScraper для получения данных
- Валидация артикулов OZON
- Логирование всех операций
- Обработка ошибок

Author: AI Agent
Created: 2025-10-20
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
import re

from loguru import logger
from database import get_supabase_client
from models.article import (
    ArticleCreate,
    ArticleResponse,
    ArticleUpdate,
    ArticleCheckResponse
)
from services.ozon_service import get_ozon_service


# ==================== Exceptions ====================

class ArticleServiceError(Exception):
    """Базовое исключение для ArticleService"""
    pass


class ArticleNotFoundError(ArticleServiceError):
    """Артикул не найден"""
    pass


class ArticleValidationError(ArticleServiceError):
    """Ошибка валидации артикула"""
    pass


class ArticleAlreadyExistsError(ArticleServiceError):
    """Артикул уже существует у пользователя"""
    pass


# ==================== Article Service ====================

class ArticleService:
    """
    Сервис для работы с артикулами OZON
    
    Управляет жизненным циклом артикулов: создание, обновление,
    удаление, проверка статуса. Интегрируется с OzonScraper
    для получения актуальных данных о товарах.
    """
    
    def __init__(self):
        """Инициализация сервиса"""
        self.supabase = get_supabase_client()
        self.ozon_service = get_ozon_service()
        logger.info("✅ ArticleService initialized")
    
    # ==================== Логирование ====================
    
    async def _log_operation(
        self,
        level: str,
        event_type: str,
        message: str,
        user_id: Optional[str] = None,
        article_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Логирование операции в БД
        
        Args:
            level: Уровень лога (INFO, WARNING, ERROR, CRITICAL)
            event_type: Тип события (article_created, article_updated, etc)
            message: Сообщение
            user_id: ID пользователя (опционально)
            article_id: ID артикула (опционально)
            metadata: Дополнительные данные (опционально)
        """
        try:
            log_data = {
                "level": level.upper(),
                "event_type": event_type,
                "message": message,
                "user_id": user_id,
                "article_id": article_id,
                "metadata": metadata or {},
                "timestamp": datetime.now().isoformat()
            }
            
            self.supabase.table("ozon_scraper_logs").insert(log_data).execute()
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to log operation to DB: {e}")
    
    # ==================== Валидация ====================
    
    def validate_article_number(self, article_number: str) -> bool:
        """
        Валидация номера артикула OZON
        
        Артикул может быть:
        - Числовым (SKU): 123456789
        - Буквенно-числовым: ABC-123-XYZ
        - С дефисами и подчеркиваниями
        
        Args:
            article_number: Номер артикула для проверки
            
        Returns:
            True если артикул валиден
            
        Raises:
            ArticleValidationError: Если артикул невалиден
        """
        if not article_number or not isinstance(article_number, str):
            raise ArticleValidationError("Артикул должен быть непустой строкой")
        
        # Убираем пробелы
        article_number = article_number.strip()
        
        # Проверяем длину (от 3 до 50 символов)
        if len(article_number) < 3:
            raise ArticleValidationError("Артикул слишком короткий (минимум 3 символа)")
        
        if len(article_number) > 50:
            raise ArticleValidationError("Артикул слишком длинный (максимум 50 символов)")
        
        # Проверяем допустимые символы (буквы, цифры, дефис, подчеркивание)
        pattern = r'^[A-Za-z0-9\-_]+$'
        if not re.match(pattern, article_number):
            raise ArticleValidationError(
                "Артикул содержит недопустимые символы. "
                "Разрешены: буквы, цифры, дефис, подчеркивание"
            )
        
        logger.debug(f"✅ Article number validated: {article_number}")
        return True
    
    # ==================== CRUD Operations ====================
    
    async def create_article(
        self,
        user_id: str,
        article_number: str,
        report_frequency: str = "once",
        fetch_data: bool = True
    ) -> ArticleResponse:
        """
        Создать новый артикул для отслеживания
        
        Args:
            user_id: UUID пользователя
            article_number: Номер артикула OZON
            fetch_data: Сразу получить данные с OZON (default: True)
            
        Returns:
            ArticleResponse с созданным артикулом
            
        Raises:
            ArticleValidationError: Если артикул невалиден
            ArticleAlreadyExistsError: Если артикул уже существует
            ArticleServiceError: При других ошибках
        """
        try:
            # Валидация артикула
            self.validate_article_number(article_number)
            
            # Проверка существования
            existing = self.supabase.table("ozon_scraper_articles").select("*").eq(
                "user_id", user_id
            ).eq("article_number", article_number).execute()
            
            if existing.data:
                raise ArticleAlreadyExistsError(
                    f"Артикул {article_number} уже добавлен"
                )
            
            # Получаем данные с OZON если нужно
            last_check_data = None
            status = "active"
            is_problematic = False
            product = None
            
            if fetch_data:
                try:
                    logger.info(f"🔍 Fetching data from OZON for {article_number}")
                    product = await self.ozon_service.get_product_info(article_number)
                    
                    if product:
                        last_check_data = product.to_dict()
                        status = "active"
                        is_problematic = False
                        logger.success(f"✅ Product data fetched: {product.name}")
                    else:
                        logger.warning(f"⚠️  Product not found on OZON: {article_number}")
                        status = "error"
                        is_problematic = True
                        last_check_data = {
                            "error": "Product not found on OZON",
                            "checked_at": datetime.now().isoformat()
                        }
                        
                except Exception as e:
                    logger.error(f"❌ Failed to fetch OZON data: {e}")
                    status = "error"
                    is_problematic = True
                    last_check_data = {
                        "error": str(e),
                        "checked_at": datetime.now().isoformat()
                    }
            
            # Преобразуем HttpUrl в строки для сохранения
            image_url_str = str(product.image_url) if product and product.image_url else None
            product_url_str = str(product.url) if product and product.url else None
            
            # Создаем запись в БД с заполнением всех полей
            article_data = {
                "user_id": user_id,
                "article_number": article_number,
                "report_frequency": report_frequency,
                "status": status,
                "last_check_data": last_check_data,
                "is_problematic": is_problematic,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                # Заполняем отдельные поля из product если данные получены
                "name": product.name if product else None,
                "price": product.price if product else None,
                "old_price": product.old_price if product else None,
                "normal_price": product.normal_price if product else None,
                "ozon_card_price": product.ozon_card_price if product else None,
                "average_price_7days": product.average_price_7days if product else None,
                "rating": product.rating if product else None,
                "reviews_count": product.reviews_count if product else None,
                "available": product.available if product else True,
                "image_url": image_url_str,
                "product_url": product_url_str,
                "last_check": datetime.now().isoformat() if product else None,
                "price_updated_at": datetime.now().isoformat() if product else None
            }
            
            result = self.supabase.table("ozon_scraper_articles").insert(
                article_data
            ).execute()
            
            if not result.data:
                raise ArticleServiceError("Failed to create article in database")
            
            created_article = result.data[0]
            
            # Логируем создание
            await self._log_operation(
                level="INFO",
                event_type="article_created",
                message=f"Article {article_number} created for user {user_id}",
                user_id=user_id,
                article_id=created_article["id"],
                metadata={
                    "article_number": article_number,
                    "status": status,
                    "is_problematic": is_problematic
                }
            )
            
            logger.success(f"✅ Article created: {article_number} (ID: {created_article['id']})")
            
            return ArticleResponse(**created_article)
            
        except (ArticleValidationError, ArticleAlreadyExistsError):
            raise
        except Exception as e:
            logger.error(f"❌ Error creating article: {e}")
            await self._log_operation(
                level="ERROR",
                event_type="article_creation_failed",
                message=f"Failed to create article {article_number}: {str(e)}",
                user_id=user_id,
                metadata={"error": str(e), "article_number": article_number}
            )
            raise ArticleServiceError(f"Failed to create article: {str(e)}")
    
    async def delete_article(self, article_id: str, user_id: Optional[str] = None) -> bool:
        """
        Удалить артикул
        
        Args:
            article_id: UUID артикула
            user_id: UUID пользователя (для проверки прав)
            
        Returns:
            True если успешно удалено
            
        Raises:
            ArticleNotFoundError: Если артикул не найден
            ArticleServiceError: При других ошибках
        """
        try:
            # Получаем артикул для проверки
            query = self.supabase.table("ozon_scraper_articles").select("*").eq("id", article_id)
            
            if user_id:
                query = query.eq("user_id", user_id)
            
            article = query.execute()
            
            if not article.data:
                raise ArticleNotFoundError(f"Article {article_id} not found")
            
            article_data = article.data[0]
            
            # Удаляем
            self.supabase.table("ozon_scraper_articles").delete().eq("id", article_id).execute()
            
            # Логируем удаление
            await self._log_operation(
                level="INFO",
                event_type="article_deleted",
                message=f"Article {article_data['article_number']} deleted",
                user_id=article_data["user_id"],
                article_id=article_id,
                metadata={"article_number": article_data["article_number"]}
            )
            
            logger.success(f"✅ Article deleted: {article_id}")
            
            return True
            
        except ArticleNotFoundError:
            raise
        except Exception as e:
            logger.error(f"❌ Error deleting article: {e}")
            await self._log_operation(
                level="ERROR",
                event_type="article_deletion_failed",
                message=f"Failed to delete article {article_id}: {str(e)}",
                metadata={"error": str(e), "article_id": article_id}
            )
            raise ArticleServiceError(f"Failed to delete article: {str(e)}")
    
    async def get_user_articles(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ArticleResponse]:
        """
        Получить все артикулы пользователя
        
        Args:
            user_id: UUID пользователя
            status: Фильтр по статусу (active, inactive, error)
            limit: Максимум записей (default: 100)
            offset: Смещение для пагинации (default: 0)
            
        Returns:
            Список ArticleResponse
        """
        try:
            query = self.supabase.table("ozon_scraper_articles").select(
                "*"
            ).eq("user_id", user_id).order("created_at", desc=True).limit(limit).offset(offset)
            
            if status:
                query = query.eq("status", status)
            
            result = query.execute()
            
            articles = [ArticleResponse(**item) for item in result.data]
            
            logger.info(f"📋 Found {len(articles)} articles for user {user_id}")
            
            return articles
            
        except Exception as e:
            logger.error(f"❌ Error fetching user articles: {e}")
            raise ArticleServiceError(f"Failed to fetch articles: {str(e)}")
    
    async def update_article_data(self, article_id: str) -> ArticleResponse:
        """
        Обновить данные артикула с OZON
        
        Args:
            article_id: UUID артикула
            
        Returns:
            ArticleResponse с обновленными данными
            
        Raises:
            ArticleNotFoundError: Если артикул не найден
            ArticleServiceError: При других ошибках
        """
        try:
            # Получаем артикул
            article = self.supabase.table("ozon_scraper_articles").select("*").eq(
                "id", article_id
            ).execute()
            
            if not article.data:
                raise ArticleNotFoundError(f"Article {article_id} not found")
            
            article_data = article.data[0]
            article_number = article_data["article_number"]
            
            logger.info(f"🔄 Updating article data: {article_number}")
            
            # Получаем свежие данные с OZON
            try:
                product = await self.ozon_service.get_product_info(article_number, use_cache=False)
                
                if product:
                    last_check_data = product.to_dict()
                    status = "active"
                    is_problematic = False
                    logger.success(f"✅ Product data updated: {product.name}")
                else:
                    logger.warning(f"⚠️  Product not found on OZON: {article_number}")
                    status = "error"
                    is_problematic = True
                    last_check_data = {
                        "error": "Product not found on OZON",
                        "checked_at": datetime.now().isoformat()
                    }
                    
            except Exception as e:
                logger.error(f"❌ Failed to fetch OZON data: {e}")
                status = "error"
                is_problematic = True
                last_check_data = {
                    "error": str(e),
                    "checked_at": datetime.now().isoformat()
                    }
            
            # Преобразуем HttpUrl в строки для сохранения
            image_url_str = str(product.image_url) if product and product.image_url else None
            product_url_str = str(product.url) if product and product.url else None
            
            # Обновляем в БД с заполнением всех полей
            update_data = {
                "last_check_data": last_check_data,
                "status": status,
                "is_problematic": is_problematic,
                "updated_at": datetime.now().isoformat(),
                # Обновляем отдельные поля из product если данные получены
                "name": product.name if product else None,
                "price": product.price if product else None,
                "old_price": product.old_price if product else None,
                "normal_price": product.normal_price if product else None,
                "ozon_card_price": product.ozon_card_price if product else None,
                "average_price_7days": product.average_price_7days if product else None,
                "rating": product.rating if product else None,
                "reviews_count": product.reviews_count if product else None,
                "available": product.available if product else True,
                "image_url": image_url_str,
                "product_url": product_url_str,
                "last_check": datetime.now().isoformat() if product else None,
                "price_updated_at": datetime.now().isoformat() if product else None
            }
            
            result = self.supabase.table("ozon_scraper_articles").update(
                update_data
            ).eq("id", article_id).execute()
            
            if not result.data:
                raise ArticleServiceError("Failed to update article in database")
            
            updated_article = result.data[0]
            
            # Логируем обновление
            await self._log_operation(
                level="INFO",
                event_type="article_updated",
                message=f"Article {article_number} data updated",
                user_id=article_data["user_id"],
                article_id=article_id,
                metadata={
                    "article_number": article_number,
                    "status": status,
                    "is_problematic": is_problematic
                }
            )
            
            logger.success(f"✅ Article updated: {article_number}")
            
            return ArticleResponse(**updated_article)
            
        except ArticleNotFoundError:
            raise
        except Exception as e:
            logger.error(f"❌ Error updating article: {e}")
            await self._log_operation(
                level="ERROR",
                event_type="article_update_failed",
                message=f"Failed to update article {article_id}: {str(e)}",
                metadata={"error": str(e), "article_id": article_id}
            )
            raise ArticleServiceError(f"Failed to update article: {str(e)}")
    
    async def check_article_status(self, article_id: str) -> ArticleCheckResponse:
        """
        Проверить статус артикула на OZON (без сохранения в БД)
        
        Args:
            article_id: UUID артикула
            
        Returns:
            ArticleCheckResponse с актуальными данными
            
        Raises:
            ArticleNotFoundError: Если артикул не найден
        """
        try:
            # Получаем артикул
            article = self.supabase.table("ozon_scraper_articles").select("*").eq(
                "id", article_id
            ).execute()
            
            if not article.data:
                raise ArticleNotFoundError(f"Article {article_id} not found")
            
            article_data = article.data[0]
            article_number = article_data["article_number"]
            
            logger.info(f"🔍 Checking article status: {article_number}")
            
            # Получаем данные с OZON (без кэша)
            product = await self.ozon_service.get_product_info(article_number, use_cache=False)
            
            if not product:
                return ArticleCheckResponse(
                    article_id=article_id,
                    article_number=article_number,
                    available=False,
                    price=None,
                    old_price=None,
                    in_stock=False,
                    last_check=datetime.now(),
                    error="Product not found on OZON"
                )
            
            # Формируем ответ
            return ArticleCheckResponse(
                article_id=article_id,
                article_number=article_number,
                available=product.available,
                price=product.price,
                old_price=product.old_price,
                in_stock=product.available,
                rating=product.rating,
                reviews_count=product.reviews_count,
                last_check=datetime.now(),
                product_url=str(product.url) if product.url else None
            )
            
        except ArticleNotFoundError:
            raise
        except Exception as e:
            logger.error(f"❌ Error checking article status: {e}")
            raise ArticleServiceError(f"Failed to check article: {str(e)}")


# ==================== Singleton ====================

_article_service_instance: Optional[ArticleService] = None


def get_article_service() -> ArticleService:
    """
    Получить singleton экземпляр ArticleService
    
    Returns:
        ArticleService instance
    """
    global _article_service_instance
    if _article_service_instance is None:
        _article_service_instance = ArticleService()
    return _article_service_instance

