"""
Comparison Service

Бизнес-логика для сравнения артикулов OZON.

Features:
- Создание групп сравнения
- Расчет метрик конкурентоспособности
- Сохранение и получение истории снэпшотов
- Генерация рекомендаций
- Вычисление индекса конкурентоспособности

Author: AI Agent
Created: 2025-10-30
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from uuid import UUID
import json

from loguru import logger
from database import get_supabase_client
from models.comparison import (
    ArticleRole,
    GroupType,
    CompetitivenessGrade,
    ArticleGroupCreate,
    ArticleGroupResponse,
    ArticleGroupMemberCreate,
    ArticleComparisonData,
    ComparisonResponse,
    ComparisonMetrics,
    PriceDifference,
    RatingDifference,
    ReviewsDifference,
    ComparisonSnapshotResponse,
    ComparisonHistoryResponse,
    QuickComparisonCreate,
    UserComparisonStats
)
from models.article import ArticleCreate
from services.article_service import ArticleService


# ==================== Exceptions ====================

class ComparisonServiceError(Exception):
    """Базовое исключение для ComparisonService"""
    pass


class GroupNotFoundError(ComparisonServiceError):
    """Группа не найдена"""
    pass


class InvalidComparisonError(ComparisonServiceError):
    """Некорректное сравнение (например, нет товара own или competitor)"""
    pass


# ==================== Comparison Service ====================

class ComparisonService:
    """
    Сервис для сравнения артикулов OZON

    Управляет группами сравнения, рассчитывает метрики,
    генерирует рекомендации и сохраняет историю.
    """

    # Константы для расчета индекса конкурентоспособности
    WEIGHTS = {
        'price': 0.45,       # 45% - цена важнее всего
        'rating': 0.30,      # 30% - рейтинг
        'reviews': 0.15,     # 15% - количество отзывов
        'availability': 0.10  # 10% - наличие
    }

    # Пороги для грейдов
    GRADE_THRESHOLDS = {
        CompetitivenessGrade.A: 0.85,  # >= 0.85
        CompetitivenessGrade.B: 0.70,  # >= 0.70
        CompetitivenessGrade.C: 0.50,  # >= 0.50
        CompetitivenessGrade.D: 0.30,  # >= 0.30
        CompetitivenessGrade.F: 0.00,  # < 0.30
    }

    def __init__(self):
        """Инициализация сервиса"""
        self.supabase = get_supabase_client()
        self.article_service = ArticleService()
        logger.info("✅ ComparisonService initialized")

    # ==================== Group Management ====================

    async def create_group(
        self,
        user_id: str,
        group_data: ArticleGroupCreate
    ) -> ArticleGroupResponse:
        """
        Создать новую группу сравнения

        Args:
            user_id: UUID пользователя
            group_data: Данные группы

        Returns:
            ArticleGroupResponse: Созданная группа
        """
        try:
            logger.info(f"Creating comparison group for user {user_id}")

            # Создаем группу в БД
            insert_data = {
                "user_id": user_id,
                "name": group_data.name,
                "group_type": group_data.group_type.value
            }

            result = self.supabase.table("ozon_scraper_article_groups").insert(insert_data).execute()

            if not result.data:
                raise ComparisonServiceError("Failed to create group")

            group = result.data[0]
            logger.info(f"✅ Group created: {group['id']}")

            return ArticleGroupResponse(
                id=group['id'],
                user_id=group['user_id'],
                name=group.get('name'),
                group_type=GroupType(group['group_type']),
                created_at=group['created_at'],
                updated_at=group['updated_at'],
                members_count=0
            )

        except Exception as e:
            logger.error(f"Error creating group: {e}")
            raise ComparisonServiceError(f"Failed to create group: {str(e)}")

    async def add_article_to_group(
        self,
        group_id: str,
        article_id: str,
        role: ArticleRole,
        position: int = 0
    ) -> bool:
        """
        Добавить артикул в группу

        Args:
            group_id: UUID группы
            article_id: UUID артикула
            role: Роль артикула в группе
            position: Позиция для сортировки

        Returns:
            bool: Успешность операции
        """
        try:
            logger.info(f"Adding article {article_id} to group {group_id} as {role}")

            insert_data = {
                "group_id": group_id,
                "article_id": article_id,
                "role": role.value,
                "position": position
            }

            result = self.supabase.table("ozon_scraper_article_group_members").insert(insert_data).execute()

            if result.data:
                logger.info(f"✅ Article added to group")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"Error adding article to group: {e}")
            return False

    async def get_group(self, group_id: str, user_id: str) -> ArticleGroupResponse:
        """
        Получить группу по ID

        Args:
            group_id: UUID группы
            user_id: UUID пользователя (для проверки прав)

        Returns:
            ArticleGroupResponse: Данные группы
        """
        try:
            result = self.supabase.table("ozon_scraper_article_groups").select("*").eq("id", group_id).eq("user_id", user_id).execute()

            if not result.data:
                raise GroupNotFoundError(f"Group {group_id} not found")

            group = result.data[0]

            # Получаем количество членов
            members_result = self.supabase.table("ozon_scraper_article_group_members").select("id", count="exact").eq("group_id", group_id).execute()
            members_count = members_result.count if members_result.count else 0

            return ArticleGroupResponse(
                id=group['id'],
                user_id=group['user_id'],
                name=group.get('name'),
                group_type=GroupType(group['group_type']),
                created_at=group['created_at'],
                updated_at=group['updated_at'],
                members_count=members_count
            )

        except GroupNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting group: {e}")
            raise ComparisonServiceError(f"Failed to get group: {str(e)}")

    async def delete_group(self, group_id: str, user_id: str) -> bool:
        """
        Удалить группу

        Args:
            group_id: UUID группы
            user_id: UUID пользователя (для проверки прав)

        Returns:
            bool: Успешность операции
        """
        try:
            logger.info(f"Deleting group {group_id}")

            result = self.supabase.table("ozon_scraper_article_groups").delete().eq("id", group_id).eq("user_id", user_id).execute()

            if result.data:
                logger.info(f"✅ Group deleted")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"Error deleting group: {e}")
            return False

    # ==================== Comparison ====================

    async def get_comparison(
        self,
        group_id: str,
        user_id: str,
        refresh: bool = False
    ) -> ComparisonResponse:
        """
        Получить сравнение артикулов в группе

        Args:
            group_id: UUID группы
            user_id: UUID пользователя
            refresh: Обновить данные с OZON перед сравнением

        Returns:
            ComparisonResponse: Полное сравнение с метриками
        """
        try:
            logger.info(f"Getting comparison for group {group_id}")

            # Проверяем группу
            group = await self.get_group(group_id, user_id)

            # Получаем все артикулы группы через SQL функцию
            result = self.supabase.rpc(
                "get_group_comparison",
                {"p_group_id": group_id}
            ).execute()

            if not result.data:
                logger.warning(f"No articles in group {group_id}")
                return ComparisonResponse(
                    group_id=group_id,
                    group_name=group.name,
                    group_type=group.group_type,
                    own_product=None,
                    competitors=[],
                    other_items=[],
                    metrics=None,
                    compared_at=datetime.now(),
                    is_fresh=True
                )

            # Группируем артикулы по ролям
            own_product = None
            competitors = []
            other_items = []

            for article_data in result.data:
                comparison_data = ArticleComparisonData(
                    article_id=article_data['article_id'],
                    article_number=article_data['article_number'],
                    role=ArticleRole(article_data['role']),
                    name=article_data['product_name'],
                    price=article_data['current_price'],
                    old_price=article_data['old_price'],
                    normal_price=article_data['normal_price'],
                    ozon_card_price=article_data['ozon_card_price'],
                    average_price_7days=article_data['average_price_7days'],
                    rating=article_data['current_rating'],
                    reviews_count=article_data['reviews_count'],
                    available=article_data['available'],
                    image_url=article_data['image_url'],
                    product_url=article_data['product_url'],
                    position=article_data['item_position']
                )

                if article_data['role'] == ArticleRole.OWN.value:
                    own_product = comparison_data
                elif article_data['role'] == ArticleRole.COMPETITOR.value:
                    competitors.append(comparison_data)
                else:
                    other_items.append(comparison_data)

            # Рассчитываем метрики (только для 1v1 сравнения)
            metrics = None
            if own_product and len(competitors) == 1:
                metrics = await self._calculate_comparison_metrics(own_product, competitors[0])

                # Сохраняем снэпшот
                await self._save_snapshot(group_id, own_product, competitors[0], metrics)

            # Проверяем свежесть данных (< 1 часа)
            is_fresh = self._check_data_freshness(result.data)

            return ComparisonResponse(
                group_id=group_id,
                group_name=group.name,
                group_type=group.group_type,
                own_product=own_product,
                competitors=competitors,
                other_items=other_items,
                metrics=metrics,
                compared_at=datetime.now(),
                is_fresh=is_fresh
            )

        except GroupNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting comparison: {e}")
            raise ComparisonServiceError(f"Failed to get comparison: {str(e)}")

    # ==================== Quick Create ====================

    async def quick_create_comparison(
        self,
        user_id: str,
        quick_data: QuickComparisonCreate
    ) -> ComparisonResponse:
        """
        Быстрое создание сравнения 1v1

        Создает группу, добавляет оба артикула, получает данные с OZON,
        рассчитывает метрики - все в одном запросе.

        Args:
            user_id: UUID пользователя
            quick_data: Данные для быстрого создания

        Returns:
            ComparisonResponse: Готовое сравнение с метриками
        """
        try:
            logger.info(f"Quick creating comparison: {quick_data.own_article_number} vs {quick_data.competitor_article_number}")

            # 1. Создаем группу
            group = await self.create_group(
                user_id,
                ArticleGroupCreate(
                    name=quick_data.group_name or f"{quick_data.own_article_number} vs {quick_data.competitor_article_number}",
                    group_type=GroupType.COMPARISON
                )
            )

            # 2. Получаем или создаем артикулы
            own_article = await self._get_or_create_article(
                user_id,
                quick_data.own_article_number,
                scrape=quick_data.scrape_now
            )

            competitor_article = await self._get_or_create_article(
                user_id,
                quick_data.competitor_article_number,
                scrape=quick_data.scrape_now
            )

            # 3. Добавляем в группу
            # Получаем ID из dict или объекта
            own_article_id = own_article.get('id') if isinstance(own_article, dict) else own_article.id
            competitor_article_id = competitor_article.get('id') if isinstance(competitor_article, dict) else competitor_article.id

            await self.add_article_to_group(group.id, own_article_id, ArticleRole.OWN, position=0)
            await self.add_article_to_group(group.id, competitor_article_id, ArticleRole.COMPETITOR, position=1)

            # 4. Получаем сравнение
            comparison = await self.get_comparison(group.id, user_id)

            logger.info(f"✅ Quick comparison created: {group.id}")
            return comparison

        except Exception as e:
            logger.error(f"Error in quick create comparison: {e}")
            raise ComparisonServiceError(f"Failed to create comparison: {str(e)}")

    # ==================== Metrics Calculation ====================

    async def _calculate_comparison_metrics(
        self,
        own: ArticleComparisonData,
        competitor: ArticleComparisonData
    ) -> ComparisonMetrics:
        """
        Рассчитать все метрики сравнения

        Args:
            own: Данные своего товара
            competitor: Данные конкурента

        Returns:
            ComparisonMetrics: Все метрики
        """
        # 1. Разница в ценах
        price_diff = self._calculate_price_difference(own, competitor)

        # 2. Разница в рейтингах
        rating_diff = self._calculate_rating_difference(own, competitor)

        # 3. Разница в отзывах
        reviews_diff = self._calculate_reviews_difference(own, competitor)

        # 4. Индекс конкурентоспособности
        comp_index = self._calculate_competitiveness_index(own, competitor)

        # 5. Грейд
        grade = self._get_grade(comp_index)

        # 6. Общая рекомендация
        overall_rec = self._generate_overall_recommendation(
            price_diff, rating_diff, reviews_diff, comp_index, grade
        )

        return ComparisonMetrics(
            price=price_diff,
            rating=rating_diff,
            reviews=reviews_diff,
            competitiveness_index=comp_index,
            grade=grade,
            overall_recommendation=overall_rec
        )

    def _calculate_price_difference(
        self,
        own: ArticleComparisonData,
        competitor: ArticleComparisonData
    ) -> PriceDifference:
        """Расчет разницы в ценах"""
        own_price = own.ozon_card_price or own.normal_price or own.price or 0
        comp_price = competitor.ozon_card_price or competitor.normal_price or competitor.price or 0

        if own_price == 0 or comp_price == 0:
            return PriceDifference(
                absolute=0,
                percentage=0,
                who_cheaper="equal",
                recommendation="Нет данных о ценах"
            )

        absolute = own_price - comp_price
        percentage = (absolute / comp_price) * 100

        if abs(percentage) < 1:
            who_cheaper = "equal"
            recommendation = "Цены примерно равны"
        elif absolute > 0:
            who_cheaper = "competitor"
            if percentage > 10:
                recommendation = f"Снизьте цену на {abs(percentage):.1f}% для конкурентоспособности"
            else:
                recommendation = "Ваша цена немного выше, но разница небольшая"
        else:
            who_cheaper = "own"
            recommendation = f"Отлично! Ваша цена ниже на {abs(percentage):.1f}%"

        return PriceDifference(
            absolute=round(absolute, 2),
            percentage=round(percentage, 2),
            who_cheaper=who_cheaper,
            recommendation=recommendation
        )

    def _calculate_rating_difference(
        self,
        own: ArticleComparisonData,
        competitor: ArticleComparisonData
    ) -> RatingDifference:
        """Расчет разницы в рейтингах"""
        own_rating = own.rating or 0
        comp_rating = competitor.rating or 0

        if own_rating == 0 or comp_rating == 0:
            return RatingDifference(
                absolute=0,
                percentage=0,
                who_better="equal",
                recommendation="Нет данных о рейтингах"
            )

        absolute = own_rating - comp_rating
        percentage = (absolute / comp_rating) * 100

        if abs(absolute) < 0.1:
            who_better = "equal"
            recommendation = "Рейтинги примерно равны"
        elif absolute > 0:
            who_better = "own"
            recommendation = f"Отлично! Ваш рейтинг выше на {absolute:.2f}"
        else:
            who_better = "competitor"
            recommendation = f"Работайте над качеством - рейтинг ниже на {abs(absolute):.2f}"

        return RatingDifference(
            absolute=round(absolute, 2),
            percentage=round(percentage, 2),
            who_better=who_better,
            recommendation=recommendation
        )

    def _calculate_reviews_difference(
        self,
        own: ArticleComparisonData,
        competitor: ArticleComparisonData
    ) -> ReviewsDifference:
        """Расчет разницы в отзывах"""
        own_reviews = own.reviews_count or 0
        comp_reviews = competitor.reviews_count or 0

        if own_reviews == 0 and comp_reviews == 0:
            return ReviewsDifference(
                absolute=0,
                percentage=0,
                who_more="equal",
                recommendation="Нет данных об отзывах"
            )

        absolute = own_reviews - comp_reviews
        percentage = (absolute / comp_reviews * 100) if comp_reviews != 0 else 0

        if own_reviews == comp_reviews:
            who_more = "equal"
            recommendation = "Количество отзывов одинаковое"
        elif absolute > 0:
            who_more = "own"
            recommendation = f"Хорошо! У вас больше отзывов на {absolute}"
        else:
            who_more = "competitor"
            if abs(percentage) > 50:
                recommendation = f"Стимулируйте отзывы - их на {abs(percentage):.0f}% меньше"
            else:
                recommendation = f"У конкурента больше отзывов на {abs(absolute)}"

        return ReviewsDifference(
            absolute=absolute,
            percentage=round(percentage, 2),
            who_more=who_more,
            recommendation=recommendation
        )

    def _calculate_competitiveness_index(
        self,
        own: ArticleComparisonData,
        competitor: ArticleComparisonData
    ) -> float:
        """
        Рассчитать индекс конкурентоспособности (0-1)

        Взвешенная формула с учетом всех факторов
        """
        scores = {}

        # 1. Цена (ниже = лучше)
        own_price = own.ozon_card_price or own.normal_price or own.price or 0
        comp_price = competitor.ozon_card_price or competitor.normal_price or competitor.price or 0

        if own_price > 0 and comp_price > 0:
            if own_price <= comp_price:
                scores['price'] = 1.0
            else:
                # Чем дороже, тем хуже score
                diff_pct = (own_price - comp_price) / comp_price
                scores['price'] = max(0, 1.0 - diff_pct)
        else:
            scores['price'] = 0.5

        # 2. Рейтинг (выше = лучше)
        own_rating = own.rating or 0
        comp_rating = competitor.rating or 0

        if own_rating > 0 and comp_rating > 0:
            scores['rating'] = own_rating / 5.0  # Нормализуем к 0-1
        else:
            scores['rating'] = 0.5

        # 3. Отзывы (больше = лучше, но с насыщением)
        own_reviews = own.reviews_count or 0
        comp_reviews = competitor.reviews_count or 0

        if own_reviews > 0:
            # Логарифмическое насыщение
            import math
            scores['reviews'] = min(1.0, math.log10(own_reviews + 1) / 3.0)
        else:
            scores['reviews'] = 0.1

        # 4. Наличие
        scores['availability'] = 1.0 if own.available else 0.0

        # Взвешенная сумма
        total_score = sum(scores[key] * self.WEIGHTS[key] for key in self.WEIGHTS)

        return round(total_score, 2)

    def _get_grade(self, index: float) -> CompetitivenessGrade:
        """Получить грейд по индексу"""
        if index >= self.GRADE_THRESHOLDS[CompetitivenessGrade.A]:
            return CompetitivenessGrade.A
        elif index >= self.GRADE_THRESHOLDS[CompetitivenessGrade.B]:
            return CompetitivenessGrade.B
        elif index >= self.GRADE_THRESHOLDS[CompetitivenessGrade.C]:
            return CompetitivenessGrade.C
        elif index >= self.GRADE_THRESHOLDS[CompetitivenessGrade.D]:
            return CompetitivenessGrade.D
        else:
            return CompetitivenessGrade.F

    def _generate_overall_recommendation(
        self,
        price_diff: PriceDifference,
        rating_diff: RatingDifference,
        reviews_diff: ReviewsDifference,
        index: float,
        grade: CompetitivenessGrade
    ) -> str:
        """Генерация общей рекомендации"""
        recommendations = []

        # Приоритет: цена > рейтинг > отзывы
        if price_diff.who_cheaper == "competitor":
            recommendations.append("🔴 Снизьте цену")

        if rating_diff.who_better == "competitor":
            recommendations.append("⚠️ Улучшайте качество товара")

        if reviews_diff.who_more == "competitor" and reviews_diff.percentage < -50:
            recommendations.append("💬 Стимулируйте отзывы")

        if not recommendations:
            return "✅ Отличная конкурентоспособность! Продолжайте в том же духе."

        return f"Грейд {grade.value} ({index:.2f}): " + ", ".join(recommendations[:2])

    # ==================== Snapshots ====================

    async def _save_snapshot(
        self,
        group_id: str,
        own: ArticleComparisonData,
        competitor: ArticleComparisonData,
        metrics: ComparisonMetrics
    ):
        """Сохранить снэпшот сравнения"""
        try:
            comparison_data = {
                "own": own.dict(),
                "competitor": competitor.dict()
            }

            metrics_data = {
                "price": metrics.price.dict(),
                "rating": metrics.rating.dict(),
                "reviews": metrics.reviews.dict(),
                "competitiveness_index": metrics.competitiveness_index,
                "grade": metrics.grade.value,
                "overall_recommendation": metrics.overall_recommendation
            }

            # Вызываем SQL функцию
            result = self.supabase.rpc(
                "save_comparison_snapshot",
                {
                    "p_group_id": group_id,
                    "p_comparison_data": json.dumps(comparison_data),
                    "p_metrics": json.dumps(metrics_data),
                    "p_competitiveness_index": metrics.competitiveness_index
                }
            ).execute()

            if result.data:
                logger.info(f"✅ Snapshot saved for group {group_id}")

        except Exception as e:
            logger.error(f"Error saving snapshot: {e}")

    async def get_comparison_history(
        self,
        group_id: str,
        user_id: str,
        days: int = 30
    ) -> ComparisonHistoryResponse:
        """
        Получить историю снэпшотов

        Args:
            group_id: UUID группы
            user_id: UUID пользователя
            days: Количество дней истории

        Returns:
            ComparisonHistoryResponse: История с массивом снэпшотов
        """
        try:
            # Проверяем права
            await self.get_group(group_id, user_id)

            # Получаем историю через SQL функцию
            result = self.supabase.rpc(
                "get_comparison_history",
                {
                    "p_group_id": group_id,
                    "p_days": days
                }
            ).execute()

            snapshots = []
            if result.data:
                for snapshot_data in result.data:
                    snapshots.append(ComparisonSnapshotResponse(
                        id=snapshot_data['snapshot_id'],
                        group_id=group_id,
                        snapshot_date=snapshot_data['snapshot_date'],
                        comparison_data=snapshot_data['comparison_data'],
                        metrics=snapshot_data['metrics'],
                        competitiveness_index=snapshot_data['competitiveness_index'],
                        created_at=snapshot_data['snapshot_date']
                    ))

            date_to = datetime.now()
            date_from = date_to - timedelta(days=days)

            return ComparisonHistoryResponse(
                group_id=group_id,
                snapshots=snapshots,
                total_count=len(snapshots),
                date_from=date_from,
                date_to=date_to
            )

        except GroupNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting comparison history: {e}")
            raise ComparisonServiceError(f"Failed to get history: {str(e)}")

    # ==================== User Statistics ====================

    async def get_user_stats(self, user_id: str) -> UserComparisonStats:
        """
        Получить статистику сравнений пользователя

        Args:
            user_id: UUID пользователя

        Returns:
            UserComparisonStats: Статистика
        """
        try:
            result = self.supabase.rpc(
                "get_user_groups_stats",
                {"p_user_id": user_id}
            ).execute()

            if result.data and len(result.data) > 0:
                stats = result.data[0]

                # Получаем дату последнего сравнения
                last_comp = self.supabase.table("ozon_scraper_comparison_snapshots") \
                    .select("created_at") \
                    .eq("group_id", user_id) \
                    .order("created_at", desc=True) \
                    .limit(1) \
                    .execute()

                last_date = None
                if last_comp.data:
                    last_date = last_comp.data[0]['created_at']

                return UserComparisonStats(
                    total_groups=stats.get('total_groups', 0),
                    comparison_groups=stats.get('comparison_groups', 0),
                    total_articles=stats.get('total_articles', 0),
                    avg_competitiveness_index=stats.get('avg_competitiveness_index'),
                    last_comparison_date=last_date
                )

            return UserComparisonStats()

        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return UserComparisonStats()

    # ==================== Helper Methods ====================

    async def _get_or_create_article(
        self,
        user_id: str,
        article_number: str,
        scrape: bool = True
    ):
        """
        Получить существующий артикул или создать новый

        Args:
            user_id: UUID пользователя
            article_number: Номер артикула
            scrape: Получить данные с OZON

        Returns:
            ArticleResponse: Артикул
        """
        try:
            # Ищем существующий
            result = self.supabase.table("ozon_scraper_articles") \
                .select("*") \
                .eq("user_id", user_id) \
                .eq("article_number", article_number) \
                .execute()

            if result.data and len(result.data) > 0:
                existing_article = result.data[0]
                logger.info(f"Article {article_number} already exists")
                
                # Если нужно обновить данные и артикул не имеет цен, обновляем
                if scrape:
                    # Проверяем, есть ли данные о ценах
                    has_price_data = (
                        existing_article.get("normal_price") or 
                        existing_article.get("ozon_card_price") or 
                        existing_article.get("price")
                    )
                    
                    # Если данных нет или они старые, обновляем
                    if not has_price_data:
                        logger.info(f"Article {article_number} exists but has no price data, updating...")
                        try:
                            # Используем update_article_data для обновления данных
                            updated = await self.article_service.update_article_data(existing_article["id"])
                            if updated:
                                # Получаем обновленный артикул
                                result = self.supabase.table("ozon_scraper_articles") \
                                    .select("*") \
                                    .eq("id", existing_article["id"]) \
                                    .execute()
                                if result.data:
                                    return result.data[0]
                        except Exception as update_error:
                            logger.warning(f"Failed to update article {article_number}: {update_error}")
                
                return existing_article

            # Создаем новый
            logger.info(f"Creating new article {article_number}")
            article = await self.article_service.create_article(
                user_id=user_id,
                article_number=article_number,
                report_frequency="once",  # По умолчанию для сравнений
                fetch_data=scrape
            )

            # Если article это dict, возвращаем как есть, иначе преобразуем
            if isinstance(article, dict):
                return article
            else:
                # Если это объект Pydantic, получаем из БД
                result = self.supabase.table("ozon_scraper_articles") \
                    .select("*") \
                    .eq("id", article.id) \
                    .execute()
                if result.data:
                    return result.data[0]
                return article

        except Exception as e:
            # Если возникла ошибка duplicate key, значит артикул уже существует
            # Пытаемся получить его из базы
            if "already exists" in str(e) or "duplicate key" in str(e) or "23505" in str(e):
                logger.warning(f"Article {article_number} already exists (caught duplicate key error), fetching it")
                result = self.supabase.table("ozon_scraper_articles") \
                    .select("*") \
                    .eq("user_id", user_id) \
                    .eq("article_number", article_number) \
                    .execute()

                if result.data and len(result.data) > 0:
                    return result.data[0]

            logger.error(f"Error in get_or_create_article: {e}")
            raise

    def _check_data_freshness(self, articles_data: List[dict], hours: int = 1) -> bool:
        """Проверить свежесть данных артикулов"""
        if not articles_data:
            return True

        threshold = datetime.now() - timedelta(hours=hours)

        for article in articles_data:
            last_check = article.get('last_check')
            if last_check:
                # Если это dict, пытаемся извлечь дату
                if isinstance(last_check, dict):
                    # Может быть поле 'created_at' или 'date' в dict
                    last_check = last_check.get('created_at') or last_check.get('date') or last_check.get('timestamp')
                    if not last_check:
                        continue
                
                # Преобразуем в datetime если это строка
                if isinstance(last_check, str):
                    try:
                        last_check = datetime.fromisoformat(last_check.replace('Z', '+00:00'))
                    except (ValueError, AttributeError):
                        continue
                # Проверяем что это действительно datetime объект
                elif not isinstance(last_check, datetime):
                    continue

                # Сравниваем даты
                try:
                    if last_check < threshold:
                        return False
                except TypeError:
                    # Если сравнение не удалось, пропускаем
                    continue

        return True
