"""
Report Service

Бизнес-логика для генерации отчетов по артикулам и пользователям.

Features:
- Генерация отчетов по артикулам и пользователям
- Экспорт в CSV и Excel (XLSX)
- Агрегация данных из нескольких источников
- Логирование всех операций

Author: AI Agent
Created: 2025-10-20
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
import csv
import io

from loguru import logger
from database import get_supabase_client
from models.report import ReportRequest, ReportResponse, ReportData


# ==================== Exceptions ====================

class ReportServiceError(Exception):
    """Базовое исключение для ReportService"""
    pass


# ==================== Report Service ====================

class ReportService:
    """
    Сервис для генерации отчетов
    
    Создает отчеты по артикулам, пользователям, экспортирует
    данные в различные форматы (CSV, XLSX).
    """
    
    def __init__(self):
        """Инициализация сервиса"""
        self.supabase = get_supabase_client()
        logger.info("✅ ReportService initialized")
    
    # ==================== Логирование ====================
    
    async def _log_operation(
        self,
        level: str,
        event_type: str,
        message: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Логирование операции в БД"""
        try:
            log_data = {
                "level": level.upper(),
                "event_type": event_type,
                "message": message,
                "user_id": user_id,
                "metadata": metadata or {},
                "timestamp": datetime.now().isoformat()
            }
            
            self.supabase.table("ozon_scraper_logs").insert(log_data).execute()
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to log operation to DB: {e}")
    
    # ==================== Report Generation ====================
    
    async def generate_article_report(
        self,
        article_id: str,
        include_history: bool = True,
        days: int = 30
    ) -> ReportData:
        """
        Сгенерировать отчет по артикулу
        
        Args:
            article_id: UUID артикула
            include_history: Включить историю запросов (default: True)
            days: Глубина истории в днях (default: 30)
            
        Returns:
            ReportData с данными отчета
            
        Raises:
            ReportServiceError: При ошибках
        """
        try:
            # Получаем данные артикула
            article = self.supabase.table("ozon_scraper_articles").select(
                "*"
            ).eq("id", article_id).execute()
            
            if not article.data:
                raise ReportServiceError(f"Article {article_id} not found")
            
            article_data = article.data[0]
            article_number = article_data["article_number"]
            
            logger.info(f"📊 Generating report for article: {article_number}")
            
            # Данные отчета
            report_data = {
                "article_id": article_id,
                "article_number": article_number,
                "status": article_data["status"],
                "created_at": article_data["created_at"],
                "updated_at": article_data["updated_at"],
                "is_problematic": article_data["is_problematic"],
                "last_check_data": article_data.get("last_check_data", {})
            }
            
            # Добавляем историю запросов если нужно
            if include_history:
                start_date = (datetime.now() - timedelta(days=days)).isoformat()
                history = self.supabase.table("ozon_scraper_request_history").select(
                    "*"
                ).eq("article_id", article_id).gte("requested_at", start_date).order(
                    "requested_at", desc=True
                ).execute()
                
                report_data["request_history"] = history.data
                report_data["total_requests"] = len(history.data)
                report_data["successful_requests"] = len([
                    r for r in history.data if r.get("success", False)
                ])
            
            # Получаем историю цен если есть
            try:
                price_history = self.supabase.rpc(
                    "get_price_history",
                    {
                        "p_article_number": article_number,
                        "p_days": days,
                        "p_limit": 100
                    }
                ).execute()
                
                if price_history.data:
                    report_data["price_history"] = price_history.data
                    
                    # Получаем среднюю цену
                    avg_price = self.supabase.rpc(
                        "get_average_price_7days",
                        {
                            "p_article_number": article_number,
                            "p_days": 7
                        }
                    ).execute()
                    
                    if avg_price.data:
                        report_data["average_price_7d"] = avg_price.data[0]
                        
            except Exception as e:
                logger.warning(f"⚠️  Failed to fetch price history: {e}")
                report_data["price_history"] = []
            
            # Логируем генерацию отчета
            await self._log_operation(
                level="INFO",
                event_type="report_generated",
                message=f"Article report generated for {article_number}",
                user_id=article_data["user_id"],
                metadata={
                    "article_id": article_id,
                    "article_number": article_number,
                    "report_type": "article"
                }
            )
            
            logger.success(f"✅ Report generated for article: {article_number}")
            
            return ReportData(**report_data)
            
        except Exception as e:
            logger.error(f"❌ Error generating article report: {e}")
            await self._log_operation(
                level="ERROR",
                event_type="report_generation_failed",
                message=f"Failed to generate article report: {str(e)}",
                metadata={"error": str(e), "article_id": article_id}
            )
            raise ReportServiceError(f"Failed to generate report: {str(e)}")
    
    async def generate_user_report(
        self,
        user_id: str,
        include_articles: bool = True,
        days: int = 30
    ) -> ReportData:
        """
        Сгенерировать отчет по пользователю
        
        Args:
            user_id: UUID пользователя
            include_articles: Включить список артикулов (default: True)
            days: Глубина истории в днях (default: 30)
            
        Returns:
            ReportData с данными отчета
        """
        try:
            # Получаем данные пользователя
            user = self.supabase.table("ozon_scraper_users").select("*").eq(
                "id", user_id
            ).execute()
            
            if not user.data:
                raise ReportServiceError(f"User {user_id} not found")
            
            user_data = user.data[0]
            
            logger.info(f"📊 Generating report for user: {user_data['telegram_id']}")
            
            # Данные отчета
            report_data = {
                "user_id": user_id,
                "telegram_id": user_data["telegram_id"],
                "telegram_username": user_data.get("telegram_username"),
                "is_blocked": user_data["is_blocked"],
                "created_at": user_data["created_at"],
                "last_active_at": user_data["last_active_at"]
            }
            
            # Получаем артикулы
            articles = self.supabase.table("ozon_scraper_articles").select("*").eq(
                "user_id", user_id
            ).execute()
            
            report_data["total_articles"] = len(articles.data)
            report_data["active_articles"] = len([
                a for a in articles.data if a["status"] == "active"
            ])
            report_data["problematic_articles"] = len([
                a for a in articles.data if a.get("is_problematic", False)
            ])
            
            if include_articles:
                report_data["articles"] = articles.data
            
            # Получаем историю запросов
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            requests = self.supabase.table("ozon_scraper_request_history").select(
                "*"
            ).eq("user_id", user_id).gte("requested_at", start_date).execute()
            
            report_data["total_requests"] = len(requests.data)
            report_data["successful_requests"] = len([
                r for r in requests.data if r.get("success", False)
            ])
            
            # Логируем генерацию отчета
            await self._log_operation(
                level="INFO",
                event_type="report_generated",
                message=f"User report generated for {user_data['telegram_id']}",
                user_id=user_id,
                metadata={
                    "telegram_id": user_data["telegram_id"],
                    "report_type": "user"
                }
            )
            
            logger.success(f"✅ Report generated for user: {user_data['telegram_id']}")
            
            return ReportData(**report_data)
            
        except Exception as e:
            logger.error(f"❌ Error generating user report: {e}")
            await self._log_operation(
                level="ERROR",
                event_type="report_generation_failed",
                message=f"Failed to generate user report: {str(e)}",
                metadata={"error": str(e), "user_id": user_id}
            )
            raise ReportServiceError(f"Failed to generate report: {str(e)}")
    
    async def generate_multiple_articles_report(
        self,
        article_ids: List[str],
        include_history: bool = False
    ) -> List[ReportData]:
        """
        Сгенерировать отчет по нескольким артикулам
        
        Args:
            article_ids: Список UUID артикулов
            include_history: Включить историю запросов (default: False)
            
        Returns:
            Список ReportData
        """
        try:
            logger.info(f"📊 Generating report for {len(article_ids)} articles")
            
            reports = []
            
            for article_id in article_ids:
                try:
                    report = await self.generate_article_report(
                        article_id,
                        include_history=include_history,
                        days=7  # Меньше данных для batch reports
                    )
                    reports.append(report)
                except Exception as e:
                    logger.warning(f"⚠️  Failed to generate report for {article_id}: {e}")
                    continue
            
            logger.success(f"✅ Generated {len(reports)} reports out of {len(article_ids)}")
            
            return reports
            
        except Exception as e:
            logger.error(f"❌ Error generating multiple reports: {e}")
            raise ReportServiceError(f"Failed to generate reports: {str(e)}")
    
    # ==================== Export Functions ====================
    
    def export_to_csv(self, data: List[Dict[str, Any]]) -> str:
        """
        Экспортировать данные в CSV
        
        Args:
            data: Список словарей с данными
            
        Returns:
            CSV строка
            
        Raises:
            ReportServiceError: При ошибках
        """
        try:
            if not data:
                raise ReportServiceError("No data to export")
            
            logger.info(f"📁 Exporting {len(data)} rows to CSV")
            
            # Создаем CSV в памяти
            output = io.StringIO()
            
            # Получаем все ключи из первой записи
            fieldnames = list(data[0].keys())
            
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
            
            csv_content = output.getvalue()
            output.close()
            
            logger.success(f"✅ CSV exported: {len(csv_content)} bytes")
            
            return csv_content
            
        except Exception as e:
            logger.error(f"❌ Error exporting to CSV: {e}")
            raise ReportServiceError(f"Failed to export CSV: {str(e)}")
    
    def export_to_xlsx(self, data: List[Dict[str, Any]], sheet_name: str = "Report") -> bytes:
        """
        Экспортировать данные в Excel (XLSX)
        
        Args:
            data: Список словарей с данными
            sheet_name: Название листа (default: "Report")
            
        Returns:
            XLSX файл в байтах
            
        Raises:
            ReportServiceError: При ошибках
        """
        try:
            if not data:
                raise ReportServiceError("No data to export")
            
            logger.info(f"📊 Exporting {len(data)} rows to XLSX")
            
            # Требуется openpyxl или xlsxwriter
            try:
                import openpyxl
                from openpyxl import Workbook
                
                # Создаем workbook
                wb = Workbook()
                ws = wb.active
                ws.title = sheet_name
                
                # Заголовки
                headers = list(data[0].keys())
                ws.append(headers)
                
                # Данные
                for row in data:
                    ws.append([row.get(key) for key in headers])
                
                # Сохраняем в байты
                output = io.BytesIO()
                wb.save(output)
                xlsx_content = output.getvalue()
                output.close()
                
                logger.success(f"✅ XLSX exported: {len(xlsx_content)} bytes")
                
                return xlsx_content
                
            except ImportError:
                logger.warning("⚠️  openpyxl not installed, falling back to CSV")
                # Fallback to CSV если нет openpyxl
                csv_content = self.export_to_csv(data)
                return csv_content.encode('utf-8')
                
        except Exception as e:
            logger.error(f"❌ Error exporting to XLSX: {e}")
            raise ReportServiceError(f"Failed to export XLSX: {str(e)}")


# ==================== Singleton ====================

_report_service_instance: Optional[ReportService] = None


def get_report_service() -> ReportService:
    """
    Получить singleton экземпляр ReportService
    
    Returns:
        ReportService instance
    """
    global _report_service_instance
    if _report_service_instance is None:
        _report_service_instance = ReportService()
    return _report_service_instance

