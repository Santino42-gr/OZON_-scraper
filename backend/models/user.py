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


class UserResponse(BaseModel):
    """Модель ответа с полной информацией о пользователе"""
    id: str = Field(..., description="UUID пользователя")
    telegram_id: int = Field(..., description="Telegram ID пользователя")
    telegram_username: Optional[str] = Field(None, description="Telegram username")
    created_at: datetime = Field(..., description="Дата регистрации")
    last_active_at: Optional[datetime] = Field(None, description="Последняя активность")
    is_blocked: bool = Field(False, description="Заблокирован ли пользователь")
    
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

