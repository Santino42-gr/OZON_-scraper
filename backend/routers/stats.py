"""
Statistics Router
API endpoints для получения статистики системы
"""

from fastapi import APIRouter, HTTPException, status, Query
from typing import Dict, Any, List
from datetime import datetime, timedelta

from database import get_supabase_client
from loguru import logger

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_stats() -> Dict[str, Any]:
    """
    Получить статистику для главного дашборда админ-панели
    
    Возвращает основные метрики системы:
    - Общее количество пользователей
    - Общее количество артикулов
    - Количество запросов за последние 24 часа
    - Процент успешных проверок
    - Количество ошибок за последние 24 часа
    """
    try:
        supabase = get_supabase_client()
        
        # Получаем количество пользователей
        users_result = supabase.table("ozon_scraper_users").select("id", count="exact").execute()
        total_users = len(users_result.data) if users_result.data else 0

        # Получаем количество активных пользователей (активность за последние 7 дней)
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        active_users_result = supabase.table("ozon_scraper_users").select("id").gte(
            "last_active_at", week_ago
        ).execute()
        active_users = len(active_users_result.data) if active_users_result.data else 0

        # Получаем количество артикулов
        articles_result = supabase.table("ozon_scraper_articles").select("id", count="exact").execute()
        total_articles = len(articles_result.data) if articles_result.data else 0

        # Получаем количество активных артикулов
        active_articles_result = supabase.table("ozon_scraper_articles").select("id").eq(
            "status", "active"
        ).execute()
        active_articles = len(active_articles_result.data) if active_articles_result.data else 0

        # Получаем статистику по логам за последние 24 часа
        yesterday = (datetime.now() - timedelta(hours=24)).isoformat()
        logs_result = supabase.table("ozon_scraper_logs").select("level").gte(
            "created_at", yesterday
        ).execute()
        
        total_requests = len(logs_result.data) if logs_result.data else 0
        errors_24h = sum(1 for log in logs_result.data if log.get("level") == "error") if logs_result.data else 0
        
        # Вычисляем успешность
        success_rate = ((total_requests - errors_24h) / total_requests * 100) if total_requests > 0 else 100.0
        
        return {
            "users": {
                "total": total_users,
                "active": active_users,
                "blocked": 0  # TODO: добавить подсчет заблокированных
            },
            "articles": {
                "total": total_articles,
                "active": active_articles,
                "archived": total_articles - active_articles
            },
            "activity": {
                "total_requests_24h": total_requests,
                "errors_24h": errors_24h,
                "success_rate": round(success_rate, 2)
            },
            "system": {
                "status": "operational",
                "uptime": "99.9%",  # TODO: реальный расчет uptime
                "last_check": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Ошибка при получении статистики дашборда: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сервера: {str(e)}"
        )


@router.get("/users")
async def get_user_stats(period: str = Query("week", description="Период (day/week/month)")) -> Dict[str, Any]:
    """
    Получить статистику по пользователям
    
    - **period**: Период для анализа (day/week/month)
    """
    try:
        supabase = get_supabase_client()
        
        # Определяем период
        periods = {
            "day": timedelta(days=1),
            "week": timedelta(days=7),
            "month": timedelta(days=30)
        }
        
        if period not in periods:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неверный период. Используйте: day, week или month"
            )
        
        start_date = (datetime.now() - periods[period]).isoformat()
        
        # Получаем новых пользователей за период
        new_users_result = supabase.table("ozon_scraper_users").select("*").gte(
            "created_at", start_date
        ).execute()

        # Получаем активных пользователей за период
        active_users_result = supabase.table("ozon_scraper_users").select("*").gte(
            "last_active", start_date
        ).execute()

        # Получаем всех пользователей
        all_users_result = supabase.table("ozon_scraper_users").select("*").execute()
        
        new_users = new_users_result.data if new_users_result.data else []
        active_users = active_users_result.data if active_users_result.data else []
        all_users = all_users_result.data if all_users_result.data else []
        
        return {
            "period": period,
            "start_date": start_date,
            "end_date": datetime.now().isoformat(),
            "total_users": len(all_users),
            "new_users": len(new_users),
            "active_users": len(active_users),
            "blocked_users": sum(1 for u in all_users if u.get("is_blocked")),
            "retention_rate": round(len(active_users) / len(all_users) * 100, 2) if all_users else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении статистики пользователей: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сервера: {str(e)}"
        )


@router.get("/articles")
async def get_article_stats() -> Dict[str, Any]:
    """
    Получить статистику по артикулам
    
    Возвращает:
    - Общее количество артикулов
    - Распределение по статусам
    - Средняя цена
    - Топ самых дорогих артикулов
    """
    try:
        supabase = get_supabase_client()
        
        # Получаем все артикулы
        articles_result = supabase.table("ozon_scraper_articles").select("*").execute()
        
        if not articles_result.data:
            return {
                "total": 0,
                "by_status": {"active": 0, "archived": 0, "error": 0},
                "price_stats": {
                    "average": 0,
                    "min": 0,
                    "max": 0,
                    "total_value": 0
                },
                "availability": {
                    "available": 0,
                    "unavailable": 0
                }
            }
        
        articles = articles_result.data
        
        # Подсчитываем по статусам
        by_status = {
            "active": sum(1 for a in articles if a.get("status") == "active"),
            "archived": sum(1 for a in articles if a.get("status") == "archived"),
            "error": sum(1 for a in articles if a.get("status") == "error")
        }
        
        # Статистика по ценам
        prices = [a.get("price", 0) or 0 for a in articles]
        
        price_stats = {
            "average": round(sum(prices) / len(prices), 2) if prices else 0,
            "min": min(prices) if prices else 0,
            "max": max(prices) if prices else 0,
            "total_value": sum(prices)
        }
        
        # Доступность
        availability = {
            "available": sum(1 for a in articles if a.get("available")),
            "unavailable": sum(1 for a in articles if not a.get("available"))
        }
        
        return {
            "total": len(articles),
            "by_status": by_status,
            "price_stats": price_stats,
            "availability": availability
        }
        
    except Exception as e:
        logger.error(f"Ошибка при получении статистики артикулов: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сервера: {str(e)}"
        )


@router.get("/activity")
async def get_activity_stats(hours: int = Query(24, description="За последние N часов")) -> Dict[str, Any]:
    """
    Получить статистику активности системы
    
    - **hours**: За последние N часов
    """
    try:
        supabase = get_supabase_client()
        
        start_date = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        # Получаем логи за период
        logs_result = supabase.table("ozon_scraper_logs").select("*").gte(
            "created_at", start_date
        ).execute()
        
        if not logs_result.data:
            return {
                "period_hours": hours,
                "total_events": 0,
                "by_level": {"info": 0, "warning": 0, "error": 0},
                "by_event_type": {},
                "timeline": []
            }
        
        logs = logs_result.data
        
        # Группировка по уровням
        by_level = {
            "info": sum(1 for log in logs if log.get("level") == "info"),
            "warning": sum(1 for log in logs if log.get("level") == "warning"),
            "error": sum(1 for log in logs if log.get("level") == "error")
        }
        
        # Группировка по типам событий
        event_types = {}
        for log in logs:
            event_type = log.get("event_type", "unknown")
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        return {
            "period_hours": hours,
            "start_date": start_date,
            "end_date": datetime.now().isoformat(),
            "total_events": len(logs),
            "by_level": by_level,
            "by_event_type": event_types
        }
        
    except Exception as e:
        logger.error(f"Ошибка при получении статистики активности: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сервера: {str(e)}"
        )

