"""
Articles Router
API endpoints для управления артикулами OZON
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
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
        from services.ozon_scraper import OzonScraper
        spp_metrics = OzonScraper.calculate_spp_metrics(
            product_info.average_price_7days,
            product_info.normal_price,
            product_info.ozon_card_price
        )
        
        # Сохраняем в БД
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
            "image_url": product_info.image_url,
            "product_url": product_info.url,
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


@router.get("/", response_model=List[ArticleResponse])
async def list_articles(
    user_id: Optional[str] = None,
    status_filter: Optional[str] = "active",
    limit: int = 100,
    offset: int = 0
):
    """
    Получить список артикулов
    
    - **user_id**: UUID пользователя (опционально, для фильтрации)
    - **status_filter**: Статус артикулов (active/archived/all)
    - **limit**: Количество записей (max 1000)
    - **offset**: Смещение для пагинации
    """
    try:
        supabase = get_supabase_client()
        
        query = supabase.table("ozon_scraper_articles").select("*")
        
        if user_id:
            query = query.eq("user_id", user_id)
        
        if status_filter and status_filter != "all":
            query = query.eq("status", status_filter)
        
        result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
        
        return result.data if result.data else []
        
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
        update_data = {
            "name": product_info.name,
            "price": product_info.price,
            "old_price": product_info.old_price,
            "rating": product_info.rating,
            "reviews_count": product_info.reviews_count,
            "available": product_info.available,
            "image_url": product_info.image_url,
            "product_url": product_info.url,
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
                "image_url": product_info.image_url,
                "product_url": product_info.url
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

