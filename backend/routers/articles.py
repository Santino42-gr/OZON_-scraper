"""
Articles Router
API endpoints для управления артикулами OZON
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime

from models.article import (
    ArticleCreate,
    ArticleResponse,
    ArticleUpdate,
    ArticleCheckResponse
)
from database import get_supabase_client
from services.ozon_service import get_ozon_service
from loguru import logger

router = APIRouter()


@router.post("/", response_model=ArticleResponse, status_code=status.HTTP_201_CREATED)
async def create_article(article: ArticleCreate):
    """
    Добавить новый артикул для мониторинга
    
    - **article_number**: Артикул товара OZON
    - **user_id**: UUID пользователя
    """
    try:
        supabase = get_supabase_client()
        
        # Проверяем, не добавлен ли уже этот артикул этим пользователем
        existing = supabase.table("ozon_scraper_articles").select("*").eq(
            "article_number", article.article_number
        ).eq("user_id", article.user_id).execute()
        
        if existing.data:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Артикул уже добавлен этим пользователем"
            )
        
        # Проверяем артикул через OzonService
        ozon = get_ozon_service()
        product_info = await ozon.get_product_info(article.article_number)
        
        if not product_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Товар не найден в OZON"
            )
        
        # Рассчитываем СПП метрики
        # Note: average_price_7days будет None для новых артикулов (нет истории)
        from services.spp_calculator import calculate_spp_metrics
        spp_metrics = calculate_spp_metrics(
            product_info.average_price_7days,
            product_info.normal_price,
            product_info.ozon_card_price
        )
        
        # Сохраняем в БД
        # Конвертируем HttpUrl объекты в строки для сериализации
        image_url_str = str(product_info.image_url) if product_info.image_url else None
        product_url_str = str(product_info.url) if product_info.url else None
        
        # Сохраняем дополнительные данные в last_check_data (JSONB)
        last_check_data = {
            "brand": product_info.brand,
            "category": product_info.category,
            "seller_name": product_info.seller_name,
            "stock_count": product_info.stock_count,
            "fetch_time_ms": product_info.fetch_time_ms,
            "source": str(product_info.source) if product_info.source else None
        }
        
        data = {
            "article_number": article.article_number,
            "user_id": article.user_id,
            "name": product_info.name,
            "price": product_info.price,
            "old_price": product_info.old_price,
            "normal_price": product_info.normal_price,
            "ozon_card_price": product_info.ozon_card_price,
            "average_price_7days": product_info.average_price_7days,
            "spp1": spp_metrics["spp1"],
            "spp2": spp_metrics["spp2"],
            "spp_total": spp_metrics["spp_total"],
            "rating": product_info.rating,
            "reviews_count": product_info.reviews_count,
            "available": product_info.available,
            "image_url": image_url_str,
            "product_url": product_url_str,
            "last_check_data": last_check_data,
            "status": "active",
            "last_check": datetime.now().isoformat(),
            "price_updated_at": datetime.now().isoformat()
        }
        
        result = supabase.table("ozon_scraper_articles").insert(data).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка при сохранении артикула"
            )
        
        logger.info(f"Артикул {article.article_number} добавлен пользователем {article.user_id}")
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при создании артикула: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сервера: {str(e)}"
        )


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: str):
    """
    Получить информацию об артикуле по ID
    
    - **article_id**: UUID артикула
    """
    try:
        supabase = get_supabase_client()
        result = supabase.table("ozon_scraper_articles").select("*").eq("id", article_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Артикул не найден"
            )
        
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении артикула: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сервера: {str(e)}"
        )


@router.get("/")
async def list_articles(
    user_id: Optional[str] = Query(None, description="UUID пользователя (для фильтрации)"),
    status: Optional[str] = Query(None, description="Статус артикулов (active/inactive/error/all)"),
    status_filter: Optional[str] = Query(None, description="Альтернативное имя для status"),
    search: Optional[str] = Query(None, description="Поиск по артикулу или названию"),
    limit: int = Query(100, le=1000, description="Количество записей (max 1000)"),
    offset: int = Query(0, ge=0, description="Смещение для пагинации"),
    skip: Optional[int] = Query(None, description="Альтернативное смещение (используется вместо offset)")
) -> Dict[str, Any]:
    """
    Получить список артикулов
    
    Возвращает формат с пагинацией: {items: [], total: int}
    """
    try:
        supabase = get_supabase_client()
        
        # Используем skip если передан (для совместимости с фронтендом)
        actual_offset = skip if skip is not None else offset
        
        # Определяем статус фильтр (поддерживаем оба варианта названия параметра)
        actual_status = status if status is not None else status_filter
        
        # Строим запрос для получения артикулов
        query = supabase.table("ozon_scraper_articles").select("*")
        
        # Применяем фильтры
        if user_id:
            query = query.eq("user_id", user_id)
        
        if actual_status and actual_status != "all":
            query = query.eq("status", actual_status)
        
        # Поиск по артикулу или названию
        if search:
            # Supabase не поддерживает OR напрямую, поэтому используем фильтр по артикулу
            # Для полноценного поиска по названию нужен был бы другой подход
            query = query.ilike("article_number", f"%{search}%")
        
        # Получаем данные с пагинацией
        result = query.order("created_at", desc=True).range(actual_offset, actual_offset + limit - 1).execute()
        
        # Получаем общее количество для подсчета
        count_query = supabase.table("ozon_scraper_articles").select("id", count="exact")
        if user_id:
            count_query = count_query.eq("user_id", user_id)
        if actual_status and actual_status != "all":
            count_query = count_query.eq("status", actual_status)
        if search:
            count_query = count_query.ilike("article_number", f"%{search}%")
        
        count_result = count_query.execute()
        # Supabase возвращает count как атрибут объекта, но может быть None
        total_count = getattr(count_result, 'count', None)
        if total_count is None:
            # Если count не доступен, используем длину данных (приблизительно)
            total_count = len(result.data) if result.data else 0
        
        # Получаем уникальные user_id для запроса пользователей
        user_ids = set()
        if result.data:
            for article in result.data:
                if article.get("user_id"):
                    user_ids.add(article.get("user_id"))
        
        # Получаем данные пользователей одним запросом
        users_map = {}
        if user_ids:
            users_result = supabase.table("ozon_scraper_users").select("id, telegram_id, telegram_username").in_("id", list(user_ids)).execute()
            if users_result.data:
                for user in users_result.data:
                    users_map[user.get("id")] = {
                        "id": user.get("id"),
                        "username": user.get("telegram_username") or f"User {user.get('telegram_id')}",
                        "telegram_id": user.get("telegram_id")
                    }
        
        # Обрабатываем данные и обогащаем информацией о пользователе
        items = []
        if result.data:
            for article in result.data:
                # Добавляем информацию о пользователе
                article_user_id = article.get("user_id")
                if article_user_id and article_user_id in users_map:
                    article["user"] = users_map[article_user_id]
                else:
                    # Если пользователь не найден, создаем пустой объект
                    article["user"] = {
                        "id": article_user_id,
                        "username": "Unknown",
                        "telegram_id": None
                    }
                
                # Добавляем last_checked_at если есть last_check
                if article.get("last_check"):
                    article["last_checked_at"] = article.get("last_check")
                
                items.append(article)
        
        return {
            "items": items,
            "total": total_count
        }
        
    except Exception as e:
        logger.error(f"Ошибка при получении списка артикулов: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сервера: {str(e)}"
        )


@router.patch("/{article_id}", response_model=ArticleResponse)
async def update_article(article_id: str, article_update: ArticleUpdate):
    """
    Обновить данные артикула
    
    - **article_id**: UUID артикула
    """
    try:
        supabase = get_supabase_client()
        
        # Проверяем существование артикула
        existing = supabase.table("ozon_scraper_articles").select("*").eq("id", article_id).execute()
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Артикул не найден"
            )
        
        # Обновляем только переданные поля
        update_data = article_update.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нет данных для обновления"
            )
        
        update_data["updated_at"] = datetime.now().isoformat()
        
        result = supabase.table("ozon_scraper_articles").update(update_data).eq("id", article_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка при обновлении артикула"
            )
        
        logger.info(f"Артикул {article_id} обновлен")
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при обновлении артикула: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сервера: {str(e)}"
        )


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(article_id: str):
    """
    Удалить артикул
    
    - **article_id**: UUID артикула
    """
    try:
        supabase = get_supabase_client()
        
        # Проверяем существование
        existing = supabase.table("ozon_scraper_articles").select("id").eq("id", article_id).execute()
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Артикул не найден"
            )
        
        # Удаляем
        supabase.table("ozon_scraper_articles").delete().eq("id", article_id).execute()
        
        logger.info(f"Артикул {article_id} удален")
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при удалении артикула: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сервера: {str(e)}"
        )


@router.post("/{article_id}/check", response_model=ArticleCheckResponse)
async def check_article(article_id: str):
    """
    Проверить актуальность данных артикула в OZON
    
    - **article_id**: UUID артикула
    """
    try:
        supabase = get_supabase_client()
        
        # Получаем артикул из БД
        result = supabase.table("ozon_scraper_articles").select("*").eq("id", article_id).execute()
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Артикул не найден"
            )
        
        article = result.data[0]
        
        # Проверяем через OzonService
        ozon = get_ozon_service()
        product_info = await ozon.get_product_info(article["article_number"], use_cache=False)
        
        checked_at = datetime.now()
        
        if not product_info:
            # Товар не найден
            logger.warning(f"Артикул {article['article_number']} не найден в OZON")
            return ArticleCheckResponse(
                article_id=article_id,
                article_number=article["article_number"],
                checked_at=checked_at,
                success=False,
                error="Товар не найден в OZON"
            )
        
        # Обновляем данные в БД
        # Конвертируем HttpUrl объекты в строки для сериализации
        image_url_str = str(product_info.image_url) if product_info.image_url else None
        product_url_str = str(product_info.url) if product_info.url else None
        
        # Обновляем last_check_data (JSONB)
        last_check_data = {
            "brand": product_info.brand,
            "category": product_info.category,
            "seller_name": product_info.seller_name,
            "stock_count": product_info.stock_count,
            "fetch_time_ms": product_info.fetch_time_ms,
            "source": str(product_info.source) if product_info.source else None
        }
        
        update_data = {
            "name": product_info.name,
            "price": product_info.price,
            "old_price": product_info.old_price,
            "rating": product_info.rating,
            "reviews_count": product_info.reviews_count,
            "available": product_info.available,
            "image_url": image_url_str,
            "product_url": product_url_str,
            "last_check_data": last_check_data,
            "last_check": checked_at.isoformat(),
            "updated_at": checked_at.isoformat()
        }
        
        supabase.table("ozon_scraper_articles").update(update_data).eq("id", article_id).execute()
        
        logger.info(f"Артикул {article['article_number']} проверен и обновлен")
        
        return ArticleCheckResponse(
            article_id=article_id,
            article_number=article["article_number"],
            checked_at=checked_at,
            success=True,
            data={
                "article_number": article["article_number"],
                "name": product_info.name,
                "price": product_info.price,
                "old_price": product_info.old_price,
                "rating": product_info.rating,
                "reviews_count": product_info.reviews_count,
                "available": product_info.available,
                "image_url": image_url_str,
                "product_url": product_url_str
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при проверке артикула: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сервера: {str(e)}"
        )

