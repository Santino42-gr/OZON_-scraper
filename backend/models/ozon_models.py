"""
Pydantic модели для OZON Scraper

Модели для валидации и сериализации данных полученных через web scraping.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, HttpUrl, validator


class ProductAvailability(str, Enum):
    """Статус наличия товара"""
    AVAILABLE = "available"
    OUT_OF_STOCK = "out_of_stock"
    LIMITED = "limited"
    PRE_ORDER = "pre_order"
    UNKNOWN = "unknown"


class ScrapingSource(str, Enum):
    """Источник данных scraping"""
    PLAYWRIGHT = "playwright"
    HTTPX = "httpx"
    CACHE = "cache"
    MANUAL = "manual"


# ==================== Основные модели товара ====================

class ProductPriceDetailed(BaseModel):
    """
    Детальная информация о ценах товара
    
    Содержит все типы цен, доступных на OZON
    """
    article: str = Field(..., description="Артикул товара")
    
    # Различные типы цен
    price: Optional[float] = Field(None, description="Текущая основная цена", ge=0)
    normal_price: Optional[float] = Field(None, description="Цена без Ozon Card", ge=0)
    ozon_card_price: Optional[float] = Field(None, description="Цена с Ozon Card", ge=0)
    old_price: Optional[float] = Field(None, description="Старая цена (перечеркнутая)", ge=0)
    
    # Средняя цена за период
    average_price_7days: Optional[float] = Field(None, description="Средняя цена за 7 дней", ge=0)
    
    # Метаданные
    currency: str = Field("RUB", description="Валюта")
    last_updated: datetime = Field(default_factory=datetime.now, description="Время последнего обновления")
    
    class Config:
        json_schema_extra = {
            "example": {
                "article": "123456789",
                "price": 1999.00,
                "normal_price": 1999.00,
                "ozon_card_price": 1799.00,
                "old_price": 2499.00,
                "average_price_7days": 1950.00,
                "currency": "RUB",
                "last_updated": "2025-10-20T12:00:00"
            }
        }


class ProductStock(BaseModel):
    """Информация об остатках товара"""
    article: str = Field(..., description="Артикул товара")
    availability: ProductAvailability = Field(ProductAvailability.UNKNOWN, description="Статус наличия")
    stock_count: Optional[int] = Field(None, description="Количество на складе", ge=0)
    last_updated: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_schema_extra = {
            "example": {
                "article": "123456789",
                "availability": "available",
                "stock_count": 10,
                "last_updated": "2025-10-20T12:00:00"
            }
        }


class ProductRating(BaseModel):
    """Информация о рейтинге товара"""
    article: str = Field(..., description="Артикул товара")
    rating: Optional[float] = Field(None, description="Рейтинг (0-5)", ge=0, le=5)
    reviews_count: Optional[int] = Field(None, description="Количество отзывов", ge=0)
    last_updated: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_schema_extra = {
            "example": {
                "article": "123456789",
                "rating": 4.5,
                "reviews_count": 123,
                "last_updated": "2025-10-20T12:00:00"
            }
        }


class ProductInfo(BaseModel):
    """
    Полная информация о товаре OZON
    
    Агрегирует все данные полученные через scraping
    """
    # Основная информация
    article: str = Field(..., description="Артикул товара")
    name: Optional[str] = Field(None, description="Название товара")
    
    # Цены
    price: Optional[float] = Field(None, description="Текущая цена", ge=0)
    old_price: Optional[float] = Field(None, description="Старая цена", ge=0)
    normal_price: Optional[float] = Field(None, description="Цена без Ozon Card", ge=0)
    ozon_card_price: Optional[float] = Field(None, description="Цена с Ozon Card", ge=0)
    average_price_7days: Optional[float] = Field(None, description="Средняя за 7 дней", ge=0)
    
    # Рейтинг
    rating: Optional[float] = Field(None, description="Рейтинг", ge=0, le=5)
    reviews_count: Optional[int] = Field(None, description="Количество отзывов", ge=0)
    
    # Наличие
    availability: ProductAvailability = Field(ProductAvailability.UNKNOWN)
    stock_count: Optional[int] = Field(None, ge=0)
    
    # Изображения
    image_url: Optional[HttpUrl] = Field(None, description="Основное изображение")
    images: List[HttpUrl] = Field(default_factory=list, description="Все изображения")
    
    # Ссылки
    url: Optional[HttpUrl] = Field(None, description="URL товара на OZON")
    product_id: Optional[str] = Field(None, description="ID товара на OZON")
    
    # Метаданные scraping
    last_check: datetime = Field(default_factory=datetime.now, description="Время последней проверки")
    fetch_time_ms: Optional[int] = Field(None, description="Время выполнения scraping (мс)", ge=0)
    source: ScrapingSource = Field(ScrapingSource.PLAYWRIGHT, description="Источник данных")
    
    # Дополнительная информация
    category: Optional[str] = Field(None, description="Категория товара")
    brand: Optional[str] = Field(None, description="Бренд")
    seller_name: Optional[str] = Field(None, description="Название продавца")
    
    @property
    def available(self) -> bool:
        """Товар в наличии"""
        return self.availability == ProductAvailability.AVAILABLE
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать в словарь"""
        return {
            "article": self.article,
            "name": self.name,
            "price": self.price,
            "old_price": self.old_price,
            "normal_price": self.normal_price,
            "ozon_card_price": self.ozon_card_price,
            "average_price_7days": self.average_price_7days,
            "rating": self.rating,
            "reviews_count": self.reviews_count,
            "availability": self.availability.value if self.availability else None,
            "available": self.available,
            "stock_count": self.stock_count,
            "image_url": str(self.image_url) if self.image_url else None,
            "images": [str(img) for img in self.images],
            "url": str(self.url) if self.url else None,
            "product_id": self.product_id,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "fetch_time_ms": self.fetch_time_ms,
            "source": self.source.value if self.source else None,
            "category": self.category,
            "brand": self.brand,
            "seller_name": self.seller_name
        }
    
    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "article": "123456789",
                "name": "Смартфон Apple iPhone 15 Pro 128GB",
                "price": 89999.00,
                "old_price": 99999.00,
                "normal_price": 89999.00,
                "ozon_card_price": 85999.00,
                "average_price_7days": 88500.00,
                "rating": 4.8,
                "reviews_count": 256,
                "availability": "available",
                "stock_count": 5,
                "image_url": "https://cdn.ozon.ru/product.jpg",
                "url": "https://www.ozon.ru/product/123456789",
                "last_check": "2025-10-20T12:00:00",
                "source": "playwright"
            }
        }


# ==================== Логирование и результаты ====================

class ScrapingResult(BaseModel):
    """
    Результат выполнения scraping
    
    Используется для передачи результатов между методами
    """
    success: bool = Field(..., description="Успешно ли выполнен scraping")
    article: str = Field(..., description="Артикул товара")
    product_info: Optional[ProductInfo] = Field(None, description="Информация о товаре")
    
    # Информация об ошибке
    error_message: Optional[str] = Field(None, description="Сообщение об ошибке")
    error_traceback: Optional[str] = Field(None, description="Traceback ошибки")
    
    # Метаданные
    start_time: datetime = Field(..., description="Время начала")
    end_time: datetime = Field(..., description="Время окончания")
    duration_ms: int = Field(..., description="Длительность (мс)", ge=0)
    retry_count: int = Field(0, description="Количество повторов", ge=0)
    source: ScrapingSource = Field(ScrapingSource.PLAYWRIGHT)
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "article": "123456789",
                "product_info": {"article": "123456789", "name": "Product"},
                "start_time": "2025-10-20T12:00:00",
                "end_time": "2025-10-20T12:00:05",
                "duration_ms": 5000,
                "retry_count": 0,
                "source": "playwright"
            }
        }


class OzonRequestLog(BaseModel):
    """
    Лог запроса к OZON
    
    Сохраняется в таблицу ozon_scraper_logs
    """
    request_id: str = Field(..., description="Уникальный ID запроса")
    method: str = Field(..., description="Метод scraping (get_product_info, etc)")
    article: str = Field(..., description="Артикул товара")
    
    # Результат
    success: bool = Field(..., description="Успешно ли выполнен запрос")
    status_code: Optional[int] = Field(None, description="HTTP статус код")
    
    # Timing
    start_time: datetime = Field(..., description="Время начала")
    end_time: datetime = Field(..., description="Время окончания")
    duration_ms: int = Field(..., description="Длительность (мс)", ge=0)
    
    # Метаданные
    source: ScrapingSource = Field(ScrapingSource.PLAYWRIGHT)
    cache_hit: bool = Field(False, description="Взято из кэша")
    retry_count: int = Field(0, description="Количество повторов", ge=0)
    
    # Ошибки
    error_message: Optional[str] = Field(None)
    error_traceback: Optional[str] = Field(None)
    
    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "method": "get_product_info",
                "article": "123456789",
                "success": True,
                "status_code": 200,
                "start_time": "2025-10-20T12:00:00",
                "end_time": "2025-10-20T12:00:05",
                "duration_ms": 5000,
                "source": "playwright",
                "cache_hit": False,
                "retry_count": 0
            }
        }


# ==================== История цен ====================

class PriceHistory(BaseModel):
    """
    Запись истории цен
    
    Соответствует таблице ozon_scraper_price_history
    """
    article_number: str = Field(..., description="Артикул товара")
    
    # Цены
    price: Optional[float] = Field(None, ge=0)
    normal_price: Optional[float] = Field(None, ge=0)
    ozon_card_price: Optional[float] = Field(None, ge=0)
    old_price: Optional[float] = Field(None, ge=0)
    
    # Дата
    price_date: datetime = Field(default_factory=datetime.now)
    
    # Метаданные
    source: str = Field("scraping", description="Источник данных")
    scraping_success: bool = Field(True)
    scraping_duration_ms: Optional[int] = Field(None, ge=0)
    
    # Дополнительно
    product_available: bool = Field(True)
    rating: Optional[float] = Field(None, ge=0, le=5)
    reviews_count: Optional[int] = Field(None, ge=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "article_number": "123456789",
                "price": 1999.00,
                "normal_price": 1999.00,
                "ozon_card_price": 1799.00,
                "old_price": 2499.00,
                "price_date": "2025-10-20T12:00:00",
                "source": "scraping",
                "scraping_success": True,
                "product_available": True
            }
        }


class PriceHistoryStats(BaseModel):
    """
    Статистика истории цен
    
    Результат SQL функции get_average_price_7days()
    """
    article_number: str
    avg_price: Optional[float] = Field(None, ge=0)
    avg_normal_price: Optional[float] = Field(None, ge=0)
    avg_ozon_card_price: Optional[float] = Field(None, ge=0)
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    data_points: int = Field(0, ge=0, description="Количество точек данных")
    first_date: Optional[datetime] = None
    last_date: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "article_number": "123456789",
                "avg_price": 1950.00,
                "avg_normal_price": 1950.00,
                "avg_ozon_card_price": 1750.00,
                "min_price": 1899.00,
                "max_price": 1999.00,
                "data_points": 7,
                "first_date": "2025-10-13T12:00:00",
                "last_date": "2025-10-20T12:00:00"
            }
        }


# ==================== Поиск ====================

class OzonSearchResult(BaseModel):
    """Результат поиска товара на OZON"""
    article: str
    name: str
    price: Optional[float] = None
    image_url: Optional[HttpUrl] = None
    url: HttpUrl
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "article": "123456789",
                "name": "Товар",
                "price": 1999.00,
                "url": "https://www.ozon.ru/product/123456789",
                "rating": 4.5,
                "reviews_count": 100
            }
        }


# ==================== Ошибки ====================

class OzonAPIError(BaseModel):
    """Ошибка при работе с OZON"""
    error_type: str = Field(..., description="Тип ошибки")
    message: str = Field(..., description="Сообщение об ошибке")
    article: Optional[str] = Field(None)
    status_code: Optional[int] = Field(None)
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_schema_extra = {
            "example": {
                "error_type": "ScrapingError",
                "message": "Failed to scrape product: 403 Forbidden",
                "article": "123456789",
                "status_code": 403,
                "timestamp": "2025-10-20T12:00:00"
            }
        }

