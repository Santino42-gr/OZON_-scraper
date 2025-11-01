"""
OZON Service
Сервис для получения информации о товарах OZON через web scraping.

Использует Playwright для обхода антибот систем и получения динамического контента.
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import httpx
from bs4 import BeautifulSoup

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
            use_cache: использовать кеш

        Returns:
            ProductInfo (from models.ozon_models) или None если товар не найден
        """
        # Используем реальный OzonScraper вместо заглушки
        from services.ozon_scraper import get_ozon_scraper

        try:
            scraper = get_ozon_scraper()
            product = await scraper.get_product_info(article, use_cache=use_cache)

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

    async def get_product_with_playwright(self, article: str) -> Optional[ProductInfo]:
        """
        Получить информацию о товаре используя Playwright
        Для обхода антибот систем
        
        Args:
            article: артикул товара
            
        Returns:
            ProductInfo или None
        """
        # TODO: Реализовать с Playwright после установки библиотеки
        logger.warning("Playwright implementation pending")
        return None

    async def get_product_with_httpx(self, article: str) -> Optional[ProductInfo]:
        """
        Получить информацию о товаре используя httpx (легковесный метод)
        Fallback если Playwright недоступен
        
        Args:
            article: артикул товара
            
        Returns:
            ProductInfo или None
        """
        try:
            url = self._construct_product_url(article)
            response = await self.client.get(url)
            response.raise_for_status()
            
            # Парсинг HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # TODO: Реализовать парсинг элементов страницы
            # Это требует анализа структуры HTML OZON
            
            logger.warning("httpx parsing implementation pending")
            return None

        except Exception as e:
            logger.error(f"Error fetching with httpx: {e}")
            return None


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


