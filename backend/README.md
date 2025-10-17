# Backend API - FastAPI

Backend API для OZON Bot MVP на основе FastAPI.

## 🚀 Быстрый старт

### Установка зависимостей

```bash
cd backend
python -m venv venv
source venv/bin/activate  # на Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Запуск в режиме разработки

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Запуск в production

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📁 Структура

```
backend/
├── main.py              # Точка входа приложения
├── config.py            # Конфигурация (загрузка .env)
├── database.py          # Подключение к Supabase
├── dependencies.py      # FastAPI dependencies
├── requirements.txt     # Python зависимости
├── routers/            # API endpoints
│   ├── __init__.py
│   ├── articles.py     # Операции с артикулами
│   ├── users.py        # Операции с пользователями
│   ├── admin.py        # Админ endpoints
│   └── health.py       # Health checks
├── services/           # Бизнес-логика
│   ├── __init__.py
│   ├── ozon_service.py # Интеграция с OZON API
│   ├── article_service.py
│   └── user_service.py
├── models/             # Pydantic модели
│   ├── __init__.py
│   ├── user.py
│   ├── article.py
│   └── request.py
└── utils/              # Утилиты
    ├── __init__.py
    ├── logger.py       # Логирование
    └── validators.py   # Валидаторы
```

## 📚 API Документация

После запуска доступна по адресам:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## 🔌 Endpoints

### Health Check
- `GET /health` - статус сервиса
- `GET /health/db` - проверка подключения к БД

### Users
- `GET /api/v1/users/{telegram_id}` - получить пользователя
- `POST /api/v1/users` - создать пользователя
- `PUT /api/v1/users/{telegram_id}` - обновить пользователя

### Articles
- `GET /api/v1/articles` - список артикулов (с пагинацией)
- `GET /api/v1/articles/{id}` - получить артикул
- `POST /api/v1/articles` - добавить артикул
- `DELETE /api/v1/articles/{id}` - удалить артикул
- `POST /api/v1/articles/{id}/check` - проверить артикул в OZON

### Admin
- `GET /api/v1/admin/users` - список всех пользователей
- `GET /api/v1/admin/stats` - статистика системы
- `GET /api/v1/admin/logs` - системные логи

## 🔒 Аутентификация

Используется Supabase Auth с JWT токенами.

Для защищенных endpoints передавайте токен в заголовке:
```
Authorization: Bearer <your-jwt-token>
```

## 🧪 Тестирование

```bash
# Установить зависимости для тестов
pip install pytest pytest-asyncio httpx

# Запустить тесты
pytest

# С coverage
pytest --cov=. --cov-report=html
```

## 📦 Зависимости

Основные:
- `fastapi` - веб-фреймворк
- `uvicorn[standard]` - ASGI сервер
- `supabase` - клиент для Supabase
- `pydantic` - валидация данных
- `python-dotenv` - работа с .env
- `httpx` - HTTP клиент
- `aiohttp` - асинхронные HTTP запросы

## 🐛 Отладка

Включите debug режим в `main.py`:

```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="debug")
```

## 📝 Переменные окружения

См. `env.example` в корне проекта:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `BACKEND_API_URL`
- `OZON_API_KEY` (если требуется)

## 🚀 Деплой

### Docker
```bash
docker build -t ozon-backend .
docker run -p 8000:8000 --env-file .env ozon-backend
```

### Railway / Render
1. Подключите GitHub репозиторий
2. Установите переменные окружения
3. Build command: `pip install -r backend/requirements.txt`
4. Start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

