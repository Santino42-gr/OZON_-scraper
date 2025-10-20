"""
Cleanup Old Data - Cron Job

Автоматическая очистка старых данных из БД для оптимизации хранилища.

Что удаляется:
- История цен старше 30 дней (ozon_scraper_price_history)
- Логи старше 90 дней (ozon_scraper_logs)
- История запросов старше 30 дней (ozon_scraper_request_history)

Запуск: Еженедельно (воскресенье 04:00)

Usage:
    python -m cron_jobs.cleanup_old_data
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from database import get_supabase_client


class DataCleanupJob:
    """Очистка старых данных из БД"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
        self.stats = {
            "start_time": None,
            "end_time": None,
            "price_history_deleted": 0,
            "logs_deleted": 0,
            "request_history_deleted": 0,
            "total_deleted": 0
        }
    
    def cleanup_price_history(self, days: int = 30) -> int:
        """
        Удалить историю цен старше N дней
        
        Args:
            days: Количество дней
            
        Returns:
            Количество удаленных записей
        """
        try:
            # Вызываем SQL функцию cleanup_old_price_history()
            result = self.supabase.rpc("cleanup_old_price_history").execute()
            deleted_count = result.data if result.data else 0
            
            logger.info(f"Deleted {deleted_count} old price history records (>{days} days)")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup price history: {e}")
            return 0
    
    def cleanup_logs(self, days: int = 90) -> int:
        """
        Удалить логи старше N дней
        
        Args:
            days: Количество дней
            
        Returns:
            Количество удаленных записей
        """
        try:
            # SQL: DELETE FROM ozon_scraper_logs WHERE timestamp < NOW() - INTERVAL '90 days'
            result = self.supabase.table("ozon_scraper_logs") \
                .delete() \
                .lt("timestamp", f"now() - interval '{days} days'") \
                .execute()
            
            deleted_count = len(result.data) if result.data else 0
            logger.info(f"Deleted {deleted_count} old log records (>{days} days)")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup logs: {e}")
            return 0
    
    def cleanup_request_history(self, days: int = 30) -> int:
        """
        Удалить историю запросов старше N дней
        
        Args:
            days: Количество дней
            
        Returns:
            Количество удаленных записей
        """
        try:
            result = self.supabase.table("ozon_scraper_request_history") \
                .delete() \
                .lt("requested_at", f"now() - interval '{days} days'") \
                .execute()
            
            deleted_count = len(result.data) if result.data else 0
            logger.info(f"Deleted {deleted_count} old request history records (>{days} days)")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup request history: {e}")
            return 0
    
    def log_execution(self):
        """Логировать результат выполнения"""
        try:
            log_entry = {
                "level": "INFO",
                "event_type": "cron_data_cleanup",
                "message": f"Data cleanup completed: {self.stats['total_deleted']} records deleted",
                "metadata": self.stats
            }
            
            self.supabase.table("ozon_scraper_logs") \
                .insert(log_entry) \
                .execute()
            
            logger.info("Cleanup execution logged to database")
            
        except Exception as e:
            logger.error(f"Failed to log cleanup execution: {e}")
    
    async def run(self):
        """Главный метод выполнения"""
        self.stats["start_time"] = datetime.now()
        
        logger.info("="*60)
        logger.info("🧹 Starting Data Cleanup Cron Job")
        logger.info("="*60)
        
        try:
            # Очистка истории цен (> 30 дней)
            self.stats["price_history_deleted"] = self.cleanup_price_history(days=30)
            
            # Очистка логов (> 90 дней)
            self.stats["logs_deleted"] = self.cleanup_logs(days=90)
            
            # Очистка истории запросов (> 30 дней)
            self.stats["request_history_deleted"] = self.cleanup_request_history(days=30)
            
            # Подсчет общего количества удаленных записей
            self.stats["total_deleted"] = (
                self.stats["price_history_deleted"] +
                self.stats["logs_deleted"] +
                self.stats["request_history_deleted"]
            )
            
            self.stats["end_time"] = datetime.now()
            duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
            
            logger.info("="*60)
            logger.info("✅ Data Cleanup Completed")
            logger.info("="*60)
            logger.info(f"Price history deleted: {self.stats['price_history_deleted']}")
            logger.info(f"Logs deleted: {self.stats['logs_deleted']}")
            logger.info(f"Request history deleted: {self.stats['request_history_deleted']}")
            logger.info(f"Total deleted: {self.stats['total_deleted']}")
            logger.info(f"Duration: {duration:.2f}s")
            
            # Логируем результат
            self.log_execution()
            
        except Exception as e:
            logger.critical(f"Data cleanup job failed: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """Entry point"""
    job = DataCleanupJob()
    await job.run()


if __name__ == "__main__":
    asyncio.run(main())

