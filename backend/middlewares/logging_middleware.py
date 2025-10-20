"""
Logging Middleware
Middleware для логирования всех HTTP запросов
"""

import time
from fastapi import Request
from typing import Callable
from loguru import logger


async def log_requests(request: Request, call_next: Callable):
    """
    Middleware для логирования всех входящих HTTP запросов
    
    Логирует:
    - Метод и путь запроса
    - Время обработки
    - Статус код ответа
    - Client IP
    - User-Agent
    
    Args:
        request: FastAPI Request object
        call_next: Следующий middleware/handler в цепочке
        
    Returns:
        Response с добавленным заголовком X-Process-Time
    """
    # Начало обработки
    start_time = time.time()
    
    # Получаем информацию о запросе
    method = request.method
    path = request.url.path
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Логируем входящий запрос
    logger.info(f"→ {method} {path} from {client_ip}")
    
    # Обрабатываем запрос
    try:
        response = await call_next(request)
    except Exception as e:
        # Логируем ошибку
        process_time = time.time() - start_time
        logger.error(
            f"✗ {method} {path} failed after {process_time:.3f}s - Error: {str(e)}"
        )
        raise
    
    # Вычисляем время обработки
    process_time = time.time() - start_time
    
    # Логируем ответ
    status_code = response.status_code
    log_message = f"← {method} {path} [{status_code}] {process_time:.3f}s"
    
    # Разный уровень логирования в зависимости от статус кода
    if status_code >= 500:
        logger.error(log_message)
    elif status_code >= 400:
        logger.warning(log_message)
    else:
        logger.info(log_message)
    
    # Добавляем заголовок с временем обработки
    response.headers["X-Process-Time"] = f"{process_time:.3f}"
    
    # Сохраняем лог в БД (опционально)
    # await save_request_log(method, path, status_code, process_time, client_ip, user_agent)
    
    return response


async def save_request_log(
    method: str,
    path: str,
    status_code: int,
    process_time: float,
    client_ip: str,
    user_agent: str
):
    """
    Сохранить лог запроса в БД (опционально)
    
    Можно использовать для детальной аналитики запросов
    """
    try:
        from database import get_supabase_client
        from datetime import datetime
        
        supabase = get_supabase_client()
        
        log_data = {
            "level": "info" if status_code < 400 else "warning" if status_code < 500 else "error",
            "event_type": "http_request",
            "message": f"{method} {path} [{status_code}]",
            "metadata": {
                "method": method,
                "path": path,
                "status_code": status_code,
                "process_time": process_time,
                "client_ip": client_ip,
                "user_agent": user_agent
            },
            "created_at": datetime.now().isoformat()
        }
        
        supabase.table("logs").insert(log_data).execute()
        
    except Exception as e:
        # Не прерываем обработку запроса если не удалось сохранить лог
        logger.warning(f"Не удалось сохранить лог запроса в БД: {e}")

