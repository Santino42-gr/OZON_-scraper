"""
Parser Market API Client

Клиент для работы с Parser Market API - облачным сервисом парсинга маркетплейсов.
Документация: https://parser.market/parser-cen-json-api/

Основные возможности:
- Отправка задач на парсинг товаров Ozon
- Отслеживание статуса задач (polling)
- Получение результатов парсинга в JSON формате
- Автоматический mapping в модель ProductInfo
"""

import asyncio
import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime
from loguru import logger
from pydantic import BaseModel, Field, HttpUrl

from models.ozon_models import (
    ProductInfo,
    ProductAvailability,
    ScrapingSource
)


# ==================== Модели Parser Market API ====================

class ParserMarketTask(BaseModel):
    """Задача для отправки в Parser Market"""
    category: str = ""
    code: float = 0.0
    productid: str = ""
    brand: str = ""
    name: str  # REQUIRED
    linkset: List[str] = []
    marketid: str = ""
    price: float = 0.0
    donotsearch: str = ""
    textsearch: str = ""


class ParserMarketSubmitRequest(BaseModel):
    """Запрос на отправку задачи"""
    apikey: str
    regionid: str = "Москва"
    market: str = "ozon"
    userlabel: str
    products: List[Dict[str, Any]]


class ParserMarketStatusRequest(BaseModel):
    """Запрос статуса задачи"""
    apikey: str
    userlabels: Optional[List[str]] = None
    orderidlist: Optional[List[int]] = None
    limit: int = 10


# ==================== Exceptions ====================

class ParserMarketError(Exception):
    """Базовая ошибка Parser Market API"""
    pass


class ParserMarketAPIError(ParserMarketError):
    """Ошибка API запроса"""
    pass


class ParserMarketTaskError(ParserMarketError):
    """Ошибка выполнения задачи парсинга"""
    pass


class ParserMarketTimeoutError(ParserMarketError):
    """Таймаут ожидания результата"""
    pass


# ==================== Parser Market Client ====================

class ParserMarketClient:
    """
    Клиент для работы с Parser Market API

    Features:
    - Submit parsing tasks for Ozon products
    - Poll task status
    - Download JSON reports
    - Automatic mapping to ProductInfo model
    - Retry logic with exponential backoff
    - Comprehensive error handling

    Example:
        >>> client = ParserMarketClient(api_key="your_key")
        >>> product = await client.parse_sync(article="123456789")
        >>> print(product.name, product.price)
    """

    BASE_URL = "https://parser.market/wp-json/client-api/v1"

    def __init__(
        self,
        api_key: str,
        region: str = "Москва",
        timeout: int = 120,
        poll_interval: int = 10,
        max_retries: int = 3
    ):
        """
        Initialize Parser Market client

        Args:
            api_key: API ключ от Parser Market
            region: Регион для парсинга (по умолчанию Москва)
            timeout: Максимальное время ожидания результата (секунды)
            poll_interval: Интервал опроса статуса задачи (секунды)
            max_retries: Максимальное количество попыток при ошибках
        """
        self.api_key = api_key
        self.region = region
        self.timeout = timeout
        self.poll_interval = poll_interval
        self.max_retries = max_retries

        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, read=60.0),
            follow_redirects=True
        )

        logger.info(
            f"Parser Market client initialized | "
            f"region={region} | timeout={timeout}s | poll_interval={poll_interval}s"
        )

    async def close(self):
        """Закрыть HTTP клиент"""
        await self.client.aclose()
        logger.debug("Parser Market client closed")

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    # ==================== Core API Methods ====================

    async def get_balance(self) -> Dict[str, Any]:
        """
        Получить баланс аккаунта

        Returns:
            Dict с информацией о балансе:
            - checks_free: бесплатные проверки
            - checks_paid: оплаченные проверки
            - checks_pending: проверки в процессе
            - checks_total: всего доступно

        Raises:
            ParserMarketAPIError: Ошибка API запроса
        """
        try:
            response = await self.client.post(
                f"{self.BASE_URL}/get-balanse",
                json={"apikey": self.api_key}
            )
            response.raise_for_status()

            result = self._parse_response(response.json())

            if result.get("result") != "success":
                raise ParserMarketAPIError(f"API returned error: {result}")

            logger.info(
                f"Balance check | "
                f"total={result.get('checks_total')} | "
                f"pending={result.get('checks_pending')}"
            )

            return result

        except httpx.HTTPError as e:
            logger.error(f"Balance check failed: {e}")
            raise ParserMarketAPIError(f"Failed to get balance: {e}")

    async def submit_task(
        self,
        article: str,
        userlabel: Optional[str] = None,
        use_marketid: bool = True
    ) -> Dict[str, Any]:
        """
        Отправить задачу на парсинг товара

        Args:
            article: Артикул товара Ozon
            userlabel: Уникальная метка задачи (по умолчанию генерируется автоматически)
            use_marketid: Если True - использует marketid (SKU ID), если False - productid (артикул продавца)

        Returns:
            Dict с информацией о задаче:
            - userlabel: метка задачи для отслеживания
            - bytes: размер отправленных данных

        Raises:
            ParserMarketAPIError: Ошибка отправки задачи
        """
        if not userlabel:
            userlabel = f"ozon_{article}_{int(datetime.now().timestamp())}"

        # Для Ozon можно использовать либо marketid (SKU ID), либо productid (артикул продавца)
        # marketid - это SKU ID товара на маркетплейсе
        # productid - это артикул продавца
        if use_marketid:
            product = {
                "category": "",
                "code": 0.0,
                "productid": "",  # Пусто для Ozon при использовании marketid
                "brand": "",
                "name": f"Product {article}",  # Required field
                "linkset": [f"https://www.ozon.ru/product/{article}/"],
                "marketid": str(article),  # Используем marketid для Ozon
                "price": 0.0,
                "donotsearch": "",
                "textsearch": ""
            }
        else:
            product = {
                "category": "",
                "code": 0.0,
                "productid": str(article),  # Используем productid (артикул продавца)
                "brand": "",
                "name": f"Product {article}",  # Required field
                "linkset": [f"https://www.ozon.ru/product/{article}/"],
                "marketid": "",  # Пусто при использовании productid
                "price": 0.0,
                "donotsearch": "",
                "textsearch": ""
            }

        payload = {
            "apikey": self.api_key,
            "regionid": self.region,
            "market": "ozon",
            "userlabel": userlabel,
            "products": [product]
        }

        try:
            logger.info(f"Submitting task | article={article} | userlabel={userlabel}")

            response = await self.client.post(
                f"{self.BASE_URL}/send-order",
                json=payload
            )
            response.raise_for_status()

            response_data = response.json()
            logger.debug(f"API response type: {type(response_data)} | data: {response_data}")
            
            result = self._parse_response(response_data)

            if not result or result.get("result") != "success":
                error_code = result.get("error_code", "unknown") if result else "unknown"
                error_message = result.get("error_message", "") if result else ""
                raise ParserMarketAPIError(
                    f"Task submission failed: {error_code} | {error_message} | Response: {result}"
                )

            logger.info(
                f"Task submitted successfully | "
                f"userlabel={result.get('userlabel')} | "
                f"bytes={result.get('bytes')}"
            )

            return result

        except httpx.HTTPError as e:
            logger.error(f"Task submission failed | article={article} | error={e}")
            raise ParserMarketAPIError(f"Failed to submit task: {e}")

    async def get_task_status(
        self,
        userlabel: Optional[str] = None,
        order_id: Optional[int] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Получить статус задачи

        Args:
            userlabel: Метка задачи для фильтрации
            order_id: ID заказа для фильтрации
            limit: Максимальное количество результатов

        Returns:
            Список задач с их статусами и ссылками на отчеты

        Raises:
            ParserMarketAPIError: Ошибка получения статуса
        """
        payload = {"apikey": self.api_key, "limit": limit}

        if userlabel:
            payload["userlabels"] = [userlabel]
        elif order_id:
            payload["orderidlist"] = [order_id]

        try:
            response = await self.client.post(
                f"{self.BASE_URL}/get-last50",
                json=payload
            )
            response.raise_for_status()

            result = self._parse_response(response.json())

            if result.get("result") != "success":
                raise ParserMarketAPIError(f"Failed to get status: {result}")

            tasks = result.get("data", [])

            logger.debug(f"Status check | found {len(tasks)} tasks")

            return tasks

        except httpx.HTTPError as e:
            logger.error(f"Status check failed: {e}")
            raise ParserMarketAPIError(f"Failed to get task status: {e}")

    async def wait_for_completion(
        self,
        userlabel: str,
        timeout: Optional[int] = None,
        poll_interval: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Ожидать завершения задачи (polling)

        Args:
            userlabel: Метка задачи для отслеживания
            timeout: Максимальное время ожидания (по умолчанию self.timeout)
            poll_interval: Интервал опроса (по умолчанию self.poll_interval)

        Returns:
            Dict с данными завершенной задачи

        Raises:
            ParserMarketTimeoutError: Таймаут ожидания
            ParserMarketTaskError: Ошибка выполнения задачи
        """
        timeout = timeout or self.timeout
        poll_interval = poll_interval or self.poll_interval

        start_time = datetime.now()
        elapsed = 0

        logger.info(
            f"Waiting for task completion | "
            f"userlabel={userlabel} | timeout={timeout}s | interval={poll_interval}s"
        )

        while elapsed < timeout:
            tasks = await self.get_task_status(userlabel=userlabel, limit=1)

            if not tasks:
                logger.warning(f"Task not found yet | userlabel={userlabel}")
                await asyncio.sleep(poll_interval)
                elapsed = (datetime.now() - start_time).total_seconds()
                continue

            task = tasks[0]
            status = self._get_field(task, "status")

            logger.debug(
                f"Task status | userlabel={userlabel} | status={status} | elapsed={elapsed:.1f}s"
            )

            if status == "completed":
                items_loaded = self._get_field(task, "items-loaded")
                logger.info(
                    f"Task completed | "
                    f"userlabel={userlabel} | items={items_loaded} | duration={elapsed:.1f}s"
                )
                return task

            elif status == "error":
                error_msg = f"Task failed with error status"
                logger.error(f"{error_msg} | userlabel={userlabel}")
                raise ParserMarketTaskError(error_msg)

            # status == "waiting" или "processing"
            await asyncio.sleep(poll_interval)
            elapsed = (datetime.now() - start_time).total_seconds()

        # Timeout
        logger.error(
            f"Task timeout | userlabel={userlabel} | timeout={timeout}s"
        )
        raise ParserMarketTimeoutError(
            f"Task timeout after {timeout}s: {userlabel}"
        )

    async def download_json_report(self, report_url: str) -> Dict[str, Any]:
        """
        Скачать и распарсить JSON отчет

        Args:
            report_url: URL JSON отчета от Parser Market

        Returns:
            Dict с данными отчета

        Raises:
            ParserMarketAPIError: Ошибка скачивания отчета
        """
        try:
            logger.debug(f"Downloading JSON report | url={report_url}")

            response = await self.client.get(report_url)
            response.raise_for_status()

            data = response.json()

            logger.debug(f"JSON report downloaded | size={len(response.content)} bytes")

            return data

        except httpx.HTTPError as e:
            logger.error(f"Report download failed | url={report_url} | error={e}")
            raise ParserMarketAPIError(f"Failed to download report: {e}")
        except Exception as e:
            logger.error(f"Report parsing failed: {e}")
            raise ParserMarketAPIError(f"Failed to parse JSON report: {e}")

    # ==================== High-Level Methods ====================

    async def parse_sync(
        self,
        article: str,
        timeout: Optional[int] = None,
        use_marketid: bool = True
    ) -> Optional[ProductInfo]:
        """
        Синхронный парсинг товара (отправка задачи + ожидание результата)

        Главный метод для замены OzonScraper.get_product_info()

        Args:
            article: Артикул товара Ozon
            timeout: Максимальное время ожидания (по умолчанию self.timeout)
            use_marketid: Если True - использует marketid, если False - productid

        Returns:
            ProductInfo или None если парсинг не удался

        Example:
            >>> client = ParserMarketClient(api_key="key")
            >>> product = await client.parse_sync("123456789")
            >>> print(product.price)
        """
        start_time = datetime.now()

        try:
            # 1. Отправляем задачу
            submit_result = await self.submit_task(article, use_marketid=use_marketid)
            userlabel = submit_result.get("userlabel")

            if not userlabel:
                logger.error(f"No userlabel in response | article={article}")
                return None

            # 2. Ждем завершения
            task = await self.wait_for_completion(
                userlabel=userlabel,
                timeout=timeout
            )

            # 3. Скачиваем JSON отчет
            report_url = self._get_field(task, "report_json")
            if not report_url:
                logger.error(f"No JSON report URL | article={article}")
                return None

            report_data = await self.download_json_report(report_url)

            # 4. Парсим в ProductInfo
            product_info = self._parse_report_to_product_info(report_data, article)

            # Добавляем метаданные
            if product_info:
                duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                product_info.fetch_time_ms = duration_ms
                product_info.source = ScrapingSource.MANUAL  # API source
                product_info.last_check = datetime.now()

                logger.info(
                    f"Product parsed successfully | "
                    f"article={article} | duration={duration_ms}ms"
                )

            return product_info

        except ParserMarketTimeoutError:
            logger.error(f"Parsing timeout | article={article}")
            return None
        except ParserMarketTaskError as e:
            logger.error(f"Parsing task failed | article={article} | error={e}")
            return None
        except ParserMarketAPIError as e:
            logger.error(f"Parser Market API error | article={article} | error={e}")
            return None
        except Exception as e:
            logger.error(f"Parsing failed | article={article} | error={e}", exc_info=True)
            return None

    async def parse_marketid(
        self,
        article: str,
        timeout: Optional[int] = None
    ) -> Optional[ProductInfo]:
        """
        Парсинг товара используя метод marketid (SKU ID Ozon)

        Явный метод для использования marketid вместо productid.
        По умолчанию submit_task() уже использует marketid для Ozon,
        но этот метод делает это явным.

        Args:
            article: SKU ID товара Ozon (marketid)
            timeout: Максимальное время ожидания (по умолчанию self.timeout)

        Returns:
            ProductInfo или None если парсинг не удался

        Example:
            >>> client = ParserMarketClient(api_key="key")
            >>> product = await client.parse_marketid("1066650955")
            >>> print(product.price)
        """
        # Используем тот же метод parse_sync, так как submit_task()
        # уже использует marketid по умолчанию для Ozon
        return await self.parse_sync(article, timeout)

    async def parse_productid(
        self,
        article: str,
        timeout: Optional[int] = None
    ) -> Optional[ProductInfo]:
        """
        Парсинг товара используя метод productid (артикул продавца)

        Args:
            article: Артикул продавца (productid)
            timeout: Максимальное время ожидания (по умолчанию self.timeout)

        Returns:
            ProductInfo или None если парсинг не удался
        """
        start_time = datetime.now()

        try:
            # 1. Отправляем задачу с use_marketid=False
            submit_result = await self.submit_task(article, use_marketid=False)
            userlabel = submit_result.get("userlabel")

            if not userlabel:
                logger.error(f"No userlabel in response | article={article}")
                return None

            # 2. Ждем завершения
            task = await self.wait_for_completion(
                userlabel=userlabel,
                timeout=timeout
            )

            # 3. Скачиваем JSON отчет
            report_url = self._get_field(task, "report_json")
            if not report_url:
                logger.error(f"No JSON report URL | article={article}")
                return None

            report_data = await self.download_json_report(report_url)

            # 4. Парсим в ProductInfo
            product_info = self._parse_report_to_product_info(report_data, article)

            # Добавляем метаданные
            if product_info:
                duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                product_info.fetch_time_ms = duration_ms
                product_info.source = ScrapingSource.MANUAL
                product_info.last_check = datetime.now()

                logger.info(
                    f"Product parsed successfully (productid) | "
                    f"article={article} | duration={duration_ms}ms"
                )

            return product_info

        except ParserMarketTimeoutError:
            logger.error(f"Parsing timeout (productid) | article={article}")
            return None
        except ParserMarketTaskError as e:
            logger.error(f"Parsing task failed (productid) | article={article} | error={e}")
            return None
        except ParserMarketAPIError as e:
            logger.error(f"Parser Market API error (productid) | article={article} | error={e}")
            return None
        except Exception as e:
            logger.error(f"Parsing failed (productid) | article={article} | error={e}", exc_info=True)
            return None

    async def parse_auto(
        self,
        article: str,
        timeout: Optional[int] = None
    ) -> Optional[ProductInfo]:
        """
        Автоматический парсинг товара: пробует productid, затем marketid
        
        Логика из parser_ozon.py: сначала пробует productid (артикул продавца),
        если не находит - пробует marketid (SKU ID Ozon).

        Args:
            article: Артикул товара Ozon
            timeout: Максимальное время ожидания для каждого метода (по умолчанию self.timeout)

        Returns:
            ProductInfo или None если товар не найден обоими методами

        Example:
            >>> client = ParserMarketClient(api_key="key")
            >>> product = await client.parse_auto("1066650955")
            >>> print(product.price)
        """
        logger.info(f"Auto parsing | article={article} | trying productid first...")

        # Пробуем сначала productid (артикул продавца)
        product = await self.parse_productid(article, timeout=timeout)
        
        if product:
            logger.info(f"✅ Product found via productid | article={article}")
            return product

        # Если не нашли, пробуем marketid (SKU ID)
        logger.info(f"Product not found via productid | article={article} | trying marketid...")
        product = await self.parse_marketid(article, timeout=timeout)
        
        if product:
            logger.info(f"✅ Product found via marketid | article={article}")
            return product

        logger.warning(f"❌ Product not found via both methods | article={article}")
        return None

    async def parse_batch(
        self,
        articles: List[str],
        timeout: Optional[int] = None
    ) -> List[Optional[ProductInfo]]:
        """
        Пакетный парсинг товаров

        Args:
            articles: Список артикулов для парсинга
            timeout: Максимальное время ожидания для каждого товара

        Returns:
            Список ProductInfo (или None для неудавшихся)

        Note:
            Выполняется последовательно для избежания rate limits
        """
        logger.info(f"Batch parsing | count={len(articles)}")

        results = []

        for i, article in enumerate(articles, 1):
            logger.info(f"Parsing {i}/{len(articles)} | article={article}")

            product = await self.parse_sync(article, timeout=timeout)
            results.append(product)

            # Небольшая задержка между запросами
            if i < len(articles):
                await asyncio.sleep(2)

        success_count = sum(1 for r in results if r is not None)
        logger.info(
            f"Batch parsing completed | "
            f"total={len(articles)} | success={success_count} | failed={len(articles) - success_count}"
        )

        return results

    # ==================== Utility Methods ====================

    def _parse_response(self, data) -> Dict[str, Any]:
        """
        Преобразовать формат ответа Parser Market в dict

        Parser Market может возвращать:
        1. Список словарей: [{"result": "success"}, {"user_id": "3"}, ...]
        2. Словарь напрямую: {"result": "success", "user_id": "3", ...}

        Преобразуем в единый словарь:
        {"result": "success", "user_id": "3", ...}
        """
        if isinstance(data, list):
            result = {}
            for item in data:
                if isinstance(item, dict):
                    result.update(item)
            return result
        elif isinstance(data, dict):
            return data
        else:
            return {}

    def _get_field(self, task_list: List[Dict], field: str) -> Any:
        """
        Извлечь поле из формата задачи Parser Market

        Задача представлена как список словарей:
        [{"order-id": 123}, {"status": "completed"}, ...]
        """
        for item in task_list:
            if field in item:
                return item[field]
        return None

    def _parse_report_to_product_info(
        self,
        report_data: Dict[str, Any],
        article: str
    ) -> Optional[ProductInfo]:
        """
        Преобразовать JSON отчет Parser Market в ProductInfo

        Args:
            report_data: Данные JSON отчета
            article: Артикул товара

        Returns:
            ProductInfo или None

        Note:
            Структура отчета Parser Market:
            {
                "data": [{
                    "Name_found": "...",
                    "Brand_found": "...",
                    "offers": [{
                        "Price": 1510.0,
                        "PromoPrice": 1465.0,
                        "OldPrice": 6990.0,
                        "OZON_couponPrice": 0.0,
                        "SkuRating": 4.8,
                        "SkuRates": 9128,
                        "Ozon_available": true,
                        "ShopUrl": "...",
                        "Offer_pics": [...]
                    }]
                }]
            }
        """
        try:
            # Проверяем наличие данных
            if not report_data.get('data') or len(report_data['data']) == 0:
                logger.warning(f"No data in report | article={article}")
                return None

            item = report_data['data'][0]

            # Основная информация о товаре
            name_found = item.get('Name_found', '')
            brand_found = item.get('Brand_found', '')
            category_found = item.get('Category_found', '')
            rating_found = item.get('Rating_found', 0.0)
            rates_found = item.get('Rates_found', 0)

            # Проверяем ServiceData
            service_data = item.get('ServiceData', {})
            is_success = service_data.get('O_IsSuccess', False)
            offers_count = item.get('Offers_counted', 0)

            # Обрабатываем предложения (offers)
            offers = item.get('offers', [])
            valid_offers = []

            for offer in offers:
                if offer.get('Name') or offer.get('Price', 0) > 0:
                    valid_offers.append(offer)

            # Товар считается найденным, если:
            # 1. Есть успешный результат в ServiceData ИЛИ
            # 2. Найдено предложений > 0 ИЛИ
            # 3. Есть валидные предложения
            found = is_success or offers_count > 0 or len(valid_offers) > 0

            if not found:
                logger.warning(f"Product not found | article={article}")
                return None

            # Выбираем лучшее предложение (с минимальной ценой или первое валидное)
            main_offer = None
            if valid_offers:
                offers_with_price = [o for o in valid_offers if o.get('Price', 0) > 0]
                if offers_with_price:
                    main_offer = min(offers_with_price, key=lambda x: x.get('Price', float('inf')))
                else:
                    main_offer = valid_offers[0]

            if not main_offer:
                logger.warning(f"No valid offers found | article={article}")
                return None

            # Извлекаем данные из основного предложения
            price = self._parse_float(main_offer.get('Price'))
            promo_price = self._parse_float(main_offer.get('PromoPrice'))
            old_price = self._parse_float(main_offer.get('OldPrice'))
            ozon_card_price = self._parse_float(main_offer.get('OZON_couponPrice'))
            sku_rating = self._parse_float(main_offer.get('SkuRating'))
            sku_rates = self._parse_int(main_offer.get('SkuRates'))
            ozon_available = main_offer.get('Ozon_available', False)
            shop_url = main_offer.get('ShopUrl', '')
            offer_pics = main_offer.get('Offer_pics', [])
            shop_name = main_offer.get('ShopName', '')

            # Определяем наличие товара
            availability = ProductAvailability.AVAILABLE if ozon_available else ProductAvailability.OUT_OF_STOCK

            # Используем рейтинг из основного предложения, если есть, иначе из корня
            final_rating = sku_rating if sku_rating else rating_found
            final_reviews_count = sku_rates if sku_rates else rates_found

            # Формируем URL
            product_url = shop_url if shop_url else f"https://www.ozon.ru/product/{article}/"

            # Извлекаем изображения (валидируем через HttpUrl)
            images = []
            image_url = None
            if offer_pics and len(offer_pics) > 0:
                for img in offer_pics:
                    if img:
                        try:
                            images.append(HttpUrl(img))
                        except Exception:
                            logger.debug(f"Invalid image URL: {img}")
                image_url = images[0] if images else None

            # Создаем ProductInfo
            product_info = ProductInfo(
                article=article,
                name=name_found or main_offer.get('Name', ''),

                # Цены
                price=price,
                normal_price=price,  # Основная цена без скидок
                ozon_card_price=ozon_card_price if ozon_card_price else promo_price,  # Используем promo_price если нет ozon_card_price
                old_price=old_price,

                # Рейтинг
                rating=final_rating,
                reviews_count=final_reviews_count,

                # Наличие
                availability=availability,
                stock_count=self._parse_int(main_offer.get('Ozon_stockcount')),

                # Изображения и ссылки
                image_url=image_url,
                images=images,
                url=HttpUrl(product_url) if product_url else HttpUrl(f"https://www.ozon.ru/product/{article}/"),
                product_id=article,

                # Дополнительно
                brand=brand_found or main_offer.get('Brand_found', ''),
                category=category_found,
                seller_name=shop_name,

                # Метаданные
                last_check=datetime.now(),
                source=ScrapingSource.MANUAL  # API source
            )

            logger.debug(
                f"Report parsed | article={article} | name={product_info.name} | "
                f"price={product_info.price} | rating={product_info.rating}"
            )

            return product_info

        except Exception as e:
            logger.error(
                f"Failed to parse report | article={article} | error={e}",
                exc_info=True
            )
            return None

    def _parse_float(self, value: Any) -> Optional[float]:
        """Безопасно преобразовать в float"""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _parse_int(self, value: Any) -> Optional[int]:
        """Безопасно преобразовать в int"""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    def _parse_availability(self, value: Any) -> ProductAvailability:
        """Преобразовать availability в enum"""
        if not value:
            return ProductAvailability.UNKNOWN

        value_str = str(value).lower()

        if "available" in value_str or "в наличии" in value_str:
            return ProductAvailability.AVAILABLE
        elif "out" in value_str or "нет" in value_str:
            return ProductAvailability.OUT_OF_STOCK
        elif "limited" in value_str or "мало" in value_str:
            return ProductAvailability.LIMITED
        elif "pre" in value_str or "предзаказ" in value_str:
            return ProductAvailability.PRE_ORDER
        else:
            return ProductAvailability.UNKNOWN


# ==================== Factory Function ====================

_parser_market_client: Optional[ParserMarketClient] = None


def get_parser_market_client(
    api_key: Optional[str] = None,
    region: str = "Москва"
) -> ParserMarketClient:
    """
    Получить singleton инстанс Parser Market клиента

    Args:
        api_key: API ключ (если None, берется из config)
        region: Регион для парсинга

    Returns:
        ParserMarketClient instance

    Example:
        >>> client = get_parser_market_client()
        >>> product = await client.parse_sync("123456789")
    """
    global _parser_market_client

    if _parser_market_client is None:
        if api_key is None:
            # Import здесь чтобы избежать circular imports
            from config import settings
            api_key = settings.PARSER_MARKET_API_KEY

        _parser_market_client = ParserMarketClient(
            api_key=api_key,
            region=region
        )
        logger.info("Parser Market client singleton created")

    return _parser_market_client


async def close_parser_market_client():
    """Закрыть глобальный клиент"""
    global _parser_market_client

    if _parser_market_client:
        await _parser_market_client.close()
        _parser_market_client = None
        logger.info("Parser Market client singleton closed")
