"""
Report Models
Pydantic модели для работы с отчетами
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class ReportRequest(BaseModel):
    """Модель запроса на генерацию отчета"""
    article_ids: List[str] = Field(..., description="Список ID артикулов для отчета", min_length=1)
    report_type: str = Field("summary", description="Тип отчета (summary/detailed/comparison)")
    include_history: bool = Field(False, description="Включить историю изменений")
    date_from: Optional[datetime] = Field(None, description="Начальная дата для истории")
    date_to: Optional[datetime] = Field(None, description="Конечная дата для истории")


class ReportData(BaseModel):
    """Данные отчета"""
    articles: List[Dict[str, Any]] = Field(..., description="Данные артикулов")
    summary: Dict[str, Any] = Field(..., description="Сводная информация")
    statistics: Dict[str, Any] = Field(..., description="Статистика")
    generated_at: datetime = Field(default_factory=datetime.now, description="Время генерации")


class ReportResponse(BaseModel):
    """Модель ответа с отчетом"""
    id: str = Field(..., description="UUID отчета")
    user_id: str = Field(..., description="UUID пользователя")
    report_type: str = Field(..., description="Тип отчета")
    report_data: ReportData = Field(..., description="Данные отчета")
    created_at: datetime = Field(..., description="Дата создания")
    
    class Config:
        from_attributes = True


class ReportSummary(BaseModel):
    """Краткая информация об отчете"""
    id: str
    report_type: str
    articles_count: int
    created_at: datetime

