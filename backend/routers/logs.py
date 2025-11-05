"""
Logs Router
API endpoints для получения логов системы
"""

from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from database import get_supabase_client
from loguru import logger

router = APIRouter()


@router.get("/")
async def get_logs(
    limit: int = Query(100, le=1000, description="Количество записей (max 1000)"),
    offset: int = Query(0, ge=0, description="Смещение для пагинации"),
    level: Optional[str] = Query(None, description="Уровень лога (info/warning/error)"),
    start_date: Optional[datetime] = Query(None, description="Начальная дата"),
    end_date: Optional[datetime] = Query(None, description="Конечная дата"),
    user_id: Optional[str] = Query(None, description="Фильтр по пользователю"),
    event_type: Optional[str] = Query(None, description="Тип события")
) -> Dict[str, Any]:
    """
    Получить логи системы с фильтрацией
    
    Возвращает список логов с поддержкой пагинации и фильтров
    """
    try:
        supabase = get_supabase_client()
        
        # Строим запрос
        query = supabase.table("ozon_scraper_logs").select("*")
        
        # Применяем фильтры
        if level:
            query = query.eq("level", level.lower())
        
        if user_id:
            query = query.eq("user_id", user_id)
        
        if event_type:
            query = query.eq("event_type", event_type)
        
        if start_date:
            query = query.gte("created_at", start_date.isoformat())
        
        if end_date:
            query = query.lte("created_at", end_date.isoformat())
        
        # Получаем данные с пагинацией
        result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
        
        # Получаем общее количество (приблизительно)
        count_result = supabase.table("ozon_scraper_logs").select("id", count="exact").execute()
        total_count = count_result.count if hasattr(count_result, 'count') else len(result.data)
        
        return {
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "items": result.data if result.data else []
        }
        
    except Exception as e:
        logger.error(f"Ошибка при получении логов: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сервера: {str(e)}"
        )


@router.get("/errors")
async def get_error_logs(
    limit: int = Query(50, le=500, description="Количество записей"),
    hours: int = Query(24, description="За последние N часов")
) -> Dict[str, Any]:
    """
    Получить только логи с ошибками за указанный период
    
    - **limit**: Количество записей (max 500)
    - **hours**: За последние N часов (по умолчанию 24)
    """
    try:
        supabase = get_supabase_client()
        
        # Вычисляем дату начала
        start_date = datetime.now() - timedelta(hours=hours)
        
        # Получаем только ошибки
        result = supabase.table("ozon_scraper_logs").select("*").eq(
            "level", "error"
        ).gte(
            "created_at", start_date.isoformat()
        ).order("created_at", desc=True).limit(limit).execute()
        
        return {
            "period_hours": hours,
            "start_date": start_date.isoformat(),
            "end_date": datetime.now().isoformat(),
            "total_errors": len(result.data) if result.data else 0,
            "data": result.data if result.data else []
        }
        
    except Exception as e:
        logger.error(f"Ошибка при получении логов ошибок: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сервера: {str(e)}"
        )


@router.get("/stats")
async def get_logs_stats(hours: int = Query(24, description="За последние N часов")) -> Dict[str, Any]:
    """
    Получить статистику по логам
    
    - **hours**: За последние N часов (по умолчанию 24)
    """
    try:
        supabase = get_supabase_client()
        
        start_date = datetime.now() - timedelta(hours=hours)
        
        # Получаем все логи за период
        result = supabase.table("ozon_scraper_logs").select("level").gte(
            "created_at", start_date.isoformat()
        ).execute()
        
        if not result.data:
            return {
                "period_hours": hours,
                "total": 0,
                "by_level": {
                    "info": 0,
                    "warning": 0,
                    "error": 0
                }
            }
        
        # Подсчитываем по уровням
        logs = result.data
        by_level = {
            "info": sum(1 for log in logs if log.get("level") == "info"),
            "warning": sum(1 for log in logs if log.get("level") == "warning"),
            "error": sum(1 for log in logs if log.get("level") == "error")
        }
        
        return {
            "period_hours": hours,
            "start_date": start_date.isoformat(),
            "end_date": datetime.now().isoformat(),
            "total": len(logs),
            "by_level": by_level
        }
        
    except Exception as e:
        logger.error(f"Ошибка при получении статистики логов: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сервера: {str(e)}"
        )


@router.delete("/clear")
async def clear_old_logs(days: int = Query(30, description="Удалить логи старше N дней")) -> Dict[str, Any]:
    """
    Очистить старые логи (только для администраторов)
    
    - **days**: Удалить логи старше N дней
    """
    try:
        supabase = get_supabase_client()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Удаляем старые логи
        result = supabase.table("ozon_scraper_logs").delete().lt(
            "created_at", cutoff_date.isoformat()
        ).execute()
        
        deleted_count = len(result.data) if result.data else 0
        
        logger.info(f"Удалено {deleted_count} старых логов (старше {days} дней)")
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Ошибка при очистке логов: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сервера: {str(e)}"
        )

