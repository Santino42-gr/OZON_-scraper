"""
OZON Service
Сервис для получения информации о товарах OZON через Parser Market API.

Использует облачный сервис Parser Market для парсинга данных Ozon.
"""

import logging
from typing import Optional, Dict, Any
import httpx

# Импортируем правильную модель ProductInfo
from models.ozon_models import ProductInfo

logger = logging.getLogger(__name__)


class OzonService:
    """
    Сервис для работы с OZON
    
    Методы:
    - get_product_info: получить полную информацию о товаре
    - get_product_price: получить только цену
    - check_availability: проверить наличие
    - search_product: найти товар по артикулу
    """

    def __init__(self):
        """Инициализация сервиса"""
        self.base_url = "https://www.ozon.ru"

        # HTTP клиент для легковесных запросов
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

    async def close(self):
        """Закрыть все соединения"""
        await self.client.aclose()

    def _construct_product_url(self, article: str) -> str:
        """
        Сконструировать URL товара на OZON
        
        Args:
            article: артикул товара
            
        Returns:
            URL товара
        """
        # OZON использует формат: /product/<название>-<id>/
        # Для поиска можем использовать search
        return f"{self.base_url}/search/?text={article}"

    async def get_product_info(self, article: str, use_cache: bool = True):
        """
        Получить полную информацию о товаре

        Args:
            article: артикул товара OZON
            use_cache: использовать кеш (игнорируется для Parser Market API)

        Returns:
            ProductInfo (from models.ozon_models) или None если товар не найден
        """
        # Используем Parser Market API с методом marketid (SKU ID Ozon)
        from services.parser_market_client import get_parser_market_client

        try:
            client = get_parser_market_client()
            # Используем parse_marketid для явного указания метода поиска
            product = await client.parse_marketid(article)

            if product:
                logger.info(f"✅ Product found: {article} - {product.name}")
            else:
                logger.warning(f"⚠️  Product not found: {article}")

            return product

        except Exception as e:
            logger.error(f"❌ Error fetching product {article}: {e}")
            return None

    async def get_product_price(self, article: str) -> Optional[float]:
        """
        Получить текущую цену товара
        
        Args:
            article: артикул товара
            
        Returns:
            Цена или None
        """
        product = await self.get_product_info(article)
        return product.price if product else None

    async def check_availability(self, article: str) -> bool:
        """
        Проверить наличие товара
        
        Args:
            article: артикул товара
            
        Returns:
            True если товар в наличии
        """
        product = await self.get_product_info(article)
        return product.available if product else False

    async def search_product(self, query: str, limit: int = 10) -> list[ProductInfo]:
        """
        Поиск товаров по запросу
        
        Args:
            query: поисковый запрос
            limit: максимальное количество результатов
            
        Returns:
            Список найденных товаров
        """
        # TODO: Реализовать поиск
        logger.warning(f"Search for '{query}' - Implementation pending")
        return []

    # Удалены методы get_product_with_playwright и get_product_with_httpx
    # Теперь используется только Parser Market API через get_product_info()


# Singleton instance
_ozon_service_instance: Optional[OzonService] = None


def get_ozon_service() -> OzonService:
    """
    Получить singleton экземпляр OzonService
    
    Returns:
        OzonService instance
    """
    global _ozon_service_instance
    if _ozon_service_instance is None:
        _ozon_service_instance = OzonService()
    return _ozon_service_instance


