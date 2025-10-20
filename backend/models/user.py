"""
User Models
Pydantic модели для работы с пользователями Telegram
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    """Базовая модель пользователя"""
    telegram_id: int = Field(..., description="Telegram ID пользователя")
    username: Optional[str] = Field(None, description="Telegram username")
    first_name: Optional[str] = Field(None, description="Имя пользователя")
    last_name: Optional[str] = Field(None, description="Фамилия пользователя")


class UserCreate(UserBase):
    """Модель для создания пользователя"""
    pass


class UserUpdate(BaseModel):
    """Модель для обновления данных пользователя"""
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_blocked: Optional[bool] = None


class UserResponse(UserBase):
    """Модель ответа с полной информацией о пользователе"""
    id: str = Field(..., description="UUID пользователя")
    created_at: datetime = Field(..., description="Дата регистрации")
    updated_at: datetime = Field(..., description="Дата последнего обновления")
    last_active: Optional[datetime] = Field(None, description="Последняя активность")
    is_blocked: bool = Field(False, description="Заблокирован ли пользователь")
    is_admin: bool = Field(False, description="Является ли администратором")
    articles_count: int = Field(0, description="Количество отслеживаемых артикулов")
    
    class Config:
        from_attributes = True


class UserStatsResponse(BaseModel):
    """Модель статистики пользователя"""
    user_id: str
    total_articles: int
    total_checks: int
    successful_checks: int
    failed_checks: int
    last_active: Optional[datetime] = None

