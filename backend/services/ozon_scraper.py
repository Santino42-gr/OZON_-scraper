"""
OZON Scraper Service

Web scraping для получения информации о товарах OZON через Playwright.

Features:
- Playwright для обхода антибот систем
- httpx + BeautifulSoup как fallback
- Retry логика с экспоненциальным backoff
- Rate limiting (Sliding Window)
- In-memory кэширование (TTL 1 час)
- Полное логирование всех запросов в БД

Author: AI Agent
Created: 2025-10-20
"""

import asyncio
import time
import uuid
import traceback
import random
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from collections import deque
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup
from loguru import logger

# Pydantic модели
from models.ozon_models import (
    ProductInfo,
    ProductPriceDetailed,
    ProductStock,
    ProductRating,
    ProductAvailability,
    ScrapingSource,
    ScrapingResult,
    OzonRequestLog
)

# Config
from config import settings


# ==================== Rate Limiter ====================

class RateLimiter:
    """
    Rate Limiter для ограничения количества запросов
    
    Использует алгоритм "Sliding Window" для точного контроля RPS.
    Поддерживает случайные задержки для имитации человеческого поведения.
    """
    
    def __init__(self, max_requests: int = 10, time_window: int = 60):
        """
        Args:
            max_requests: Максимум запросов в time_window
            time_window: Временное окно в секундах (по умолчанию 60)
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: deque = deque()
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """
        Ждать пока не освободится слот для запроса
        
        Блокирует выполнение если достигнут лимит запросов.
        Добавляет случайную задержку для имитации человека.
        """
        async with self._lock:
            now = time.time()
            
            # Удаляем старые запросы (вне окна)
            while self.requests and self.requests[0] < now - self.time_window:
                self.requests.popleft()
            
            # Если достигли лимита - ждем
            if len(self.requests) >= self.max_requests:
                sleep_time = self.time_window - (now - self.requests[0]) + 1
                if sleep_time > 0:
                    logger.warning(
                        f"⚠️  Rate limit reached ({len(self.requests)}/{self.max_requests}). "
                        f"Sleeping for {sleep_time:.1f}s"
                    )
                    await asyncio.sleep(sleep_time)
                    # Рекурсивно пробуем снова
                    return await self.acquire()
            
            # Добавляем случайную задержку (1-3 сек) для имитации человека
            random_delay = random.uniform(1.0, 3.0)
            if len(self.requests) > 0:
                await asyncio.sleep(random_delay)
            
            # Добавляем текущий запрос
            self.requests.append(time.time())
            
            logger.debug(
                f"Rate limiter: {len(self.requests)}/{self.max_requests} requests "
                f"in window (delay: {random_delay:.2f}s)"
            )


# ==================== Retry Logic ====================

async def retry_with_backoff(
    func,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    exceptions: tuple = (Exception,)
):
    """
    Retry decorator с экспоненциальным backoff
    
    Args:
        func: Async функция для выполнения
        max_retries: Максимум попыток
        base_delay: Базовая задержка между попытками (сек)
        max_delay: Максимальная задержка (сек)
        exceptions: Tuple исключений для retry
        
    Returns:
        Результат выполнения функции
        
    Raises:
        Последнее исключение если все попытки failed
    """
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            return await func()
        except exceptions as e:
            last_exception = e
            
            if attempt == max_retries - 1:
                # Последняя попытка - пробрасываем ошибку
                raise
            
            # Вычисляем задержку с экспоненциальным ростом + jitter
            delay = min(base_delay * (2 ** attempt), max_delay)
            jitter = random.uniform(0, delay * 0.1)  # 10% jitter
            total_delay = delay + jitter
            
            logger.warning(
                f"🔄 Attempt {attempt + 1}/{max_retries} failed: {type(e).__name__}: {str(e)}. "
                f"Retrying in {total_delay:.2f}s..."
            )
            
            await asyncio.sleep(total_delay)
    
    # На всякий случай
    raise last_exception


# ==================== OZON Scraper ====================

class OzonScraper:
    """
    Сервис для web scraping OZON
    
    Features:
    - Playwright для динамического контента (основной метод)
    - httpx + BeautifulSoup как fallback
    - Retry логика с экспоненциальным backoff
    - Rate limiting (Sliding Window)
    - In-memory кэширование (TTL 1 час)
    - Полное логирование в БД
    
    Usage:
        scraper = OzonScraper()
        product = await scraper.get_product_info("123456789")
        await scraper.close()
    """
    
    def __init__(
        self,
        cache_ttl: int = 3600,  # 1 час по умолчанию
        rate_limit: int = 10,
        timeout: int = 30
    ):
        """
        Инициализация сервиса
        
        Args:
            cache_ttl: Время жизни кэша в секундах (default: 3600 = 1 час)
            rate_limit: Максимум запросов в минуту
            timeout: Timeout запросов в секундах
        """
        self.base_url = "https://www.ozon.ru"
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, ProductInfo] = {}
        self._playwright = None
        self._browser = None
        self._context = None
        
        # Rate limiter
        self.rate_limiter = RateLimiter(max_requests=rate_limit, time_window=60)
        
        # HTTP клиент (fallback)
        self.client = httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers=self._get_default_headers()
        )
        
        # Статистика
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "playwright_requests": 0,
            "httpx_requests": 0
        }
        
        logger.info(
            f"🚀 OzonScraper initialized: cache_ttl={cache_ttl}s, "
            f"rate_limit={rate_limit}/min, timeout={timeout}s"
        )
    
    def _get_default_headers(self) -> Dict[str, str]:
        """Получить дефолтные HTTP заголовки"""
        return {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0"
        }
    
    async def _init_playwright(self):
        """Инициализация Playwright (lazy loading)"""
        if self._playwright is None:
            try:
                from playwright.async_api import async_playwright
                
                self._playwright = await async_playwright().start()
                self._browser = await self._playwright.chromium.launch(
                    headless=getattr(settings, 'PLAYWRIGHT_HEADLESS', True)
                )
                self._context = await self._browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent=self._get_default_headers()["User-Agent"]
                )
                
                logger.info("✅ Playwright initialized successfully")
                
            except ImportError:
                logger.error(
                    "❌ Playwright not installed! "
                    "Run: pip install playwright && playwright install chromium"
                )
                raise
            except Exception as e:
                logger.error(f"❌ Failed to initialize Playwright: {e}")
                raise
    
    async def close(self):
        """Закрыть все соединения"""
        if self.client:
            await self.client.aclose()
        
        if self._context:
            await self._context.close()
        
        if self._browser:
            await self._browser.close()
        
        if self._playwright:
            await self._playwright.stop()
        
        logger.info("🔒 OzonScraper closed")
    
    # ==================== Кэширование ====================
    
    def _get_from_cache(self, article: str) -> Optional[ProductInfo]:
        """Получить данные из кэша"""
        if article in self._cache:
            product = self._cache[article]
            age = (datetime.now() - product.last_check).total_seconds()
            
            if age < self.cache_ttl:
                self.stats["cache_hits"] += 1
                logger.info(f"💾 Cache HIT for {article} (age: {age:.1f}s)")
                return product
            else:
                logger.debug(f"⏰ Cache EXPIRED for {article} (age: {age:.1f}s)")
                del self._cache[article]
        
        self.stats["cache_misses"] += 1
        return None
    
    def _save_to_cache(self, article: str, product: ProductInfo):
        """Сохранить данные в кэш"""
        product.last_check = datetime.now()
        self._cache[article] = product
        logger.debug(f"💾 Cached product {article}")
    
    def clear_cache(self):
        """Очистить весь кэш"""
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"🧹 Cache cleared: {count} entries removed")
    
    # ==================== Логирование ====================
    
    async def _log_request(self, log: OzonRequestLog):
        """
        Сохранить лог запроса в БД
        
        Args:
            log: OzonRequestLog model
        """
        try:
            from database import get_supabase_client
            
            supabase = get_supabase_client()
            
            log_data = {
                "level": "error" if not log.success else "info",
                "event_type": f"ozon_{log.method}",
                "message": (
                    f"OZON {log.method} for {log.article}: "
                    f"{'SUCCESS' if log.success else 'FAILED'}"
                ),
                "metadata": {
                    "request_id": log.request_id,
                    "method": log.method,
                    "article": log.article,
                    "success": log.success,
                    "status_code": log.status_code,
                    "duration_ms": log.duration_ms,
                    "retry_count": log.retry_count,
                    "source": log.source.value,
                    "cache_hit": log.cache_hit,
                    "error_message": log.error_message,
                    "error_traceback": log.error_traceback
                },
                "created_at": log.start_time.isoformat()
            }
            
            supabase.table("ozon_scraper_logs").insert(log_data).execute()
            logger.debug(f"📝 Request log saved: {log.request_id}")
            
        except Exception as e:
            # Не прерываем работу если не удалось сохранить лог
            logger.warning(f"⚠️  Failed to save request log to DB: {e}")
    
    # ==================== URL Construction ====================
    
    def _construct_product_url(self, article: str) -> str:
        """
        Сконструировать URL товара на OZON
        
        Args:
            article: артикул товара
            
        Returns:
            URL для поиска товара
        """
        # OZON search URL
        return f"{self.base_url}/search/?text={quote(article)}"
    
    # ==================== HTML Parsing ====================
    
    def _parse_product_from_html(self, html: str, article: str) -> Optional[ProductInfo]:
        """
        Парсинг HTML страницы OZON для извлечения информации о товаре
        
        Args:
            html: HTML контент страницы
            article: артикул товара
            
        Returns:
            ProductInfo или None
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Ищем первый результат поиска (обычно это наш товар)
            search_results = soup.find_all('div', {'data-widget': 'searchResultsV2'})
            if not search_results:
                logger.warning(f"⚠️  No search results found for {article}")
                return None
            
            # Ищем карточку товара
            product_card = search_results[0].find('div', recursive=True)
            if not product_card:
                logger.warning(f"⚠️  No product card found for {article}")
                return None
            
            # === Парсинг названия товара ===
            name = None
            name_elem = soup.find('span', class_=lambda x: x and 'tsBody500Medium' in x)
            if name_elem:
                name = name_elem.get_text(strip=True)
            
            # === Парсинг цен ===
            # 1. Обычная цена (без Ozon Card) - черный текст
            normal_price = None
            normal_price_elem = soup.find('span', {'data-widget': 'webPrice'})
            if not normal_price_elem:
                # Альтернативный селектор
                normal_price_elem = soup.find('span', class_=lambda x: x and 'tsHeadline500Medium' in x)
            
            if normal_price_elem:
                price_text = normal_price_elem.get_text(strip=True)
                normal_price = self._parse_price_text(price_text)
            
            # 2. Цена с Ozon Card - фиолетовый текст
            ozon_card_price = None
            ozon_card_elem = soup.find('span', {'data-widget': 'webOzonCardPrice'})
            if not ozon_card_elem:
                # Альтернативный селектор
                ozon_card_elem = soup.find('span', class_=lambda x: x and 'ozonCard' in str(x).lower())
            
            if ozon_card_elem:
                price_text = ozon_card_elem.get_text(strip=True)
                ozon_card_price = self._parse_price_text(price_text)
            
            # 3. Старая цена (перечеркнутая)
            old_price = None
            old_price_elem = soup.find('span', class_=lambda x: x and 'line-through' in str(x))
            if not old_price_elem:
                old_price_elem = soup.find('s')
            
            if old_price_elem:
                price_text = old_price_elem.get_text(strip=True)
                old_price = self._parse_price_text(price_text)
            
            # Определяем основную цену
            price = ozon_card_price or normal_price
            
            # === Парсинг рейтинга ===
            rating = None
            rating_elem = soup.find('span', class_=lambda x: x and 'rating' in str(x).lower())
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                try:
                    rating = float(rating_text.replace(',', '.'))
                except:
                    pass
            
            # === Парсинг количества отзывов ===
            reviews_count = None
            reviews_elem = soup.find('span', string=lambda x: x and 'отзыв' in str(x).lower())
            if reviews_elem:
                reviews_text = reviews_elem.get_text(strip=True)
                try:
                    # Извлекаем число из текста типа "123 отзыва"
                    import re
                    match = re.search(r'\d+', reviews_text)
                    if match:
                        reviews_count = int(match.group())
                except:
                    pass
            
            # === Парсинг URL товара ===
            product_url = None
            link_elem = soup.find('a', href=lambda x: x and '/product/' in str(x))
            if link_elem:
                href = link_elem.get('href')
                if href.startswith('http'):
                    product_url = href
                elif href.startswith('/'):
                    product_url = f"{self.base_url}{href}"
            
            # === Парсинг изображения ===
            image_url = None
            img_elem = soup.find('img', src=lambda x: x and 'cdn' in str(x).lower())
            if img_elem:
                image_url = img_elem.get('src')
            
            # === Парсинг наличия ===
            availability = ProductAvailability.AVAILABLE
            if soup.find(string=lambda x: x and 'нет в наличии' in str(x).lower()):
                availability = ProductAvailability.OUT_OF_STOCK
            elif soup.find(string=lambda x: x and 'под заказ' in str(x).lower()):
                availability = ProductAvailability.PRE_ORDER
            
            # Если не нашли ни одну цену - товар не найден
            if not price and not normal_price:
                logger.warning(f"⚠️  No prices found for {article}")
                return None
            
            # Формируем результат
            product = ProductInfo(
                article=article,
                name=name or f"Product {article}",
                price=price,
                normal_price=normal_price,
                ozon_card_price=ozon_card_price,
                old_price=old_price,
                average_price_7days=None,  # Будет вычислено позже на основе истории
                rating=rating,
                reviews_count=reviews_count,
                availability=availability,
                image_url=image_url,
                url=product_url or self._construct_product_url(article),
                source=ScrapingSource.HTTPX
            )
            
            logger.info(
                f"✅ Parsed {article}: "
                f"normal_price={normal_price}, "
                f"ozon_card_price={ozon_card_price}, "
                f"name={name}"
            )
            
            return product
            
        except Exception as e:
            logger.error(f"❌ Error parsing HTML for {article}: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None
    
    def _parse_price_text(self, price_text: str) -> Optional[float]:
        """
        Парсинг цены из текста
        
        Args:
            price_text: Текст с ценой (например, "1 999 ₽", "1999", "1,999.00")
            
        Returns:
            Цена как float или None
        """
        try:
            # Убираем все кроме цифр, точек и запятых
            import re
            cleaned = re.sub(r'[^\d,.]', '', price_text)
            
            # Заменяем запятую на точку
            cleaned = cleaned.replace(',', '.')
            
            # Если несколько точек, оставляем только последнюю (десятичный разделитель)
            parts = cleaned.split('.')
            if len(parts) > 2:
                cleaned = ''.join(parts[:-1]) + '.' + parts[-1]
            
            # Конвертируем в float
            price = float(cleaned)
            
            return price if price > 0 else None
            
        except Exception as e:
            logger.debug(f"Failed to parse price from '{price_text}': {e}")
            return None
    
    # ==================== СПП Метрики ====================
    
    @staticmethod
    def calculate_spp_metrics(
        average_price_7days: Optional[float],
        normal_price: Optional[float],
        ozon_card_price: Optional[float]
    ) -> Dict[str, Optional[float]]:
        """
        Рассчитать показатели СПП (скидки)
        
        Формулы:
        - СПП1 = (Средняя за 7 дней - Обычная цена) / Средняя за 7 дней × 100%
        - СПП2 = (Обычная цена - Цена с картой) / Обычная цена × 100%
        - СПП Общий = (Средняя за 7 дней - Цена с картой) / Средняя за 7 дней × 100%
        
        Args:
            average_price_7days: Средняя цена за 7 дней
            normal_price: Цена без Ozon Card
            ozon_card_price: Цена с Ozon Card
            
        Returns:
            Dict с ключами spp1, spp2, spp_total (значения в процентах или None)
        """
        spp1 = None
        spp2 = None
        spp_total = None
        
        # СПП1: (avg - normal) / avg * 100
        if average_price_7days and average_price_7days > 0 and normal_price is not None:
            spp1 = round((average_price_7days - normal_price) / average_price_7days * 100, 1)
        
        # СПП2: (normal - card) / normal * 100
        if normal_price and normal_price > 0 and ozon_card_price is not None:
            spp2 = round((normal_price - ozon_card_price) / normal_price * 100, 1)
        
        # СПП Общий: (avg - card) / avg * 100
        if average_price_7days and average_price_7days > 0 and ozon_card_price is not None:
            spp_total = round((average_price_7days - ozon_card_price) / average_price_7days * 100, 1)
        
        return {
            "spp1": spp1,
            "spp2": spp2,
            "spp_total": spp_total
        }
    
    # ==================== Scraping Methods ====================
    
    async def _scrape_with_playwright(self, article: str) -> Optional[ProductInfo]:
        """
        Scrape информацию о товаре используя Playwright
        
        Основной метод для обхода антибот систем.
        
        Args:
            article: артикул товара
            
        Returns:
            ProductInfo или None
        """
        try:
            # Инициализируем Playwright если еще не инициализирован
            await self._init_playwright()
            
            # Создаем новую страницу
            page = await self._context.new_page()
            
            try:
                url = self._construct_product_url(article)
                logger.info(f"🌐 Scraping {article} via Playwright: {url}")
                
                # Переходим на страницу
                response = await page.goto(url, wait_until="domcontentloaded")
                
                # Проверяем статус
                if response.status != 200:
                    logger.warning(f"⚠️  HTTP {response.status} for {article}")
                    if response.status == 403:
                        raise httpx.HTTPStatusError(
                            f"403 Forbidden for {url}",
                            request=None,
                            response=response
                        )
                
                # Ждем загрузки контента (можно настроить селекторы)
                try:
                    await page.wait_for_selector('[data-widget="searchResultsV2"]', timeout=5000)
                except:
                    logger.warning(f"⚠️  Timeout waiting for search results for {article}")
                
                # Получаем HTML
                html = await page.content()
                
                # Парсим
                product = self._parse_product_from_html(html, article)
                
                if product:
                    product.source = ScrapingSource.PLAYWRIGHT
                    self.stats["playwright_requests"] += 1
                
                return product
                
            finally:
                await page.close()
                
        except Exception as e:
            logger.error(f"❌ Playwright scraping failed for {article}: {e}")
            raise
    
    async def _scrape_with_httpx(self, article: str) -> Optional[ProductInfo]:
        """
        Scrape информацию о товаре используя httpx (fallback метод)
        
        Args:
            article: артикул товара
            
        Returns:
            ProductInfo или None
        """
        try:
            url = self._construct_product_url(article)
            logger.info(f"🌐 Scraping {article} via httpx: {url}")
            
            response = await self.client.get(url)
            response.raise_for_status()
            
            # Парсим HTML
            product = self._parse_product_from_html(response.text, article)
            
            if product:
                product.source = ScrapingSource.HTTPX
                self.stats["httpx_requests"] += 1
            
            return product
        
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ HTTP {e.response.status_code} for {article}")
            
            # Если 403 - переключаемся на Playwright
            if e.response.status_code == 403:
                logger.info(f"🔄 Switching to Playwright for {article}")
                return await self._scrape_with_playwright(article)
            
            raise
        
        except Exception as e:
            logger.error(f"❌ httpx scraping failed for {article}: {e}")
            return None
    
    # ==================== Public API ====================
    
    async def get_product_info(
        self,
        article: str,
        use_cache: bool = True,
        force_playwright: bool = False
    ) -> Optional[ProductInfo]:
        """
        Получить полную информацию о товаре
        
        Args:
            article: артикул товара OZON
            use_cache: использовать кэш
            force_playwright: принудительно использовать Playwright
            
        Returns:
            ProductInfo или None если товар не найден
        """
        request_id = str(uuid.uuid4())
        start_time = datetime.now()
        cache_hit = False
        retry_count = 0
        
        self.stats["total_requests"] += 1
        
        # Проверить кэш
        if use_cache:
            cached = self._get_from_cache(article)
            if cached:
                cache_hit = True
                
                # Логируем cache hit
                await self._log_request(OzonRequestLog(
                    request_id=request_id,
                    method="get_product_info",
                    article=article,
                    success=True,
                    start_time=start_time,
                    end_time=datetime.now(),
                    duration_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                    source=ScrapingSource.CACHE,
                    cache_hit=True,
                    retry_count=0
                ))
                
                return cached
        
        # Rate limiting
        await self.rate_limiter.acquire()
        
        # Функция для retry
        async def fetch_product():
            nonlocal retry_count
            retry_count += 1
            
            if force_playwright:
                return await self._scrape_with_playwright(article)
            else:
                # Сначала пробуем httpx (быстрее)
                return await self._scrape_with_httpx(article)
        
        try:
            # Выполняем с retry
            product = await retry_with_backoff(
                fetch_product,
                max_retries=3,
                base_delay=1.0,
                exceptions=(httpx.TimeoutException, httpx.HTTPError)
            )
            
            end_time = datetime.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            if product:
                product.fetch_time_ms = duration_ms
                
                # Сохранить в кэш
                if use_cache:
                    self._save_to_cache(article, product)
                
                self.stats["successful_requests"] += 1
                
                # Логируем успех
                await self._log_request(OzonRequestLog(
                    request_id=request_id,
                    method="get_product_info",
                    article=article,
                    success=True,
                    status_code=200,
                    start_time=start_time,
                    end_time=end_time,
                    duration_ms=duration_ms,
                    source=product.source,
                    cache_hit=cache_hit,
                    retry_count=retry_count - 1
                ))
                
                logger.success(f"✅ Successfully scraped {article} in {duration_ms}ms")
                
                return product
            else:
                self.stats["failed_requests"] += 1
                
                # Товар не найден
                await self._log_request(OzonRequestLog(
                    request_id=request_id,
                    method="get_product_info",
                    article=article,
                    success=False,
                    status_code=404,
                    start_time=start_time,
                    end_time=datetime.now(),
                    duration_ms=duration_ms,
                    error_message="Product not found",
                    source=ScrapingSource.HTTPX,
                    cache_hit=False,
                    retry_count=retry_count - 1
                ))
                
                logger.warning(f"⚠️  Product not found: {article}")
                
                return None
        
        except Exception as e:
            end_time = datetime.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            error_traceback = traceback.format_exc()
            
            self.stats["failed_requests"] += 1
            
            logger.error(f"❌ Error fetching product {article}: {e}")
            
            # Логируем ошибку
            await self._log_request(OzonRequestLog(
                request_id=request_id,
                method="get_product_info",
                article=article,
                success=False,
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration_ms,
                error_message=str(e),
                error_traceback=error_traceback,
                source=ScrapingSource.HTTPX,
                cache_hit=False,
                retry_count=retry_count - 1
            ))
            
            return None
    
    async def get_product_prices_detailed(self, article: str) -> Optional[ProductPriceDetailed]:
        """
        Получить детальную информацию о ценах товара
        
        Включает цены с/без Ozon Card, старую цену, среднюю за 7 дней.
        
        Args:
            article: артикул товара
            
        Returns:
            ProductPriceDetailed или None
        """
        product = await self.get_product_info(article)
        
        if not product:
            return None
        
        # Получаем среднюю цену за 7 дней из БД
        average_price_7days = await self._get_average_price_from_db(article)
        
        return ProductPriceDetailed(
            article=article,
            price=product.price,
            normal_price=product.normal_price,
            ozon_card_price=product.ozon_card_price,
            old_price=product.old_price,
            average_price_7days=average_price_7days,
            last_updated=product.last_check
        )
    
    async def _get_average_price_from_db(self, article: str) -> Optional[float]:
        """
        Получить среднюю цену за 7 дней из БД
        
        Args:
            article: артикул товара
            
        Returns:
            Средняя цена или None
        """
        try:
            from database import get_supabase_client
            
            supabase = get_supabase_client()
            
            # Вызываем SQL функцию get_average_price_7days
            result = supabase.rpc(
                "get_average_price_7days",
                {"p_article_number": article, "p_days": 7}
            ).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0].get("avg_price")
            
            return None
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to get average price from DB: {e}")
            return None
    
    async def get_product_stock(self, article: str) -> Optional[ProductStock]:
        """
        Получить информацию об остатках товара
        
        Args:
            article: артикул товара
            
        Returns:
            ProductStock или None
        """
        product = await self.get_product_info(article)
        
        if not product:
            return None
        
        return ProductStock(
            article=article,
            availability=product.availability,
            stock_count=product.stock_count,
            last_updated=product.last_check
        )
    
    async def get_product_rating(self, article: str) -> Optional[ProductRating]:
        """
        Получить информацию о рейтинге товара
        
        Args:
            article: артикул товара
            
        Returns:
            ProductRating или None
        """
        product = await self.get_product_info(article)
        
        if not product or not product.rating:
            return None
        
        return ProductRating(
            article=article,
            rating=product.rating,
            reviews_count=product.reviews_count or 0,
            last_updated=product.last_check
        )
    
    async def check_availability(self, article: str) -> bool:
        """
        Проверить наличие товара
        
        Args:
            article: артикул товара
            
        Returns:
            True если товар в наличии
        """
        product = await self.get_product_info(article)
        return product.available if product else False
    
    async def scrape_multiple_products(
        self,
        articles: List[str],
        use_cache: bool = True
    ) -> Dict[str, Optional[ProductInfo]]:
        """
        Scrape несколько товаров (batch processing)
        
        Args:
            articles: список артикулов
            use_cache: использовать кэш
            
        Returns:
            Словарь {article: ProductInfo}
        """
        results = {}
        
        logger.info(f"📦 Batch scraping {len(articles)} products...")
        
        for article in articles:
            try:
                product = await self.get_product_info(article, use_cache=use_cache)
                results[article] = product
            except Exception as e:
                logger.error(f"❌ Failed to scrape {article}: {e}")
                results[article] = None
        
        successful = sum(1 for p in results.values() if p is not None)
        logger.info(f"✅ Batch scraping completed: {successful}/{len(articles)} successful")
        
        return results
    
    # ==================== Statistics ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Получить статистику работы scraper
        
        Returns:
            Словарь со статистикой
        """
        cache_hit_rate = (
            (self.stats["cache_hits"] / max(self.stats["total_requests"], 1)) * 100
            if self.stats["total_requests"] > 0
            else 0
        )
        
        success_rate = (
            (self.stats["successful_requests"] / max(self.stats["total_requests"], 1)) * 100
            if self.stats["total_requests"] > 0
            else 0
        )
        
        return {
            **self.stats,
            "cache_size": len(self._cache),
            "cache_hit_rate": round(cache_hit_rate, 2),
            "success_rate": round(success_rate, 2)
        }
    
    def print_stats(self):
        """Вывести статистику в консоль"""
        stats = self.get_stats()
        
        logger.info("="*60)
        logger.info("📊 OZON Scraper Statistics:")
        logger.info("="*60)
        logger.info(f"Total requests: {stats['total_requests']}")
        logger.info(f"Successful: {stats['successful_requests']}")
        logger.info(f"Failed: {stats['failed_requests']}")
        logger.info(f"Success rate: {stats['success_rate']}%")
        logger.info(f"Cache hits: {stats['cache_hits']}")
        logger.info(f"Cache misses: {stats['cache_misses']}")
        logger.info(f"Cache hit rate: {stats['cache_hit_rate']}%")
        logger.info(f"Cache size: {stats['cache_size']}")
        logger.info(f"Playwright requests: {stats['playwright_requests']}")
        logger.info(f"httpx requests: {stats['httpx_requests']}")
        logger.info("="*60)


# ==================== Singleton ====================

_ozon_scraper_instance: Optional[OzonScraper] = None


def get_ozon_scraper() -> OzonScraper:
    """
    Получить singleton экземпляр OzonScraper
    
    Returns:
        OzonScraper instance
    """
    global _ozon_scraper_instance
    if _ozon_scraper_instance is None:
        _ozon_scraper_instance = OzonScraper(
            cache_ttl=getattr(settings, 'OZON_CACHE_TTL', 3600),
            rate_limit=getattr(settings, 'OZON_RATE_LIMIT', 10),
            timeout=getattr(settings, 'OZON_TIMEOUT', 30)
        )
    return _ozon_scraper_instance

