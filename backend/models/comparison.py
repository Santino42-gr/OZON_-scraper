"""
Comparison Models
Pydantic модели для функционала сравнения артикулов
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
from enum import Enum


# =====================================================
# Enums
# =====================================================

class ArticleRole(str, Enum):
    """Роль артикула в группе сравнения"""
    OWN = "own"              # Свой товар
    COMPETITOR = "competitor"  # Конкурент
    ITEM = "item"            # Обычный товар


class GroupType(str, Enum):
    """Тип группы артикулов"""
    COMPARISON = "comparison"  # Сравнение (свой vs конкурент)
    VARIANTS = "variants"      # Варианты одного товара
    SIMILAR = "similar"        # Похожие товары


class CompetitivenessGrade(str, Enum):
    """Грейды конкурентоспособности"""
    A = "A"  # 0.85-1.00 - Отличная
    B = "B"  # 0.70-0.84 - Хорошая
    C = "C"  # 0.50-0.69 - Средняя
    D = "D"  # 0.30-0.49 - Ниже среднего
    F = "F"  # 0.00-0.29 - Плохая


# =====================================================
# Article Group Models
# =====================================================

class ArticleGroupCreate(BaseModel):
    """Модель для создания группы сравнения"""
    name: Optional[str] = Field(None, description="Название группы (опционально)")
    group_type: GroupType = Field(GroupType.COMPARISON, description="Тип группы")


class ArticleGroupUpdate(BaseModel):
    """Модель для обновления группы"""
    name: Optional[str] = Field(None, description="Новое название группы")


class ArticleGroupResponse(BaseModel):
    """Модель ответа с информацией о группе"""
    id: str = Field(..., description="UUID группы")
    user_id: str = Field(..., description="UUID пользователя-владельца")
    name: Optional[str] = Field(None, description="Название группы")
    group_type: GroupType = Field(..., description="Тип группы")
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: datetime = Field(..., description="Дата последнего обновления")
    members_count: Optional[int] = Field(None, description="Количество артикулов в группе")

    class Config:
        from_attributes = True


# =====================================================
# Group Member Models
# =====================================================

class ArticleGroupMemberCreate(BaseModel):
    """Модель для добавления артикула в группу"""
    article_id: str = Field(..., description="UUID артикула")
    role: ArticleRole = Field(ArticleRole.ITEM, description="Роль артикула в группе")
    position: int = Field(0, description="Позиция для сортировки")


class ArticleGroupMemberResponse(BaseModel):
    """Модель члена группы с данными артикула"""
    id: str = Field(..., description="UUID записи member")
    group_id: str = Field(..., description="UUID группы")
    article_id: str = Field(..., description="UUID артикула")
    role: ArticleRole = Field(..., description="Роль артикула")
    position: int = Field(..., description="Позиция")
    added_at: datetime = Field(..., description="Дата добавления")

    class Config:
        from_attributes = True


# =====================================================
# Comparison Metrics Models
# =====================================================

class PriceDifference(BaseModel):
    """Модель разницы в ценах"""
    absolute: float = Field(..., description="Абсолютная разница в рублях")
    percentage: float = Field(..., description="Разница в процентах")
    who_cheaper: Literal["own", "competitor", "equal"] = Field(..., description="Кто дешевле")
    recommendation: Optional[str] = Field(None, description="Рекомендация по цене")


class RatingDifference(BaseModel):
    """Модель разницы в рейтингах"""
    absolute: float = Field(..., description="Абсолютная разница в рейтинге")
    percentage: float = Field(..., description="Разница в процентах")
    who_better: Literal["own", "competitor", "equal"] = Field(..., description="У кого лучше")
    recommendation: Optional[str] = Field(None, description="Рекомендация по рейтингу")


class ReviewsDifference(BaseModel):
    """Модель разницы в отзывах"""
    absolute: int = Field(..., description="Абсолютная разница в количестве")
    percentage: float = Field(..., description="Разница в процентах")
    who_more: Literal["own", "competitor", "equal"] = Field(..., description="У кого больше")
    recommendation: Optional[str] = Field(None, description="Рекомендация по отзывам")


class ComparisonMetrics(BaseModel):
    """Все метрики сравнения"""
    price: PriceDifference = Field(..., description="Разница в ценах")
    rating: RatingDifference = Field(..., description="Разница в рейтингах")
    reviews: ReviewsDifference = Field(..., description="Разница в отзывах")
    competitiveness_index: float = Field(..., description="Индекс конкурентоспособности (0-1)", ge=0, le=1)
    grade: CompetitivenessGrade = Field(..., description="Грейд конкурентоспособности")
    overall_recommendation: str = Field(..., description="Общая рекомендация")


# =====================================================
# Article Comparison Data
# =====================================================

class ArticleComparisonData(BaseModel):
    """Данные артикула для сравнения"""
    article_id: str = Field(..., description="UUID артикула")
    article_number: str = Field(..., description="Номер артикула")
    role: ArticleRole = Field(..., description="Роль в группе")
    name: Optional[str] = Field(None, description="Название товара")

    # Цены
    price: Optional[float] = Field(None, description="Текущая цена")
    old_price: Optional[float] = Field(None, description="Старая цена")
    normal_price: Optional[float] = Field(None, description="Цена без карты")
    ozon_card_price: Optional[float] = Field(None, description="Цена с картой")
    average_price_7days: Optional[float] = Field(None, description="Средняя за 7 дней")

    # Метрики
    rating: Optional[float] = Field(None, description="Рейтинг")
    reviews_count: Optional[int] = Field(None, description="Количество отзывов")

    # Дополнительно
    available: bool = Field(True, description="Наличие")
    image_url: Optional[str] = Field(None, description="URL изображения")
    product_url: Optional[str] = Field(None, description="URL товара")
    position: int = Field(0, description="Позиция в группе")

    class Config:
        from_attributes = True


# =====================================================
# Comparison Response
# =====================================================

class ComparisonResponse(BaseModel):
    """Полное сравнение группы артикулов"""
    group_id: str = Field(..., description="UUID группы")
    group_name: Optional[str] = Field(None, description="Название группы")
    group_type: GroupType = Field(..., description="Тип группы")

    own_product: Optional[ArticleComparisonData] = Field(None, description="Свой товар")
    competitors: List[ArticleComparisonData] = Field(default_factory=list, description="Конкуренты")
    other_items: List[ArticleComparisonData] = Field(default_factory=list, description="Другие товары")

    metrics: Optional[ComparisonMetrics] = Field(None, description="Метрики сравнения (для 1v1)")

    compared_at: datetime = Field(..., description="Дата сравнения")
    is_fresh: bool = Field(True, description="Актуальность данных (< 1 часа)")


# =====================================================
# Snapshot Models
# =====================================================

class ComparisonSnapshotCreate(BaseModel):
    """Модель для создания снэпшота"""
    group_id: str = Field(..., description="UUID группы")
    comparison_data: dict = Field(..., description="Данные сравнения (JSON)")
    metrics: dict = Field(..., description="Метрики (JSON)")
    competitiveness_index: float = Field(..., description="Индекс конкурентоспособности", ge=0, le=1)


class ComparisonSnapshotResponse(BaseModel):
    """Модель снэпшота из истории"""
    id: str = Field(..., description="UUID снэпшота")
    group_id: str = Field(..., description="UUID группы")
    snapshot_date: datetime = Field(..., description="Дата снимка")
    comparison_data: dict = Field(..., description="Данные сравнения")
    metrics: dict = Field(..., description="Метрики")
    competitiveness_index: float = Field(..., description="Индекс конкурентоспособности")
    created_at: datetime = Field(..., description="Дата создания записи")

    class Config:
        from_attributes = True


class ComparisonHistoryResponse(BaseModel):
    """Модель истории сравнений"""
    group_id: str = Field(..., description="UUID группы")
    snapshots: List[ComparisonSnapshotResponse] = Field(..., description="Список снэпшотов")
    total_count: int = Field(..., description="Общее количество снэпшотов")
    date_from: datetime = Field(..., description="Начало периода")
    date_to: datetime = Field(..., description="Конец периода")


# =====================================================
# Quick Create Model
# =====================================================

class QuickComparisonCreate(BaseModel):
    """Быстрое создание сравнения (1 запрос для 2 артикулов)"""
    own_article_number: str = Field(..., description="Артикул своего товара")
    competitor_article_number: str = Field(..., description="Артикул конкурента")
    group_name: Optional[str] = Field(None, description="Название группы")
    scrape_now: bool = Field(True, description="Сразу получить данные с OZON")
    report_frequency: Optional[str] = Field("once", description="Частота отчетов для создаваемых артикулов: 'once' или 'twice'")


# =====================================================
# User Statistics
# =====================================================

class UserComparisonStats(BaseModel):
    """Статистика сравнений пользователя"""
    total_groups: int = Field(0, description="Всего групп")
    comparison_groups: int = Field(0, description="Групп типа comparison")
    total_articles: int = Field(0, description="Всего артикулов в группах")
    avg_competitiveness_index: Optional[float] = Field(None, description="Средний индекс")
    last_comparison_date: Optional[datetime] = Field(None, description="Дата последнего сравнения")
