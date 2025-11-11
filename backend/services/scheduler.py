"""
Scheduler Service

Планировщик для автоматических задач (Cron jobs).

Features:
- Обновление снэпшотов сравнений (каждые 24 часа)
- Сбор истории цен (каждые 24 часа)
- Логирование всех операций

Author: AI Agent
Created: 2025-10-31
"""

from typing import List
from datetime import datetime
import asyncio

from loguru import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from database import get_supabase_client
from services.comparison_service import ComparisonService
from services.article_service import ArticleService


# ==================== Scheduler Instance ====================

scheduler = AsyncIOScheduler()


# ==================== Cron Jobs ====================

async def update_comparison_snapshots():
    """
    Обновить снэпшоты для всех активных групп сравнения

    Запускается каждые 24 часа через scheduler.

    Для каждой группы:
    1. Получить артикулы группы
    2. Scrape данные для каждого артикула
    3. Рассчитать метрики сравнения
    4. Сохранить снэпшот
    """
    logger.info("=" * 60)
    logger.info("🔄 Starting comparison snapshots update...")
    logger.info("=" * 60)

    start_time = datetime.now()
    supabase = get_supabase_client()
    comparison_service = ComparisonService()
    article_service = ArticleService()

    try:
        # Получить все группы сравнения
        result = supabase.table("ozon_scraper_article_groups") \
            .select("id, user_id, name, group_type") \
            .eq("group_type", "comparison") \
            .execute()

        if not result.data:
            logger.info("No comparison groups found")
            return

        total = len(result.data)
        success = 0
        errors = 0

        logger.info(f"Found {total} comparison groups to update")

        for group in result.data:
            group_id = group['id']
            user_id = group['user_id']
            group_name = group.get('name', 'Unnamed')

            try:
                logger.info(f"Processing group {group_id} ({group_name})")

                # Получаем членов группы
                members_result = supabase.table("ozon_scraper_article_group_members") \
                    .select("article_id, role") \
                    .eq("group_id", group_id) \
                    .execute()

                if not members_result.data or len(members_result.data) < 2:
                    logger.warning(f"Group {group_id} has less than 2 articles - skipping")
                    continue

                # Обновляем данные каждого артикула
                logger.info(f"Updating {len(members_result.data)} articles in group")

                for member in members_result.data:
                    article_id = member['article_id']
                    try:
                        # Обновляем данные артикула
                        await article_service.check_article(article_id, user_id)
                        logger.debug(f"  ✅ Article {article_id} updated")
                    except Exception as e:
                        logger.error(f"  ❌ Failed to update article {article_id}: {e}")

                # Небольшая пауза между scraping
                await asyncio.sleep(2)

                # Получаем обновленное сравнение (это автоматически сохранит снэпшот)
                comparison = await comparison_service.get_comparison(
                    group_id=group_id,
                    user_id=user_id,
                    refresh=False  # Данные уже обновлены выше
                )

                if comparison.metrics:
                    success += 1
                    logger.success(
                        f"✅ Snapshot saved for group {group_id} "
                        f"(Index: {comparison.metrics.competitiveness_index}, "
                        f"Grade: {comparison.metrics.grade.value})"
                    )
                else:
                    logger.warning(f"⚠️ No metrics for group {group_id} - snapshot not saved")

            except Exception as e:
                errors += 1
                logger.error(f"❌ Error processing group {group_id}: {e}")
                logger.exception(e)

        # Итоговая статистика
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info("=" * 60)
        logger.success(
            f"✅ Comparison snapshots update completed!\n"
            f"   Total groups: {total}\n"
            f"   Successful: {success}\n"
            f"   Errors: {errors}\n"
            f"   Time elapsed: {elapsed:.1f}s"
        )
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ Critical error in update_comparison_snapshots: {e}")
        logger.exception(e)


async def update_price_history():
    """
    Обновить историю цен для всех артикулов

    Запускается каждые 24 часа через scheduler.

    Для каждого артикула:
    1. Scrape текущие данные
    2. Сохранить в price_history
    """
    logger.info("=" * 60)
    logger.info("📊 Starting price history update...")
    logger.info("=" * 60)

    start_time = datetime.now()
    supabase = get_supabase_client()
    article_service = ArticleService()

    try:
        # Получить все артикулы
        result = supabase.table("ozon_scraper_articles") \
            .select("id, user_id, article_number") \
            .execute()

        if not result.data:
            logger.info("No articles found")
            return

        total = len(result.data)
        success = 0
        errors = 0

        logger.info(f"Found {total} articles to update")

        for article in result.data:
            article_id = article['id']
            user_id = article['user_id']
            article_number = article.get('article_number', 'Unknown')

            try:
                # Обновляем данные артикула
                await article_service.check_article(article_id, user_id)
                success += 1
                logger.debug(f"✅ Article {article_number} updated")

                # Небольшая пауза между запросами
                await asyncio.sleep(1)

            except Exception as e:
                errors += 1
                logger.error(f"❌ Failed to update article {article_number}: {e}")

        # Итоговая статистика
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info("=" * 60)
        logger.success(
            f"✅ Price history update completed!\n"
            f"   Total articles: {total}\n"
            f"   Successful: {success}\n"
            f"   Errors: {errors}\n"
            f"   Time elapsed: {elapsed:.1f}s"
        )
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ Critical error in update_price_history: {e}")
        logger.exception(e)


# ==================== Scheduler Management ====================

def start_scheduler():
    """
    Запустить планировщик задач

    Регистрирует все cron jobs и запускает scheduler
    """
    logger.info("🚀 Starting scheduler...")

    # Задача 1: Обновление снэпшотов сравнений (каждый день в 03:00)
    scheduler.add_job(
        update_comparison_snapshots,
        trigger=CronTrigger(hour=3, minute=0),
        id='update_comparison_snapshots',
        name='Update Comparison Snapshots',
        replace_existing=True
    )
    logger.info("  ✅ Registered job: update_comparison_snapshots (daily at 03:00)")

    # Задача 2: Обновление истории цен (каждый день в 04:00)
    scheduler.add_job(
        update_price_history,
        trigger=CronTrigger(hour=4, minute=0),
        id='update_price_history',
        name='Update Price History',
        replace_existing=True
    )
    logger.info("  ✅ Registered job: update_price_history (daily at 04:00)")

    # Запускаем scheduler
    scheduler.start()
    logger.success("✅ Scheduler started successfully!")

    # Показываем список зарегистрированных задач
    logger.info("Registered jobs:")
    for job in scheduler.get_jobs():
        logger.info(f"  - {job.name} (ID: {job.id}, Next run: {job.next_run_time})")


def stop_scheduler():
    """Остановить планировщик задач"""
    logger.info("🛑 Stopping scheduler...")
    scheduler.shutdown()
    logger.success("✅ Scheduler stopped")


def run_job_manually(job_id: str):
    """
    Запустить задачу вручную

    Args:
        job_id: ID задачи ('update_comparison_snapshots' или 'update_price_history')
    """
    job = scheduler.get_job(job_id)
    if job:
        logger.info(f"🔧 Running job manually: {job.name}")
        job.func()
    else:
        logger.error(f"❌ Job not found: {job_id}")


# ==================== Manual Testing ====================

async def test_comparison_snapshots():
    """Тестовый запуск обновления снэпшотов"""
    logger.info("🧪 Testing comparison snapshots update...")
    await update_comparison_snapshots()


async def test_price_history():
    """Тестовый запуск обновления истории цен"""
    logger.info("🧪 Testing price history update...")
    await update_price_history()


if __name__ == "__main__":
    # Для ручного тестирования
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "test-snapshots":
            asyncio.run(test_comparison_snapshots())
        elif sys.argv[1] == "test-price":
            asyncio.run(test_price_history())
        else:
            print("Usage:")
            print("  python scheduler.py test-snapshots  # Test comparison snapshots")
            print("  python scheduler.py test-price      # Test price history")
    else:
        # Запустить scheduler в standalone режиме
        start_scheduler()

        try:
            # Держим процесс запущенным
            asyncio.get_event_loop().run_forever()
        except (KeyboardInterrupt, SystemExit):
            stop_scheduler()
