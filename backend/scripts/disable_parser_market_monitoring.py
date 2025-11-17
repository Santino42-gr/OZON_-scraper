"""
Скрипт для отключения автоматических заданий мониторинга Parser Market

Проблема: Ежедневно с 06:00 до 07:00 приходит ~80 писем с мониторингом через Parser Market API.
Задания создаются через API, но не видны в личном кабинете клиента.

Этот скрипт:
1. Получает все задания через Parser Market API
2. Фильтрует задания с расписанием 06:00-07:00
3. Пытается отключить/удалить эти задания через API
4. Выводит отчет о результатах

Usage:
    python -m scripts.disable_parser_market_monitoring
    python -m scripts.disable_parser_market_monitoring --dry-run  # Только просмотр без удаления
    python -m scripts.disable_parser_market_monitoring --start-hour 6 --end-hour 7  # Настройка времени
"""

import asyncio
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Добавляем backend в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from services.parser_market_client import ParserMarketClient
from config import settings


async def find_monitoring_tasks(
    client: ParserMarketClient,
    start_hour: int = 6,
    end_hour: int = 7
) -> List[Dict[str, Any]]:
    """
    Найти задания мониторинга с указанным расписанием

    Args:
        client: Parser Market клиент
        start_hour: Начальный час (0-23)
        end_hour: Конечный час (0-23)

    Returns:
        Список заданий мониторинга
    """
    logger.info("=" * 60)
    logger.info("🔍 Поиск заданий мониторинга...")
    logger.info("=" * 60)

    # Получаем все задания
    logger.info("Получение всех заданий через API...")
    all_tasks = await client.get_all_tasks(limit=1000)
    logger.info(f"Найдено заданий всего: {len(all_tasks)}")

    # Фильтруем по времени
    logger.info(f"Фильтрация заданий с расписанием {start_hour:02d}:00-{end_hour:02d}:00...")
    monitoring_tasks = client.filter_tasks_by_time(
        all_tasks,
        start_hour=start_hour,
        end_hour=end_hour
    )

    logger.info(f"Найдено заданий мониторинга: {len(monitoring_tasks)}")
    return monitoring_tasks


async def disable_monitoring_tasks(
    client: ParserMarketClient,
    tasks: List[Dict[str, Any]],
    dry_run: bool = False
) -> Dict[str, int]:
    """
    Отключить задания мониторинга

    Args:
        client: Parser Market клиент
        tasks: Список заданий для отключения
        dry_run: Если True - только просмотр без удаления

    Returns:
        Словарь со статистикой: {"success": N, "failed": M, "skipped": K}
    """
    stats = {"success": 0, "failed": 0, "skipped": 0}

    if not tasks:
        logger.info("Нет заданий для отключения")
        return stats

    logger.info("=" * 60)
    if dry_run:
        logger.info("🔍 DRY RUN - задания не будут удалены")
    else:
        logger.info("🗑️  Отключение заданий мониторинга...")
    logger.info("=" * 60)

    for i, task in enumerate(tasks, 1):
        task_dict = client._parse_task_dict(task)
        task_id = client.extract_task_id(task)
        userlabel = client.extract_userlabel(task)

        logger.info(f"\n[{i}/{len(tasks)}] Обработка задания:")
        logger.info(f"  ID: {task_id}")
        logger.info(f"  Userlabel: {userlabel}")
        logger.info(f"  Данные: {task_dict}")

        if dry_run:
            logger.info("  ⚠️  DRY RUN - задание не будет удалено")
            stats["skipped"] += 1
            continue

        # Пытаемся удалить задание
        try:
            success = await client.delete_task(
                order_id=task_id,
                userlabel=userlabel
            )

            if success:
                logger.success(f"  ✅ Задание успешно отключено")
                stats["success"] += 1
            else:
                logger.warning(f"  ⚠️  Не удалось отключить через API")
                stats["failed"] += 1

        except Exception as e:
            logger.error(f"  ❌ Ошибка при отключении: {e}")
            stats["failed"] += 1

        # Небольшая задержка между запросами
        if i < len(tasks):
            await asyncio.sleep(0.5)

    return stats


async def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(
        description="Отключение автоматических заданий мониторинга Parser Market"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Только просмотр заданий без удаления"
    )
    parser.add_argument(
        "--start-hour",
        type=int,
        default=6,
        help="Начальный час для фильтрации (0-23, по умолчанию 6)"
    )
    parser.add_argument(
        "--end-hour",
        type=int,
        default=7,
        help="Конечный час для фильтрации (0-23, по умолчанию 7)"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="API ключ Parser Market (если не указан, берется из настроек)"
    )

    args = parser.parse_args()

    # Проверка аргументов
    if not (0 <= args.start_hour < 24 and 0 <= args.end_hour < 24):
        logger.error("Часы должны быть в диапазоне 0-23")
        return 1

    # Инициализация клиента
    api_key = args.api_key or settings.PARSER_MARKET_API_KEY
    if not api_key:
        logger.error("API ключ Parser Market не найден. Укажите через --api-key или настройте PARSER_MARKET_API_KEY")
        return 1

    client = ParserMarketClient(
        api_key=api_key,
        region=settings.PARSER_MARKET_REGION
    )

    try:
        # Поиск заданий мониторинга
        monitoring_tasks = await find_monitoring_tasks(
            client,
            start_hour=args.start_hour,
            end_hour=args.end_hour
        )

        if not monitoring_tasks:
            logger.info("✅ Заданий мониторинга с указанным расписанием не найдено")
            return 0

        # Отключение заданий
        stats = await disable_monitoring_tasks(
            client,
            monitoring_tasks,
            dry_run=args.dry_run
        )

        # Итоговый отчет
        logger.info("=" * 60)
        logger.info("📊 ИТОГОВЫЙ ОТЧЕТ")
        logger.info("=" * 60)
        logger.info(f"Всего найдено заданий: {len(monitoring_tasks)}")
        logger.info(f"Успешно отключено: {stats['success']}")
        logger.info(f"Не удалось отключить: {stats['failed']}")
        logger.info(f"Пропущено (dry-run): {stats['skipped']}")

        if args.dry_run:
            logger.info("\n⚠️  Это был DRY RUN. Для реального отключения запустите без --dry-run")
        elif stats["failed"] > 0:
            logger.warning(
                "\n⚠️  Некоторые задания не удалось отключить через API.\n"
                "Рекомендуется обратиться в поддержку Parser Market для отключения заданий мониторинга."
            )

        return 0 if stats["failed"] == 0 else 1

    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        return 1

    finally:
        await client.close()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

