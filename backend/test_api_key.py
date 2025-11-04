"""
Быстрый тест для проверки загрузки API ключа
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import settings

print(f"API Key from config: {settings.PARSER_MARKET_API_KEY}")
print(f"API Key length: {len(settings.PARSER_MARKET_API_KEY) if settings.PARSER_MARKET_API_KEY else 0}")
print(f"API Key starts with 'your': {settings.PARSER_MARKET_API_KEY.startswith('your') if settings.PARSER_MARKET_API_KEY else False}")

