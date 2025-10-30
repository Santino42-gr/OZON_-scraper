"""
Models Package
Pydantic модели для валидации данных
"""

from .article import (
    ArticleBase,
    ArticleCreate,
    ArticleUpdate,
    ArticleResponse,
    ArticleCheckResponse
)

from .user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserStatsResponse
)

from .report import (
    ReportRequest,
    ReportData,
    ReportResponse,
    ReportSummary
)

from .ozon_models import (
    ProductInfo,
    ProductPriceDetailed,
    ProductStock,
    ProductRating,
    ProductAvailability,
    ScrapingSource,
    ScrapingResult,
    OzonRequestLog,
    PriceHistory,
    PriceHistoryStats,
    OzonSearchResult,
    OzonAPIError
)

from .comparison import (
    ArticleRole,
    GroupType,
    CompetitivenessGrade,
    ArticleGroupCreate,
    ArticleGroupUpdate,
    ArticleGroupResponse,
    ArticleGroupMemberCreate,
    ArticleGroupMemberResponse,
    PriceDifference,
    RatingDifference,
    SPPDifference,
    ReviewsDifference,
    ComparisonMetrics,
    ArticleComparisonData,
    ComparisonResponse,
    ComparisonSnapshotCreate,
    ComparisonSnapshotResponse,
    ComparisonHistoryResponse,
    QuickComparisonCreate,
    UserComparisonStats
)

__all__ = [
    # Article models
    "ArticleBase",
    "ArticleCreate",
    "ArticleUpdate",
    "ArticleResponse",
    "ArticleCheckResponse",
    
    # User models
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserStatsResponse",
    
    # Report models
    "ReportRequest",
    "ReportData",
    "ReportResponse",
    "ReportSummary",
    
    # OZON models
    "ProductInfo",
    "ProductPriceDetailed",
    "ProductStock",
    "ProductRating",
    "ProductAvailability",
    "ScrapingSource",
    "ScrapingResult",
    "OzonRequestLog",
    "PriceHistory",
    "PriceHistoryStats",
    "OzonSearchResult",
    "OzonAPIError",

    # Comparison models
    "ArticleRole",
    "GroupType",
    "CompetitivenessGrade",
    "ArticleGroupCreate",
    "ArticleGroupUpdate",
    "ArticleGroupResponse",
    "ArticleGroupMemberCreate",
    "ArticleGroupMemberResponse",
    "PriceDifference",
    "RatingDifference",
    "SPPDifference",
    "ReviewsDifference",
    "ComparisonMetrics",
    "ArticleComparisonData",
    "ComparisonResponse",
    "ComparisonSnapshotCreate",
    "ComparisonSnapshotResponse",
    "ComparisonHistoryResponse",
    "QuickComparisonCreate",
    "UserComparisonStats",
]
