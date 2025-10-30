"""
Routers Package
API endpoints организованные по модулям
"""

from . import articles
from . import prices
from . import comparison
from . import users
from . import reports
from . import logs
from . import stats

__all__ = [
    "articles",
    "prices",
    "comparison",
    "users",
    "reports",
    "logs",
    "stats"
]
