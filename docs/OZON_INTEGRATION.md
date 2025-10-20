# OZON Integration - Руководство по интеграции

Практическое руководство по работе с OZON Service в проекте.

## 📦 Установка зависимостей

### Backend requirements

Добавьте в `backend/requirements.txt`:

```txt
# Web Scraping
playwright==1.48.0
beautifulsoup4==4.12.3
lxml==5.3.0
fake-useragent==1.5.1

# Уже установлены:
# httpx==0.27.2
# aiohttp==3.10.5
```

### Установка Playwright

После установки Python пакетов, установите браузеры:

```bash
cd backend
pip install playwright
playwright install chromium
```

## 🚀 Использование OzonService

### Базовое использование

```python
from services.ozon_service import get_ozon_service

# Получить сервис
ozon = get_ozon_service()

# Получить информацию о товаре
product = await ozon.get_product_info("123456789")

if product:
    print(f"Название: {product.name}")
    print(f"Цена: {product.price} ₽")
    print(f"Рейтинг: {product.rating} ⭐")
    print(f"В наличии: {product.available}")
else:
    print("Товар не найден")
```

### Получение только цены

```python
price = await ozon.get_product_price("123456789")
print(f"Цена: {price} ₽")
```

### Проверка наличия

```python
available = await ozon.check_availability("123456789")
if available:
    print("Товар в наличии!")
else:
    print("Товар закончился")
```

### Использование в FastAPI endpoint

```python
from fastapi import APIRouter, HTTPException
from services.ozon_service import get_ozon_service

router = APIRouter()

@router.get("/articles/{article_number}/check")
async def check_article(article_number: str):
    """Проверить артикул в OZON"""
    ozon = get_ozon_service()
    
    try:
        product = await ozon.get_product_info(article_number)
        
        if not product:
            raise HTTPException(status_code=404, detail="Товар не найден")
        
        return {
            "success": True,
            "data": product.to_dict()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## 🎯 Реализация с Playwright

### Пример полной реализации

```python
from playwright.async_api import async_playwright, Browser, Page
import asyncio

async def fetch_product_with_playwright(article: str) -> ProductInfo:
    """Получить товар используя Playwright"""
    
    async with async_playwright() as p:
        # Запустить браузер
        browser = await p.chromium.launch(headless=True)
        
        # Создать контекст с настройками
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        
        # Открыть страницу
        page = await context.new_page()
        
        try:
            # Перейти на страницу поиска
            url = f"https://www.ozon.ru/search/?text={article}"
            await page.goto(url, wait_until="networkidle")
            
            # Подождать загрузки результатов
            await page.wait_for_selector('[data-widget="searchResultsV2"]', timeout=10000)
            
            # Извлечь данные
            name = await page.locator('span[class*="tsBody500Medium"]').first.text_content()
            price_text = await page.locator('span[class*="tsHeadline500Medium"]').first.text_content()
            
            # Парсинг цены
            price = float(price_text.replace('₽', '').replace(' ', '').strip())
            
            # Создать ProductInfo
            product = ProductInfo(
                article=article,
                name=name,
                price=price,
                available=True,
                url=page.url,
            )
            
            return product
            
        finally:
            await context.close()
            await browser.close()
```

## 🔧 Конфигурация

### Настройки в .env

```env
# OZON Configuration
OZON_RATE_LIMIT=30
OZON_TIMEOUT=10
OZON_CACHE_TTL=3600
OZON_USE_PLAYWRIGHT=true

# Playwright
PLAYWRIGHT_HEADLESS=true
PLAYWRIGHT_TIMEOUT=30000
```

### Загрузка настроек

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OZON_RATE_LIMIT: int = 30
    OZON_TIMEOUT: int = 10
    OZON_CACHE_TTL: int = 3600
    OZON_USE_PLAYWRIGHT: bool = True
    
    PLAYWRIGHT_HEADLESS: bool = True
    PLAYWRIGHT_TIMEOUT: int = 30000
```

## 📊 Кеширование

### Встроенный кеш (Memory)

```python
# Использовать кеш (по умолчанию)
product = await ozon.get_product_info("123456", use_cache=True)

# Игнорировать кеш
product = await ozon.get_product_info("123456", use_cache=False)
```

### Redis кеширование (будущая версия)

```python
import redis.asyncio as redis
from typing import Optional

class OzonServiceWithRedis(OzonService):
    def __init__(self, redis_client: redis.Redis):
        super().__init__()
        self.redis = redis_client
    
    async def _get_from_cache(self, article: str) -> Optional[ProductInfo]:
        # Получить из Redis
        data = await self.redis.get(f"ozon:product:{article}")
        if data:
            return ProductInfo(**json.loads(data))
        return None
    
    async def _save_to_cache(self, article: str, product: ProductInfo):
        # Сохранить в Redis с TTL
        await self.redis.setex(
            f"ozon:product:{article}",
            self.cache_ttl,
            json.dumps(product.to_dict())
        )
```

## 🛡️ Обработка ошибок

### Retry с backoff

```python
import asyncio
from functools import wraps

def retry_with_backoff(max_retries=3, base_delay=1):
    """Декоратор для retry с экспоненциальным backoff"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Retry {attempt + 1}/{max_retries} after {delay}s")
                    await asyncio.sleep(delay)
        return wrapper
    return decorator

# Использование
@retry_with_backoff(max_retries=3, base_delay=2)
async def fetch_product(article: str):
    ozon = get_ozon_service()
    return await ozon.get_product_info(article)
```

### Rate Limiting

```python
import time
from collections import deque

class RateLimiter:
    """Rate limiter для ограничения запросов"""
    
    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
    
    async def acquire(self):
        """Ждать пока не освободится слот"""
        now = time.time()
        
        # Удалить старые запросы
        while self.requests and self.requests[0] < now - self.time_window:
            self.requests.popleft()
        
        # Проверить лимит
        if len(self.requests) >= self.max_requests:
            sleep_time = self.time_window - (now - self.requests[0])
            await asyncio.sleep(sleep_time)
        
        self.requests.append(now)

# Использование
rate_limiter = RateLimiter(max_requests=30, time_window=60)

async def safe_fetch(article: str):
    await rate_limiter.acquire()
    ozon = get_ozon_service()
    return await ozon.get_product_info(article)
```

## 🧪 Тестирование

### Unit тесты

```python
import pytest
from services.ozon_service import OzonService, ProductInfo

@pytest.mark.asyncio
async def test_get_product_info():
    """Тест получения информации о товаре"""
    ozon = OzonService()
    
    product = await ozon.get_product_info("123456789")
    
    assert product is not None
    assert product.article == "123456789"
    assert product.price > 0
    await ozon.close()

@pytest.mark.asyncio
async def test_cache():
    """Тест кеширования"""
    ozon = OzonService(cache_ttl=10)
    
    # Первый запрос (без кеша)
    product1 = await ozon.get_product_info("123456789")
    
    # Второй запрос (из кеша)
    product2 = await ozon.get_product_info("123456789")
    
    assert product1.article == product2.article
    assert product1.last_check == product2.last_check
    await ozon.close()
```

### Integration тесты

```python
@pytest.mark.asyncio
async def test_real_ozon_product():
    """Тест с реальным товаром OZON (требует интернет)"""
    ozon = OzonService()
    
    # Используйте реальный артикул для теста
    product = await ozon.get_product_info("реальный-артикул")
    
    if product:
        assert product.name is not None
        assert product.price > 0
        assert product.url.startswith("https://www.ozon.ru")
    
    await ozon.close()
```

## 📈 Мониторинг

### Логирование

```python
import logging

# Настроить логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('ozon_service')

# В коде
logger.info(f"Fetching product {article}")
logger.warning(f"Product {article} not found")
logger.error(f"Error: {e}")
```

### Метрики (Prometheus)

```python
from prometheus_client import Counter, Histogram

# Счетчики
ozon_requests_total = Counter('ozon_requests_total', 'Total OZON requests')
ozon_requests_failed = Counter('ozon_requests_failed', 'Failed OZON requests')
ozon_cache_hits = Counter('ozon_cache_hits', 'Cache hits')

# Гистограмма времени ответа
ozon_request_duration = Histogram('ozon_request_duration_seconds', 'Request duration')

# Использование
ozon_requests_total.inc()
with ozon_request_duration.time():
    product = await ozon.get_product_info(article)
```

## 🚧 Roadmap

### Phase 1: MVP (текущая) ✅
- ✅ Базовая структура OzonService
- ✅ Кеширование в памяти
- ✅ Заглушки для тестирования

### Phase 2: Playwright Implementation
- ⏭️ Реализация парсинга с Playwright
- ⏭️ Извлечение: name, price, rating, reviews
- ⏭️ Обработка ошибок и retry

### Phase 3: Optimization
- ⏭️ Redis кеширование
- ⏭️ Rate limiting
- ⏭️ Batch запросы
- ⏭️ Proxy ротация

### Phase 4: Advanced Features
- ⏭️ История изменения цен
- ⏭️ Уведомления о изменениях
- ⏭️ Мониторинг и алерты
- ⏭️ API endpoints для статистики

## 📚 Полезные ресурсы

- [Playwright Documentation](https://playwright.dev/python/)
- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [httpx Documentation](https://www.python-httpx.org/)
- [OZON для продавцов](https://seller.ozon.ru/)

---

**Статус:** 🚧 В разработке  
**Последнее обновление:** 2025-10-18


