"""
Routers Package
API endpoints организованные по модулям
"""

from . import articles
from . import users
from . import reports
from . import logs
from . import stats

__all__ = [
    "articles",
    "users",
    "reports",
    "logs",
    "stats"
]
