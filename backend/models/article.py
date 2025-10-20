"""
Article Models
Pydantic модели для работы с артикулами OZON
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ArticleBase(BaseModel):
    """Базовая модель артикула"""
    article_number: str = Field(..., description="Артикул товара OZON")
    name: Optional[str] = Field(None, description="Название товара")
    price: Optional[float] = Field(None, description="Текущая цена")
    old_price: Optional[float] = Field(None, description="Старая цена (перечеркнутая)")
    normal_price: Optional[float] = Field(None, description="Цена без Ozon карты")
    ozon_card_price: Optional[float] = Field(None, description="Цена с Ozon картой")
    average_price_7days: Optional[float] = Field(None, description="Средняя цена за 7 дней")
    rating: Optional[float] = Field(None, description="Рейтинг товара")
    reviews_count: Optional[int] = Field(None, description="Количество отзывов")
    available: bool = Field(True, description="Наличие товара")
    image_url: Optional[str] = Field(None, description="URL изображения товара")
    product_url: Optional[str] = Field(None, description="URL страницы товара")


class ArticleCreate(BaseModel):
    """Модель для создания артикула"""
    article_number: str = Field(..., description="Артикул товара OZON", min_length=1)
    user_id: str = Field(..., description="ID пользователя")


class ArticleUpdate(BaseModel):
    """Модель для обновления данных артикула"""
    name: Optional[str] = None
    price: Optional[float] = None
    old_price: Optional[float] = None
    normal_price: Optional[float] = None
    ozon_card_price: Optional[float] = None
    average_price_7days: Optional[float] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    available: Optional[bool] = None
    image_url: Optional[str] = None
    product_url: Optional[str] = None


class ArticleResponse(ArticleBase):
    """Модель ответа с полной информацией об артикуле"""
    id: str = Field(..., description="UUID артикула")
    user_id: str = Field(..., description="UUID пользователя")
    created_at: datetime = Field(..., description="Дата добавления")
    updated_at: datetime = Field(..., description="Дата последнего обновления")
    last_check: Optional[datetime] = Field(None, description="Дата последней проверки")
    status: str = Field("active", description="Статус артикула (active/archived/error)")
    
    class Config:
        from_attributes = True


class ArticleCheckResponse(BaseModel):
    """Модель ответа при проверке артикула"""
    article_id: str
    article_number: str
    checked_at: datetime
    success: bool
    data: Optional[ArticleBase] = None
    error: Optional[str] = None

