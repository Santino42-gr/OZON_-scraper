"""
Handlers package
Обработчики команд и сообщений бота
"""

from . import start
from . import help
from . import onboarding
from . import articles
from . import reports
from . import stats
from . import common

__all__ = [
    "start",
    "help",
    "onboarding",
    "articles",
    "reports",
    "stats",
    "common",
]

