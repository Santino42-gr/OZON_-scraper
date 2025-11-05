"""
Users Router
API endpoints для управления пользователями
"""

from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional, Dict, Any
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
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
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
            # Пользователь уже существует - обновляем last_active_at и возвращаем его данные
            user_id = existing.data[0]["id"]
            update_data = {
                "last_active_at": datetime.now().isoformat(),
                "telegram_username": user.username  # Обновляем username на случай если изменился
            }

            result = supabase.table("ozon_scraper_users").update(update_data).eq(
                "id", user_id
            ).execute()

            logger.info(f"Пользователь {user.telegram_id} уже существует, обновлен last_active_at")
            return result.data[0] if result.data else existing.data[0]

        # Создаем нового пользователя
        data = {
            "telegram_id": user.telegram_id,
            "telegram_username": user.username,
            "is_blocked": False,
            "created_at": datetime.now().isoformat(),
            "last_active_at": datetime.now().isoformat()
        }

        result = supabase.table("ozon_scraper_users").insert(data).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка при создании пользователя"
            )

        logger.info(f"Пользователь {user.telegram_id} успешно зарегистрирован")
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


@router.get("/")
async def list_users(
    is_blocked: Optional[bool] = Query(None, description="Фильтр по статусу блокировки"),
    search: Optional[str] = Query(None, description="Поиск по имени или Telegram ID"),
    limit: int = Query(100, le=1000, description="Количество записей (max 1000)"),
    offset: int = Query(0, ge=0, description="Смещение для пагинации"),
    skip: Optional[int] = Query(None, description="Альтернативное смещение (используется вместо offset)")
) -> Dict[str, Any]:
    """
    Получить список пользователей (для админ-панели)
    
    Возвращает формат с пагинацией: {items: [], total: int}
    """
    try:
        supabase = get_supabase_client()
        
        # Используем skip если передан (для совместимости с фронтендом)
        actual_offset = skip if skip is not None else offset
        
        # Строим запрос для получения данных
        query = supabase.table("ozon_scraper_users").select("*")
        
        # Применяем фильтры
        if is_blocked is not None:
            query = query.eq("is_blocked", is_blocked)
        
        # Поиск по telegram_id или telegram_username
        if search:
            try:
                # Пробуем найти по telegram_id (если это число)
                telegram_id_int = int(search)
                query = query.eq("telegram_id", telegram_id_int)
            except ValueError:
                # Если не число, ищем по username
                query = query.ilike("telegram_username", f"%{search}%")
        
        # Получаем данные с пагинацией
        result = query.order("created_at", desc=True).range(actual_offset, actual_offset + limit - 1).execute()
        
        # Получаем общее количество для подсчета (применяем те же фильтры)
        count_query = supabase.table("ozon_scraper_users").select("id", count="exact")
        if is_blocked is not None:
            count_query = count_query.eq("is_blocked", is_blocked)
        if search:
            try:
                telegram_id_int = int(search)
                count_query = count_query.eq("telegram_id", telegram_id_int)
            except ValueError:
                count_query = count_query.ilike("telegram_username", f"%{search}%")
        
        count_result = count_query.execute()
        # Supabase возвращает count как атрибут объекта, но может быть None
        total_count = getattr(count_result, 'count', None)
        if total_count is None:
            # Если count не доступен, используем длину данных (приблизительно)
            total_count = len(result.data) if result.data else 0
        
        # Обогащаем данные: добавляем counts для каждого пользователя
        items = []
        if result.data:
            for user in result.data:
                user_id = user.get("id")
                
                # Подсчитываем артикулы пользователя
                articles_result = supabase.table("ozon_scraper_articles").select("id", count="exact").eq("user_id", user_id).execute()
                articles_count = articles_result.count if hasattr(articles_result, 'count') else len(articles_result.data) if articles_result.data else 0
                
                # Подсчитываем запросы (логи) пользователя
                logs_result = supabase.table("ozon_scraper_logs").select("id", count="exact").eq("user_id", user_id).execute()
                requests_count = logs_result.count if hasattr(logs_result, 'count') else len(logs_result.data) if logs_result.data else 0
                
                # Добавляем counts в объект пользователя
                user["articles_count"] = articles_count
                user["requests_count"] = requests_count
                items.append(user)
        
        return {
            "items": items,
            "total": total_count
        }
        
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


@router.patch("/{user_id}/block", response_model=UserResponse)
async def toggle_user_block(user_id: str):
    """
    Переключить статус блокировки пользователя (для админ-панели)
    
    - **user_id**: UUID пользователя
    """
    try:
        supabase = get_supabase_client()
        
        # Получаем текущий статус
        existing = supabase.table("ozon_scraper_users").select("is_blocked").eq("id", user_id).execute()
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        current_status = existing.data[0].get("is_blocked", False)
        new_status = not current_status
        
        result = supabase.table("ozon_scraper_users").update({
            "is_blocked": new_status,
            "updated_at": datetime.now().isoformat()
        }).eq("id", user_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка при обновлении статуса блокировки"
            )
        
        user_data = result.data[0]
        user_data["is_blocked"] = new_status
        logger.info(f"Пользователь {user_id} {'заблокирован' if new_status else 'разблокирован'}")
        return user_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при переключении блокировки пользователя: {e}")
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


@router.get("/{user_id}/articles")
async def get_user_articles(user_id: str) -> Dict[str, Any]:
    """
    Получить артикулы пользователя
    
    - **user_id**: UUID пользователя
    """
    try:
        supabase = get_supabase_client()
        
        # Проверяем существование пользователя
        user_result = supabase.table("ozon_scraper_users").select("id").eq("id", user_id).execute()
        if not user_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        # Получаем артикулы пользователя
        articles_result = supabase.table("ozon_scraper_articles").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        
        items = []
        if articles_result.data:
            for article in articles_result.data:
                # Добавляем last_checked_at если есть last_check
                if article.get("last_check"):
                    article["last_checked_at"] = article.get("last_check")
                items.append(article)
        
        return {
            "items": items,
            "total": len(items)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении артикулов пользователя: {e}")
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
        articles_result = supabase.table("ozon_scraper_articles").select("id").eq("user_id", user_id).execute()
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

