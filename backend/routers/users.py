"""
Users Router
API endpoints для управления пользователями
"""

from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from datetime import datetime

from models.user import (
    UserCreate,
    UserResponse,
    UserUpdate,
    UserStatsResponse
)
from database import get_supabase_client
from loguru import logger

router = APIRouter()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    """
    Регистрация нового пользователя
    
    - **telegram_id**: Telegram ID пользователя
    - **username**: Telegram username (опционально)
    - **first_name**: Имя пользователя (опционально)
    - **last_name**: Фамилия пользователя (опционально)
    """
    try:
        supabase = get_supabase_client()
        
        # Проверяем, не зарегистрирован ли уже пользователь
        existing = supabase.table("ozon_scraper_users").select("*").eq(
            "telegram_id", user.telegram_id
        ).execute()
        
        if existing.data:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Пользователь уже зарегистрирован"
            )
        
        # Создаем пользователя
        data = {
            "telegram_id": user.telegram_id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_blocked": False,
            "is_admin": False,
            "last_active": datetime.now().isoformat()
        }
        
        result = supabase.table("ozon_scraper_users").insert(data).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка при создании пользователя"
            )
        
        logger.info(f"Пользователь {user.telegram_id} зарегистрирован")
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при создании пользователя: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сервера: {str(e)}"
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """
    Получить информацию о пользователе по ID
    
    - **user_id**: UUID пользователя
    """
    try:
        supabase = get_supabase_client()
        result = supabase.table("ozon_scraper_users").select("*").eq("id", user_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении пользователя: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сервера: {str(e)}"
        )


@router.get("/telegram/{telegram_id}", response_model=UserResponse)
async def get_user_by_telegram_id(telegram_id: int):
    """
    Получить информацию о пользователе по Telegram ID
    
    - **telegram_id**: Telegram ID пользователя
    """
    try:
        supabase = get_supabase_client()
        result = supabase.table("ozon_scraper_users").select("*").eq("telegram_id", telegram_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении пользователя: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сервера: {str(e)}"
        )


@router.get("/", response_model=List[UserResponse])
async def list_users(
    is_blocked: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    Получить список пользователей (для админ-панели)
    
    - **is_blocked**: Фильтр по статусу блокировки (опционально)
    - **limit**: Количество записей (max 1000)
    - **offset**: Смещение для пагинации
    """
    try:
        supabase = get_supabase_client()
        
        query = supabase.table("ozon_scraper_users").select("*")
        
        if is_blocked is not None:
            query = query.eq("is_blocked", is_blocked)
        
        result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
        
        return result.data if result.data else []
        
    except Exception as e:
        logger.error(f"Ошибка при получении списка пользователей: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сервера: {str(e)}"
        )


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_update: UserUpdate):
    """
    Обновить данные пользователя
    
    - **user_id**: UUID пользователя
    """
    try:
        supabase = get_supabase_client()
        
        # Проверяем существование
        existing = supabase.table("ozon_scraper_users").select("*").eq("id", user_id).execute()
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        # Обновляем только переданные поля
        update_data = user_update.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нет данных для обновления"
            )
        
        update_data["updated_at"] = datetime.now().isoformat()
        
        result = supabase.table("ozon_scraper_users").update(update_data).eq("id", user_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка при обновлении пользователя"
            )
        
        logger.info(f"Пользователь {user_id} обновлен")
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при обновлении пользователя: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сервера: {str(e)}"
        )


@router.post("/{user_id}/block", response_model=UserResponse)
async def block_user(user_id: str):
    """
    Заблокировать пользователя
    
    - **user_id**: UUID пользователя
    """
    try:
        supabase = get_supabase_client()
        
        result = supabase.table("ozon_scraper_users").update({
            "is_blocked": True,
            "updated_at": datetime.now().isoformat()
        }).eq("id", user_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        logger.info(f"Пользователь {user_id} заблокирован")
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при блокировке пользователя: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сервера: {str(e)}"
        )


@router.post("/{user_id}/unblock", response_model=UserResponse)
async def unblock_user(user_id: str):
    """
    Разблокировать пользователя
    
    - **user_id**: UUID пользователя
    """
    try:
        supabase = get_supabase_client()
        
        result = supabase.table("ozon_scraper_users").update({
            "is_blocked": False,
            "updated_at": datetime.now().isoformat()
        }).eq("id", user_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        logger.info(f"Пользователь {user_id} разблокирован")
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при разблокировке пользователя: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сервера: {str(e)}"
        )


@router.get("/{user_id}/stats", response_model=UserStatsResponse)
async def get_user_stats(user_id: str):
    """
    Получить статистику пользователя
    
    - **user_id**: UUID пользователя
    """
    try:
        supabase = get_supabase_client()
        
        # Проверяем существование пользователя
        user_result = supabase.table("ozon_scraper_users").select("*").eq("id", user_id).execute()
        if not user_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        user = user_result.data[0]
        
        # Получаем статистику по артикулам
        articles_result = supabase.table("articles").select("id").eq("user_id", user_id).execute()
        total_articles = len(articles_result.data) if articles_result.data else 0
        
        # TODO: Добавить статистику по проверкам когда будет таблица logs
        
        return UserStatsResponse(
            user_id=user_id,
            total_articles=total_articles,
            total_checks=0,
            successful_checks=0,
            failed_checks=0,
            last_active=user.get("last_active")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении статистики пользователя: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сервера: {str(e)}"
        )

