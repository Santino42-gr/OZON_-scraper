"""
Prices Router
API endpoints для работы с ценами товаров OZON
"""

from fastapi import APIRouter, HTTPException, status, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from database import get_supabase_client
from services.ozon_service import get_ozon_service
from models.ozon_models import ProductPriceDetailed, PriceHistory, PriceHistoryStats
from loguru import logger

router = APIRouter()


# ==================== Response Models ====================

class ArticlePricesResponse(BaseModel):
    """Все цены товара"""
    article_id: str
    article_number: str
    price: Optional[float] = None
    normal_price: Optional[float] = None
    ozon_card_price: Optional[float] = None
    old_price: Optional[float] = None
    average_price_7days: Optional[float] = None
    price_updated_at: Optional[datetime] = None
    currency: str = "RUB"
    
    class Config:
        json_schema_extra = {
            "example": {
                "article_id": "550e8400-e29b-41d4-a716-446655440000",
                "article_number": "123456789",
                "price": 1799.00,
                "normal_price": 1999.00,
                "ozon_card_price": 1799.00,
                "old_price": 2499.00,
                "average_price_7days": 1950.00,
                "price_updated_at": "2025-10-21T12:00:00",
                "currency": "RUB"
            }
        }


class PriceHistoryResponse(BaseModel):
    """История изменения цен"""
    article_number: str
    days: int
    total_records: int
    history: List[Dict[str, Any]]
    
    class Config:
        json_schema_extra = {
            "example": {
                "article_number": "123456789",
                "days": 7,
                "total_records": 7,
                "history": [
                    {
                        "price_date": "2025-10-21T00:00:00",
                        "price": 1799.00,
                        "normal_price": 1999.00,
                        "ozon_card_price": 1799.00,
                        "product_available": True
                    }
                ]
            }
        }


class PriceAverageResponse(BaseModel):
    """Средняя цена за период"""
    article_number: str
    days: int
    avg_price: Optional[float] = None
    avg_normal_price: Optional[float] = None
    avg_ozon_card_price: Optional[float] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    data_points: int = 0
    first_date: Optional[datetime] = None
    last_date: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "article_number": "123456789",
                "days": 7,
                "avg_price": 1950.00,
                "avg_normal_price": 1950.00,
                "avg_ozon_card_price": 1750.00,
                "min_price": 1899.00,
                "max_price": 1999.00,
                "data_points": 7,
                "first_date": "2025-10-14T00:00:00",
                "last_date": "2025-10-21T00:00:00"
            }
        }


# ==================== Endpoints ====================

@router.get("/{article_id}/prices", response_model=ArticlePricesResponse)
async def get_article_prices(article_id: str):
    """
    Получить все цены товара
    
    Возвращает все доступные типы цен:
    - Обычная цена (без Ozon Card)
    - Цена с Ozon Card
    - Старая цена (перечеркнутая)
    - Средняя цена за 7 дней
    
    Args:
        article_id: UUID артикула
        
    Returns:
        ArticlePricesResponse с детальной информацией о ценах
    """
    try:
        supabase = get_supabase_client()
        
        # Получаем артикул из БД
        response = supabase.table("ozon_scraper_articles") \
            .select("*") \
            .eq("id", article_id) \
            .execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Артикул не найден"
            )
        
        article = response.data[0]
        
        # Возвращаем цены
        return ArticlePricesResponse(
            article_id=article["id"],
            article_number=article["article_number"],
            price=article.get("price"),
            normal_price=article.get("normal_price"),
            ozon_card_price=article.get("ozon_card_price"),
            old_price=article.get("old_price"),
            average_price_7days=article.get("average_price_7days"),
            price_updated_at=article.get("price_updated_at")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении цен артикула {article_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сервера: {str(e)}"
        )


@router.get("/{article_id}/price-history", response_model=PriceHistoryResponse)
async def get_article_price_history(
    article_id: str,
    days: int = Query(default=7, ge=1, le=30, description="Количество дней для истории")
):
    """
    Получить историю изменения цен за период
    
    Возвращает историю изменения всех типов цен за указанный период.
    
    Args:
        article_id: UUID артикула
        days: Количество дней (от 1 до 30, по умолчанию 7)
        
    Returns:
        PriceHistoryResponse с историей цен
    """
    try:
        supabase = get_supabase_client()
        
        # Получаем артикул из БД
        response = supabase.table("ozon_scraper_articles") \
            .select("article_number") \
            .eq("id", article_id) \
            .execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Артикул не найден"
            )
        
        article_number = response.data[0]["article_number"]
        
        # Вызываем SQL функцию для получения истории
        history_response = supabase.rpc(
            "get_price_history",
            {
                "p_article_number": article_number,
                "p_days": days,
                "p_limit": 100
            }
        ).execute()
        
        history = history_response.data or []
        
        # Форматируем данные
        formatted_history = []
        for record in history:
            formatted_history.append({
                "price_date": record.get("price_date"),
                "price": record.get("price"),
                "normal_price": record.get("normal_price"),
                "ozon_card_price": record.get("ozon_card_price"),
                "old_price": record.get("old_price"),
                "product_available": record.get("product_available", True)
            })
        
        logger.info(f"История цен для {article_number}: {len(formatted_history)} записей за {days} дней")
        
        return PriceHistoryResponse(
            article_number=article_number,
            days=days,
            total_records=len(formatted_history),
            history=formatted_history
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении истории цен для {article_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сервера: {str(e)}"
        )


@router.get("/{article_id}/price-average", response_model=PriceAverageResponse)
async def get_article_price_average(
    article_id: str,
    days: int = Query(default=7, ge=1, le=30, description="Количество дней для расчета средней")
):
    """
    Получить среднюю цену за период
    
    Рассчитывает среднюю, минимальную и максимальную цену за указанный период.
    Также возвращает количество точек данных и диапазон дат.
    
    Args:
        article_id: UUID артикула
        days: Количество дней (от 1 до 30, по умолчанию 7)
        
    Returns:
        PriceAverageResponse со статистикой цен
    """
    try:
        supabase = get_supabase_client()
        
        # Получаем артикул из БД
        response = supabase.table("ozon_scraper_articles") \
            .select("article_number") \
            .eq("id", article_id) \
            .execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Артикул не найден"
            )
        
        article_number = response.data[0]["article_number"]
        
        # Вызываем SQL функцию для получения средней цены
        avg_response = supabase.rpc(
            "get_average_price_7days",
            {
                "p_article_number": article_number,
                "p_days": days
            }
        ).execute()
        
        if not avg_response.data or len(avg_response.data) == 0:
            # Нет данных для этого артикула
            logger.warning(f"Нет данных истории цен для {article_number}")
            return PriceAverageResponse(
                article_number=article_number,
                days=days,
                avg_price=None,
                data_points=0
            )
        
        stats = avg_response.data[0]
        
        logger.info(
            f"Средняя цена для {article_number} за {days} дней: "
            f"avg={stats.get('avg_price')}, min={stats.get('min_price')}, max={stats.get('max_price')}"
        )
        
        return PriceAverageResponse(
            article_number=article_number,
            days=days,
            avg_price=stats.get("avg_price"),
            avg_normal_price=stats.get("avg_normal_price"),
            avg_ozon_card_price=stats.get("avg_ozon_card_price"),
            min_price=stats.get("min_price"),
            max_price=stats.get("max_price"),
            data_points=stats.get("data_points", 0),
            first_date=stats.get("first_date"),
            last_date=stats.get("last_date")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении средней цены для {article_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сервера: {str(e)}"
        )


@router.post("/{article_id}/refresh-prices")
async def refresh_article_prices(article_id: str):
    """
    Обновить информацию о ценах товара
    
    Выполняет web scraping для получения актуальных цен и обновляет данные в БД.
    Также обновляет среднюю цену за 7 дней.
    
    Args:
        article_id: UUID артикула
        
    Returns:
        Обновленная информация о ценах
    """
    try:
        supabase = get_supabase_client()
        
        # Получаем артикул из БД
        response = supabase.table("ozon_scraper_articles") \
            .select("*") \
            .eq("id", article_id) \
            .execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Артикул не найден"
            )
        
        article = response.data[0]
        article_number = article["article_number"]
        
        # Получаем свежие данные через Parser Market API
        ozon_service = get_ozon_service()
        product_info = await ozon_service.get_product_info(
            article_number,
            use_cache=False  # Не используем кэш для обновления
        )
        
        if not product_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Не удалось получить данные о товаре"
            )
        
        # Обновляем цены в БД
        update_data = {
            "price": product_info.price,
            "normal_price": product_info.normal_price,
            "ozon_card_price": product_info.ozon_card_price,
            "old_price": product_info.old_price,
            "price_updated_at": datetime.now().isoformat(),
            "last_check": datetime.now().isoformat(),
            "available": product_info.available,
            "rating": product_info.rating,
            "reviews_count": product_info.reviews_count
        }
        
        supabase.table("ozon_scraper_articles") \
            .update(update_data) \
            .eq("id", article_id) \
            .execute()
        
        # Обновляем среднюю цену за 7 дней
        supabase.rpc(
            "update_article_average_price",
            {"p_article_number": article_number}
        ).execute()
        
        # Пересчитываем СПП метрики
        supabase.rpc(
            "update_article_spp_metrics",
            {"p_article_number": article_number}
        ).execute()
        
        # Получаем обновленные данные
        updated_response = supabase.table("ozon_scraper_articles") \
            .select("*") \
            .eq("id", article_id) \
            .execute()
        
        updated_article = updated_response.data[0]
        
        logger.info(f"Цены обновлены для артикула {article_number}")
        
        return ArticlePricesResponse(
            article_id=updated_article["id"],
            article_number=updated_article["article_number"],
            price=updated_article.get("price"),
            normal_price=updated_article.get("normal_price"),
            ozon_card_price=updated_article.get("ozon_card_price"),
            old_price=updated_article.get("old_price"),
            average_price_7days=updated_article.get("average_price_7days"),
            price_updated_at=updated_article.get("price_updated_at")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при обновлении цен для {article_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сервера: {str(e)}"
        )


@router.get("/{article_id}/spp")
async def get_article_spp_metrics(article_id: str):
    """
    Получить показатели СПП (скидки) для артикула
    
    Возвращает:
    - СПП1: Скидка от средней цены за 7 дней до обычной цены
    - СПП2: Скидка Ozon Card (от обычной до цены с картой)
    - СПП Общий: Общая скидка (от средней за 7 дней до цены с картой)
    
    Args:
        article_id: UUID артикула
        
    Returns:
        SPPMetrics с показателями скидки
    """
    try:
        from models.ozon_models import SPPMetrics
        
        supabase = get_supabase_client()
        
        # Получаем артикул из БД
        response = supabase.table("ozon_scraper_articles") \
            .select("spp1, spp2, spp_total") \
            .eq("id", article_id) \
            .execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Артикул не найден"
            )
        
        data = response.data[0]
        
        return SPPMetrics(
            spp1=data.get("spp1"),
            spp2=data.get("spp2"),
            spp_total=data.get("spp_total")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении СПП для {article_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сервера: {str(e)}"
        )


@router.post("/update-all-averages")
async def update_all_average_prices():
    """
    Обновить средние цены для всех активных артикулов
    
    Полезно для массового обновления средних цен после накопления истории.
    Требует прав администратора.
    
    Returns:
        Количество обновленных артикулов
    """
    try:
        supabase = get_supabase_client()
        
        # Вызываем SQL функцию для обновления всех средних цен
        result = supabase.rpc("update_all_average_prices", {}).execute()
        
        updated_count = result.data if result.data else 0
        
        logger.info(f"Обновлены средние цены для {updated_count} артикулов")
        
        return {
            "success": True,
            "updated_count": updated_count,
            "message": f"Средние цены обновлены для {updated_count} артикулов"
        }
        
    except Exception as e:
        logger.error(f"Ошибка при массовом обновлении средних цен: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сервера: {str(e)}"
        )


@router.post("/update-all-spp")
async def update_all_spp_metrics():
    """
    Обновить показатели СПП для всех активных артикулов
    
    Пересчитывает СПП1, СПП2 и СПП Общий для всех активных товаров.
    Требует прав администратора.
    
    Returns:
        Количество обновленных артикулов
    """
    try:
        supabase = get_supabase_client()
        
        # Вызываем SQL функцию для обновления всех СПП
        result = supabase.rpc("update_all_spp_metrics", {}).execute()
        
        updated_count = result.data if result.data else 0
        
        logger.info(f"Обновлены показатели СПП для {updated_count} артикулов")
        
        return {
            "success": True,
            "updated_count": updated_count,
            "message": f"Показатели СПП обновлены для {updated_count} артикулов"
        }
        
    except Exception as e:
        logger.error(f"Ошибка при массовом обновлении СПП: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сервера: {str(e)}"
        )

