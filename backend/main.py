"""
OZON Bot Backend API
FastAPI приложение для обработки запросов от Telegram бота и админ-панели
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Routers будут импортированы позже
# from routers import articles, users, admin, health

app = FastAPI(
    title="OZON Bot API",
    description="Backend API для OZON Telegram Bot & Admin Panel MVP",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS настройки для frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В production укажите конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "service": "OZON Bot Backend API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "backend-api"}


# Подключение роутеров (будет позже)
# app.include_router(health.router, prefix="/health", tags=["Health"])
# app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
# app.include_router(articles.router, prefix="/api/v1/articles", tags=["Articles"])
# app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )

