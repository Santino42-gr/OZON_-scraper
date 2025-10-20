"""
Reports Router
API endpoints для генерации отчетов
"""

from fastapi import APIRouter, HTTPException, status
from typing import List
from datetime import datetime

from models.report import (
    ReportRequest,
    ReportResponse,
    ReportData,
    ReportSummary
)
from database import get_supabase_client
from loguru import logger

router = APIRouter()


@router.post("/", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def generate_report(report_request: ReportRequest, user_id: str):
    """
    Сгенерировать отчет по артикулам
    
    - **article_ids**: Список UUID артикулов
    - **report_type**: Тип отчета (summary/detailed/comparison)
    - **include_history**: Включить историю изменений
    - **user_id**: UUID пользователя (query parameter)
    """
    try:
        supabase = get_supabase_client()
        
        # Получаем данные артикулов
        articles_data = []
        for article_id in report_request.article_ids:
            result = supabase.table("articles").select("*").eq("id", article_id).execute()
            if result.data:
                articles_data.append(result.data[0])
        
        if not articles_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Артикулы не найдены"
            )
        
        # Формируем данные отчета
        report_data = ReportData(
            articles=articles_data,
            summary={
                "total_articles": len(articles_data),
                "average_price": sum(a.get("price", 0) or 0 for a in articles_data) / len(articles_data) if articles_data else 0,
                "available_count": sum(1 for a in articles_data if a.get("available")),
                "total_value": sum(a.get("price", 0) or 0 for a in articles_data)
            },
            statistics={
                "min_price": min((a.get("price", 0) or 0 for a in articles_data), default=0),
                "max_price": max((a.get("price", 0) or 0 for a in articles_data), default=0),
                "avg_rating": sum(a.get("rating", 0) or 0 for a in articles_data) / len(articles_data) if articles_data else 0
            },
            generated_at=datetime.now()
        )
        
        # Сохраняем отчет в БД
        report_db_data = {
            "user_id": user_id,
            "report_type": report_request.report_type,
            "report_data": report_data.model_dump(),
            "created_at": datetime.now().isoformat()
        }
        
        result = supabase.table("reports").insert(report_db_data).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка при сохранении отчета"
            )
        
        logger.info(f"Отчет создан для пользователя {user_id}")
        
        return ReportResponse(
            id=result.data[0]["id"],
            user_id=user_id,
            report_type=report_request.report_type,
            report_data=report_data,
            created_at=result.data[0]["created_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при генерации отчета: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сервера: {str(e)}"
        )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(report_id: str):
    """
    Получить отчет по ID
    
    - **report_id**: UUID отчета
    """
    try:
        supabase = get_supabase_client()
        result = supabase.table("reports").select("*").eq("id", report_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Отчет не найден"
            )
        
        report = result.data[0]
        
        return ReportResponse(
            id=report["id"],
            user_id=report["user_id"],
            report_type=report["report_type"],
            report_data=ReportData(**report["report_data"]),
            created_at=report["created_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении отчета: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сервера: {str(e)}"
        )


@router.get("/", response_model=List[ReportSummary])
async def list_reports(user_id: str, limit: int = 50, offset: int = 0):
    """
    Получить список отчетов пользователя
    
    - **user_id**: UUID пользователя
    - **limit**: Количество записей (max 100)
    - **offset**: Смещение для пагинации
    """
    try:
        supabase = get_supabase_client()
        
        result = supabase.table("reports").select("id, report_type, created_at, report_data").eq(
            "user_id", user_id
        ).order("created_at", desc=True).range(offset, offset + limit - 1).execute()
        
        if not result.data:
            return []
        
        # Формируем summary
        summaries = []
        for report in result.data:
            summaries.append(ReportSummary(
                id=report["id"],
                report_type=report["report_type"],
                articles_count=len(report["report_data"].get("articles", [])),
                created_at=report["created_at"]
            ))
        
        return summaries
        
    except Exception as e:
        logger.error(f"Ошибка при получении списка отчетов: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сервера: {str(e)}"
        )


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(report_id: str):
    """
    Удалить отчет
    
    - **report_id**: UUID отчета
    """
    try:
        supabase = get_supabase_client()
        
        # Проверяем существование
        existing = supabase.table("reports").select("id").eq("id", report_id).execute()
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Отчет не найден"
            )
        
        # Удаляем
        supabase.table("reports").delete().eq("id", report_id).execute()
        
        logger.info(f"Отчет {report_id} удален")
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при удалении отчета: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сервера: {str(e)}"
        )

