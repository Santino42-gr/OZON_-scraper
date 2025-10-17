"""
Database module
Подключение к Supabase и базовые операции с БД
"""

from supabase import create_client, Client
from config import settings
from typing import Optional

# Глобальный клиент Supabase
_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """
    Получить клиент Supabase (singleton pattern)
    
    Returns:
        Client: Supabase client instance
    """
    global _supabase_client
    
    if _supabase_client is None:
        _supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY
        )
    
    return _supabase_client


async def check_database_connection() -> bool:
    """
    Проверить подключение к базе данных
    
    Returns:
        bool: True если подключение успешно
    """
    try:
        client = get_supabase_client()
        # Простой запрос для проверки подключения
        result = client.table("users").select("id").limit(1).execute()
        return True
    except Exception as e:
        print(f"Database connection error: {e}")
        return False

