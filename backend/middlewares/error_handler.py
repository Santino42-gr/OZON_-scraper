"""
Error Handler Middleware
Централизованная обработка ошибок приложения
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from loguru import logger
import traceback
from datetime import datetime

from config import settings


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Глобальный обработчик всех необработанных исключений
    
    Логирует ошибку с полным стеком и возвращает JSON ответ
    
    Args:
        request: FastAPI Request object
        exc: Exception object
        
    Returns:
        JSONResponse с информацией об ошибке
    """
    # Получаем информацию о запросе
    method = request.method
    path = request.url.path
    client_ip = request.client.host if request.client else "unknown"
    
    # Получаем полный стек ошибки
    error_traceback = traceback.format_exc()
    
    # Логируем ошибку
    logger.error(
        f"Global exception in {method} {path} from {client_ip}\n"
        f"Exception: {type(exc).__name__}: {str(exc)}\n"
        f"Traceback:\n{error_traceback}"
    )
    
    # Сохраняем ошибку в БД
    await save_error_log(
        method=method,
        path=path,
        error_type=type(exc).__name__,
        error_message=str(exc),
        error_traceback=error_traceback,
        client_ip=client_ip
    )
    
    # Формируем ответ
    error_response = {
        "error": "Internal Server Error",
        "message": str(exc) if settings.ENVIRONMENT == "development" else "An unexpected error occurred",
        "type": type(exc).__name__,
        "timestamp": datetime.now().isoformat(),
        "path": path
    }
    
    # В development режиме добавляем traceback
    if settings.ENVIRONMENT == "development":
        error_response["traceback"] = error_traceback.split("\n")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Обработчик ошибок валидации Pydantic
    
    Возвращает детальную информацию о том, какие поля не прошли валидацию
    
    Args:
        request: FastAPI Request object
        exc: RequestValidationError object
        
    Returns:
        JSONResponse с деталями ошибок валидации
    """
    # Логируем ошибку валидации
    logger.warning(
        f"Validation error in {request.method} {request.url.path}\n"
        f"Errors: {exc.errors()}"
    )
    
    # Форматируем ошибки для удобного чтения
    formatted_errors = []
    for error in exc.errors():
        formatted_errors.append({
            "field": " -> ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "message": "Request data validation failed",
            "details": formatted_errors,
            "timestamp": datetime.now().isoformat(),
            "path": request.url.path
        }
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Обработчик HTTP исключений (404, 403, и т.д.)
    
    Args:
        request: FastAPI Request object
        exc: HTTPException object
        
    Returns:
        JSONResponse с информацией об HTTP ошибке
    """
    # Логируем HTTP ошибки
    if exc.status_code >= 500:
        logger.error(f"HTTP {exc.status_code} in {request.method} {request.url.path}: {exc.detail}")
    elif exc.status_code >= 400:
        logger.warning(f"HTTP {exc.status_code} in {request.method} {request.url.path}: {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail if isinstance(exc.detail, str) else "HTTP Error",
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat(),
            "path": request.url.path
        }
    )


async def save_error_log(
    method: str,
    path: str,
    error_type: str,
    error_message: str,
    error_traceback: str,
    client_ip: str
):
    """
    Сохранить лог ошибки в БД
    
    Args:
        method: HTTP метод
        path: Путь запроса
        error_type: Тип ошибки (название класса исключения)
        error_message: Сообщение об ошибке
        error_traceback: Полный стек ошибки
        client_ip: IP клиента
    """
    try:
        from database import get_supabase_client
        
        supabase = get_supabase_client()
        
        error_data = {
            "level": "error",
            "event_type": "exception",
            "message": f"{error_type}: {error_message}",
            "metadata": {
                "method": method,
                "path": path,
                "error_type": error_type,
                "error_message": error_message,
                "error_traceback": error_traceback,
                "client_ip": client_ip
            },
            "created_at": datetime.now().isoformat()
        }
        
        supabase.table("logs").insert(error_data).execute()
        
    except Exception as e:
        # Не прерываем обработку если не удалось сохранить в БД
        logger.warning(f"Не удалось сохранить лог ошибки в БД: {e}")

