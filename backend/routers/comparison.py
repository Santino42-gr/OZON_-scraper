"""
Comparison Router
API endpoints для сравнения артикулов OZON
"""

from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime

from models.comparison import (
    ArticleGroupCreate,
    ArticleGroupUpdate,
    ArticleGroupResponse,
    ArticleGroupMemberCreate,
    ComparisonResponse,
    ComparisonHistoryResponse,
    QuickComparisonCreate,
    UserComparisonStats
)
from services.comparison_service import (
    ComparisonService,
    ComparisonServiceError,
    GroupNotFoundError,
    InvalidComparisonError
)
from loguru import logger

router = APIRouter()


# ==================== Group Management ====================

@router.post("/groups", response_model=ArticleGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_comparison_group(
    user_id: str,
    group_data: ArticleGroupCreate
):
    """
    Создать новую группу сравнения

    - **user_id**: UUID пользователя (query parameter)
    - **name**: Название группы (опционально)
    - **group_type**: Тип группы (comparison, variants, similar)
    """
    try:
        service = ComparisonService()
        group = await service.create_group(user_id, group_data)
        logger.info(f"✅ Comparison group created: {group.id}")
        return group

    except ComparisonServiceError as e:
        logger.error(f"Error creating group: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/groups/{group_id}", response_model=ArticleGroupResponse)
async def get_comparison_group(
    group_id: str,
    user_id: str = Query(..., description="UUID пользователя")
):
    """
    Получить информацию о группе сравнения

    - **group_id**: UUID группы
    - **user_id**: UUID пользователя (для проверки прав доступа)
    """
    try:
        service = ComparisonService()
        group = await service.get_group(group_id, user_id)
        return group

    except GroupNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group not found: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error getting group: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.delete("/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comparison_group(
    group_id: str,
    user_id: str = Query(..., description="UUID пользователя")
):
    """
    Удалить группу сравнения

    - **group_id**: UUID группы
    - **user_id**: UUID пользователя (для проверки прав доступа)
    """
    try:
        service = ComparisonService()
        success = await service.delete_group(group_id, user_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found or access denied"
            )

        logger.info(f"✅ Group deleted: {group_id}")
        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting group: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


# ==================== Group Members ====================

@router.post("/groups/{group_id}/members", status_code=status.HTTP_201_CREATED)
async def add_article_to_group(
    group_id: str,
    member_data: ArticleGroupMemberCreate
):
    """
    Добавить артикул в группу сравнения

    - **group_id**: UUID группы
    - **article_id**: UUID артикула
    - **role**: Роль артикула (own, competitor, item)
    - **position**: Позиция для сортировки
    """
    try:
        service = ComparisonService()
        success = await service.add_article_to_group(
            group_id,
            member_data.article_id,
            member_data.role,
            member_data.position
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to add article to group"
            )

        logger.info(f"✅ Article {member_data.article_id} added to group {group_id}")
        return {"message": "Article added successfully"}

    except Exception as e:
        logger.error(f"Error adding article to group: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


# ==================== Comparison ====================

@router.get("/groups/{group_id}/compare", response_model=ComparisonResponse)
async def get_comparison(
    group_id: str,
    user_id: str = Query(..., description="UUID пользователя"),
    refresh: bool = Query(False, description="Обновить данные с OZON перед сравнением")
):
    """
    Получить сравнение артикулов в группе

    Возвращает все артикулы группы с рассчитанными метриками.
    Для сравнения 1v1 (own vs competitor) также рассчитывается:
    - Разницы в ценах, рейтингах, СПП, отзывах
    - Индекс конкурентоспособности (0-1)
    - Грейд (A-F)
    - Рекомендации по улучшению

    - **group_id**: UUID группы
    - **user_id**: UUID пользователя
    - **refresh**: Обновить данные с OZON (медленнее, но актуальнее)
    """
    try:
        service = ComparisonService()
        comparison = await service.get_comparison(group_id, user_id, refresh)
        return comparison

    except GroupNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group not found: {str(e)}"
        )
    except InvalidComparisonError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid comparison: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error getting comparison: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/quick-compare", response_model=ComparisonResponse, status_code=status.HTTP_201_CREATED)
async def quick_create_comparison(
    user_id: str,
    quick_data: QuickComparisonCreate
):
    """
    Быстрое создание сравнения 1v1

    Создает группу, добавляет оба артикула, получает данные с OZON,
    и возвращает готовое сравнение с метриками - все в одном запросе.

    Это самый простой способ сравнить два товара!

    - **user_id**: UUID пользователя
    - **own_article_number**: Артикул вашего товара
    - **competitor_article_number**: Артикул конкурента
    - **group_name**: Название группы (опционально)
    - **scrape_now**: Сразу получить данные с OZON (по умолчанию true)

    Пример запроса:
    ```json
    {
      "own_article_number": "123456789",
      "competitor_article_number": "987654321",
      "group_name": "Мой товар vs Конкурент A",
      "scrape_now": true
    }
    ```

    Ответ включает:
    - Полные данные обоих товаров
    - Все метрики сравнения
    - Индекс конкурентоспособности и грейд
    - Конкретные рекомендации по улучшению
    """
    try:
        service = ComparisonService()
        comparison = await service.quick_create_comparison(user_id, quick_data)

        logger.info(f"✅ Quick comparison created: {comparison.group_id}")
        return comparison

    except ComparisonServiceError as e:
        logger.error(f"Error in quick comparison: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in quick comparison: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


# ==================== History ====================

@router.get("/groups/{group_id}/history", response_model=ComparisonHistoryResponse)
async def get_comparison_history(
    group_id: str,
    user_id: str = Query(..., description="UUID пользователя"),
    days: int = Query(30, ge=1, le=365, description="Количество дней истории (1-365)")
):
    """
    Получить историю снэпшотов сравнения

    Возвращает все сохраненные снэпшоты за указанный период.
    Позволяет отслеживать изменения цен, рейтингов и конкурентоспособности во времени.

    - **group_id**: UUID группы
    - **user_id**: UUID пользователя
    - **days**: Количество дней (от 1 до 365, по умолчанию 30)

    Используйте эти данные для:
    - Построения графиков изменений
    - Анализа трендов
    - Оценки эффективности ваших действий
    """
    try:
        service = ComparisonService()
        history = await service.get_comparison_history(group_id, user_id, days)
        return history

    except GroupNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group not found: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


# ==================== User Statistics ====================

@router.get("/users/{user_id}/stats", response_model=UserComparisonStats)
async def get_user_comparison_stats(user_id: str):
    """
    Получить статистику сравнений пользователя

    Возвращает общую статистику:
    - Количество групп сравнения
    - Количество артикулов в группах
    - Средний индекс конкурентоспособности
    - Дата последнего сравнения

    - **user_id**: UUID пользователя
    """
    try:
        service = ComparisonService()
        stats = await service.get_user_stats(user_id)
        return stats

    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


# ==================== Health Check ====================

@router.get("/health")
async def comparison_health_check():
    """
    Проверка работоспособности Comparison API

    Возвращает статус и версию модуля
    """
    return {
        "status": "healthy",
        "module": "comparison",
        "version": "1.0.0",
        "features": [
            "group_management",
            "comparison_metrics",
            "competitiveness_index",
            "snapshots",
            "recommendations"
        ]
    }
